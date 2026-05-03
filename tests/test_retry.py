"""
Tests for the 429 retry behavior introduced on the Wallbox session.

Three layers of coverage:

1. TestRetryConfiguration — verifies the Retry adapter is mounted on the
   session with the configuration we expect.
2. TestExistingErrorContract — verifies non-retryable errors continue to
   raise requests.HTTPError exactly as before, using requests-mock.
3. TestRetryBehaviour — end-to-end behavioural tests against a real local
   HTTP server (pytest-httpserver). These exercise the full HTTP path
   including the urllib3 Retry adapter, which requests-mock bypasses.
"""

import time

import pytest
import requests
import requests_mock

from wallbox import Wallbox


def _retry(session):
    """Pull the configured Retry object off a session's https adapter."""
    return session.get_adapter("https://example.com/").max_retries


class TestRetryConfiguration:
    def test_retry_adapter_is_mounted_for_https(self):
        w = Wallbox("user", "pass")
        adapter = w._session.get_adapter("https://example.com/")
        assert adapter is not None
        assert hasattr(adapter, "max_retries")

    def test_status_forcelist_is_429_only(self):
        # 5xx is intentionally excluded: some POST endpoints in the lib are
        # not idempotent (restartCharger, updateFirmware) and silently
        # retrying them on a transient server error could cause the action
        # to fire twice. 429 is always safe to retry — by definition the
        # server has not processed the request.
        retry = _retry(Wallbox("user", "pass")._session)
        assert retry.status_forcelist == (429,)

    def test_status_forcelist_excludes_auth_and_other_4xx(self):
        # Auth failures must not be transparently retried, otherwise bad
        # credentials would silently burn through the retry budget.
        retry = _retry(Wallbox("user", "pass")._session)
        for code in (400, 401, 403, 404, 500, 502, 503, 504):
            assert code not in retry.status_forcelist

    def test_allowed_methods_cover_all_verbs_in_use(self):
        retry = _retry(Wallbox("user", "pass")._session)
        assert {"GET", "POST", "PUT"} <= set(retry.allowed_methods)

    def test_respects_retry_after_header(self):
        retry = _retry(Wallbox("user", "pass")._session)
        assert retry.respect_retry_after_header is True

    def test_does_not_raise_on_status(self):
        # raise_on_status=False keeps the existing HTTPError contract: callers
        # see requests.HTTPError, not urllib3.MaxRetryError / RetryError.
        retry = _retry(Wallbox("user", "pass")._session)
        assert retry.raise_on_status is False

    def test_default_retry_budget(self):
        retry = _retry(Wallbox("user", "pass")._session)
        assert retry.total == 3
        assert retry.backoff_factor == 1.0

    def test_connect_and_read_retries_disabled(self):
        # Network errors (DNS, connection refused, read timeout) must not be
        # retried by this PR. The retry budget is for 429 only — silently
        # retrying network failures is a separate decision.
        retry = _retry(Wallbox("user", "pass")._session)
        assert retry.connect == 0
        assert retry.read == 0

    def test_retry_budget_is_tunable(self):
        retry = _retry(Wallbox("user", "pass", maxRetries=5, backoffFactor=2.5)._session)
        assert retry.total == 5
        assert retry.backoff_factor == 2.5


class TestExistingErrorContract:
    """
    Sanity checks that introducing the retry adapter has not altered the
    exception type seen by callers for non-retryable failures.

    Note: requests_mock.Mocker(session=...) replaces the session's adapters
    with its own, so the Retry adapter is bypassed for the duration of these
    tests. That is intentional here — these tests cover the post-retry path
    (i.e. what the caller sees once retries are exhausted or never happened).
    Retry-loop behaviour itself is provided by urllib3 and covered by its
    own test suite; this PR verifies our configuration plugs into it
    correctly via the TestRetryConfiguration class above.
    """

    def _authed_client(self):
        w = Wallbox("user", "pass")
        # Skip authenticate() — these tests target post-auth methods.
        w.headers["Authorization"] = "Bearer fake"
        return w

    def test_404_still_raises_http_error(self):
        w = self._authed_client()
        with requests_mock.Mocker(session=w._session) as m:
            m.get(f"{w.baseUrl}chargers/status/123", status_code=404)
            with pytest.raises(requests.exceptions.HTTPError):
                w.getChargerStatus(123)

    def test_400_still_raises_http_error(self):
        w = self._authed_client()
        with requests_mock.Mocker(session=w._session) as m:
            m.put(f"{w.baseUrl}v2/charger/123", status_code=400)
            with pytest.raises(requests.exceptions.HTTPError):
                w.lockCharger(123)

    def test_success_returns_decoded_payload(self):
        w = self._authed_client()
        with requests_mock.Mocker(session=w._session) as m:
            m.get(
                f"{w.baseUrl}chargers/status/123",
                json={"status_id": 194, "name": "test"},
            )
            result = w.getChargerStatus(123)
            assert result["status_id"] == 194


class TestRetryBehaviour:
    """
    End-to-end tests using pytest-httpserver. Unlike requests-mock, this
    spins up a real localhost HTTP server, so requests travel through the
    full urllib3 Retry adapter and the retry behaviour is actually
    exercised — not just the configuration we declared.

    These tests use a very small backoffFactor so that retry sleeps don't
    slow the suite down.
    """

    def _wallbox(self, httpserver, **kwargs):
        kwargs.setdefault("backoffFactor", 0.001)
        w = Wallbox("user", "pass", **kwargs)
        url = httpserver.url_for("/")
        if not url.endswith("/"):
            url += "/"
        w.baseUrl = url
        w.authUrl = url
        # The production session mounts the retry adapter on https:// only,
        # because the Wallbox API is https. pytest-httpserver runs plaintext
        # localhost, so for these tests we mirror the retry adapter onto
        # http:// — keeping production https-only while still exercising the
        # full Retry path in the test suite.
        w._session.mount("http://", w._session.get_adapter("https://example.com/"))
        # Skip authenticate() — these tests target post-auth methods.
        w.headers["Authorization"] = "Bearer fake"
        return w

    def test_429_then_200_triggers_one_retry_and_succeeds(self, httpserver):
        # First request gets a 429, second gets a 200. The lib should retry
        # transparently and the caller should see the decoded 200 payload.
        httpserver.expect_oneshot_request(
            "/v3/chargers/groups"
        ).respond_with_data("rate limited", status=429)
        httpserver.expect_oneshot_request(
            "/v3/chargers/groups"
        ).respond_with_json(
            {"result": {"groups": [{"chargers": [{"id": 42}]}]}}
        )

        w = self._wallbox(httpserver)
        result = w.getChargersList()

        assert result == [42]
        assert len(httpserver.log) == 2  # initial + 1 retry

    def test_429_forever_exhausts_retries_and_raises_http_error(self, httpserver):
        # Server returns 429 to every request. After maxRetries=2 the lib
        # should raise the HTTPError that callers expect (not RetryError /
        # MaxRetryError). Total requests = 1 initial + 2 retries = 3.
        httpserver.expect_request("/v3/chargers/groups").respond_with_data(
            "rate limited", status=429
        )

        w = self._wallbox(httpserver, maxRetries=2)

        with pytest.raises(requests.exceptions.HTTPError) as excinfo:
            w.getChargersList()

        assert excinfo.value.response.status_code == 429
        assert len(httpserver.log) == 3

    def test_retry_after_header_is_honored(self, httpserver):
        # Server replies 429 with Retry-After: 1, then 200 on retry. With
        # respect_retry_after_header=True the lib should sleep ~1s between
        # attempts. With it disabled, the test would complete in well under
        # 100ms (backoffFactor=0.001), so a 0.9s lower bound is a wide,
        # non-flaky boundary.
        httpserver.expect_oneshot_request(
            "/v3/chargers/groups"
        ).respond_with_data(
            "rate limited", status=429, headers={"Retry-After": "1"}
        )
        httpserver.expect_oneshot_request(
            "/v3/chargers/groups"
        ).respond_with_json({"result": {"groups": []}})

        w = self._wallbox(httpserver)
        start = time.monotonic()
        w.getChargersList()
        elapsed = time.monotonic() - start

        assert elapsed >= 0.9, f"expected ~1s wait from Retry-After, got {elapsed:.3f}s"
        assert len(httpserver.log) == 2

    def test_401_is_not_retried(self, httpserver):
        # Auth failures must surface immediately. Otherwise bad credentials
        # would silently consume the entire retry budget on every call.
        httpserver.expect_request("/v3/chargers/groups").respond_with_data(
            "unauthorized", status=401
        )

        w = self._wallbox(httpserver, maxRetries=3)

        with pytest.raises(requests.exceptions.HTTPError) as excinfo:
            w.getChargersList()

        assert excinfo.value.response.status_code == 401
        # Exactly one request — no retry.
        assert len(httpserver.log) == 1

    def test_connection_error_is_not_retried(self):
        # Network failures (DNS, connection refused, timeout) must surface
        # immediately, not be silently retried — that scope belongs to a
        # separate decision and a separate PR. The retry budget is for 429
        # only.
        #
        # We use a deliberately slow backoffFactor here so that *if* connect
        # retries fired they would take noticeably long (3 sleeps of
        # 0.1 + 0.2 + 0.4 = 0.7s). With connect retries disabled the call
        # should fail in well under that window.
        import socket
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        closed_port = sock.getsockname()[1]
        sock.close()

        w = Wallbox("user", "pass", maxRetries=3, backoffFactor=0.1)
        # Mirror the retry adapter onto http:// so this test actually
        # exercises connect=0 through our adapter (production session is
        # https-only — see _wallbox fixture for the same reasoning).
        w._session.mount("http://", w._session.get_adapter("https://example.com/"))
        w.baseUrl = f"http://127.0.0.1:{closed_port}/"
        w.headers["Authorization"] = "Bearer fake"

        start = time.monotonic()
        with pytest.raises(requests.exceptions.ConnectionError):
            w.getChargersList()
        elapsed = time.monotonic() - start

        assert elapsed < 0.3, (
            f"connection error should fail fast, took {elapsed:.3f}s — "
            "indicates network errors are being retried"
        )
