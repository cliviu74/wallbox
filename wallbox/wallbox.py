"""

Wallbox class

"""

from datetime import datetime
from time import timezone
from requests.auth import HTTPBasicAuth
import requests
import json

from wallbox.bearerauth import BearerAuth

DEFAULT_TIMEOUT_S = 5
RETRY_ON_TIMEOUT_NUMBER = 3

class Wallbox:
    def __init__(self, username, password, requestGetTimeout = DEFAULT_TIMEOUT_S, jwtTokenDrift = 0):
        self.username = username
        self.password = password
        self._requestTimeout = requestGetTimeout
        self.baseUrl = "https://api.wall-box.com/"
        self.authUrl = "https://user-api.wall-box.com/"
        self.jwtTokenDrift = jwtTokenDrift
        self.jwtToken = ""
        self.jwtRefreshToken = ""
        self.jwtTokenTtl = 0
        self.jwtRefreshTokenTtl = 0
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8",
            "User-Agent": "HomeAssistantWallboxPlugin/1.0.0",
        }
        self._requestNumRetry = RETRY_ON_TIMEOUT_NUMBER

    @property
    def requestGetTimeout(self):
        return self._requestTimeout


    def _request_method_helper(self, method, url, overcharge_headers=None, **kwargs):

        headers = overcharge_headers
        if overcharge_headers is None:
            headers = self.headers

        for i in range(self._requestNumRetry):
            try:
                response = method(
                    url,
                    headers=headers,
                    timeout=self._requestTimeout,
                    **kwargs
                )
                response.raise_for_status()
                return response

            except requests.exceptions.Timeout as err:
                # Ok we can continue trying it is a timeout
                if i >= self._requestNumRetry - 1:
                    raise (err)
            except requests.exceptions.HTTPError as err:
                #has been raised for HTTP errors only shoud trace it
                raise (err)
            except requests.exceptions.RequestException as err:
                #Any other exception from requests (Connection errors, Too many redirects, etc
                raise (err)


    def _get_helper(self, url, **kwargs):
        return self._request_method_helper(method=requests.get, url=url, **kwargs)

    def _put_helper(self, url, **kwargs):
        return self._request_method_helper(method=requests.put, url=url, **kwargs)

    def _post_helper(self, url, **kwargs):
        return self._request_method_helper(method=requests.post, url=url, **kwargs)

    def authenticate(self):
        self._authenticate(from_refresh=False)

    def _authenticate(self, from_refresh=False):
        auth_path = "users/signin"
        auth = HTTPBasicAuth(self.username, self.password)

        ask_for_refresh = False
        # if already has token:
        if from_refresh is False and self.jwtToken != "":
            # check if token is still valid
            if round((self.jwtTokenTtl / 1000) - self.jwtTokenDrift, 0) > datetime.timestamp(datetime.now()):
                return
            # if not, check if refresh token is still valid
            elif (self.jwtRefreshToken != ""
                  and round((self.jwtRefreshTokenTtl / 1000) - self.jwtTokenDrift, 0)
                  > datetime.timestamp(datetime.now())):
                # try to refresh token
                auth_path = "users/refresh-token"
                auth = BearerAuth(self.jwtRefreshToken)
                ask_for_refresh = True

        try:
            response = self._get_helper(url=f"{self.authUrl}{auth_path}", auth=auth, overcharge_headers={'Partner': 'wallbox'})
        except requests.exceptions.HTTPError as err:
            if from_refresh or ask_for_refresh is False:
                raise(err)
            #we need to redo a full "authentication" as the refresh token is probably no more valid or have an issue
            #got this after running the integration for a while
            self._authenticate(from_refresh=True)
            return

        self.jwtToken = json.loads(response.text)["data"]["attributes"]["token"]
        self.jwtRefreshToken = json.loads(response.text)["data"]["attributes"]["refresh_token"]
        self.jwtTokenTtl = json.loads(response.text)["data"]["attributes"]["ttl"]
        self.jwtRefreshTokenTtl = json.loads(response.text)["data"]["attributes"]["refresh_token_ttl"]
        self.headers["Authorization"] = f"Bearer {self.jwtToken}"

    def getChargersList(self):
        chargerIds = []
        response = self._get_helper(f"{self.baseUrl}v3/chargers/groups")
        for group in json.loads(response.text)["result"]["groups"]:
            for charger in group["chargers"]:
                chargerIds.append(charger["id"])
        return chargerIds

    def getChargerStatus(self, chargerId):
        response = self._get_helper(f"{self.baseUrl}chargers/status/{chargerId}")
        return json.loads(response.text)

    def unlockCharger(self, chargerId):
        response = self._put_helper(url=f"{self.baseUrl}v2/charger/{chargerId}", data='{"locked":0}')
        return json.loads(response.text)

    def lockCharger(self, chargerId):
        response = self._put_helper(url=f"{self.baseUrl}v2/charger/{chargerId}", data='{"locked":1}')
        return json.loads(response.text)

    def setMaxChargingCurrent(self, chargerId, newMaxChargingCurrentValue):
        response = self._put_helper(url=f"{self.baseUrl}v2/charger/{chargerId}", data=f'{{ "maxChargingCurrent":{newMaxChargingCurrentValue}}}')
        return json.loads(response.text)

    def pauseChargingSession(self, chargerId):
        response = self._post_helper(url=f"{self.baseUrl}v3/chargers/{chargerId}/remote-action", data='{"action":2}')
        return json.loads(response.text)

    def resumeChargingSession(self, chargerId):
        response = self._post_helper(url=f"{self.baseUrl}v3/chargers/{chargerId}/remote-action", data='{"action":1}')
        return json.loads(response.text)

    def restartCharger(self, chargerId):
        response = self._post_helper(url=f"{self.baseUrl}v3/chargers/{chargerId}/remote-action", data='{"action":3}')
        return json.loads(response.text)

    def getSessionList(self, chargerId, startDate, endDate):
        payload = {'charger': chargerId, 'start_date': startDate.timestamp(), 'end_date': endDate.timestamp()}
        response = self._get_helper(url=f"{self.baseUrl}v4/sessions/stats", params=payload)
        return json.loads(response.text)

    def setEnergyCost(self, chargerId, energyCost):
        response = self._post_helper(url=f"{self.baseUrl}chargers/config/{chargerId}", json={'energyCost': energyCost})
        return json.loads(response.text)