"""

Wallbox class

"""

from datetime import datetime
from requests.auth import HTTPBasicAuth
import requests
import json

from wallbox.bearerauth import BearerAuth


class Wallbox:
    def __init__(self, username, password, requestGetTimeout = None, jwtTokenDrift = 0):
        self.username = username
        self.password = password
        self._requestGetTimeout = requestGetTimeout
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

    @property
    def requestGetTimeout(self):
        return self._requestGetTimeout

    def authenticate(self):
        auth_path = "users/signin"
        auth = HTTPBasicAuth(self.username, self.password)
        # if already has token:
        if self.jwtToken != "":
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

        try:
            response = requests.get(
                f"{self.authUrl}{auth_path}",
                auth=auth,
                headers={'Partner': 'wallbox'},
                timeout=self._requestGetTimeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)

        self.jwtToken = json.loads(response.text)["data"]["attributes"]["token"]
        self.jwtRefreshToken = json.loads(response.text)["data"]["attributes"]["refresh_token"]
        self.jwtTokenTtl = json.loads(response.text)["data"]["attributes"]["ttl"]
        self.jwtRefreshTokenTtl = json.loads(response.text)["data"]["attributes"]["refresh_token_ttl"]
        self.headers["Authorization"] = f"Bearer {self.jwtToken}"

    def getChargersList(self):
        chargerIds = []
        try:
            response = requests.get(
                f"{self.baseUrl}v3/chargers/groups",
                headers=self.headers,
                timeout=self._requestGetTimeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        for group in json.loads(response.text)["result"]["groups"]:
            for charger in group["chargers"]:
                chargerIds.append(charger["id"])
        return chargerIds

    def getChargerStatus(self, chargerId):
        try:
            response = requests.get(
                f"{self.baseUrl}chargers/status/{chargerId}", 
                headers=self.headers,
                timeout=self._requestGetTimeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    def unlockCharger(self, chargerId):
        try:
            response = requests.put(
                f"{self.baseUrl}v2/charger/{chargerId}",
                headers=self.headers,
                data='{"locked":0}',
                timeout=self._requestGetTimeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    def lockCharger(self, chargerId):
        try:
            response = requests.put(
                f"{self.baseUrl}v2/charger/{chargerId}",
                headers=self.headers,
                data='{"locked":1}',
                timeout=self._requestGetTimeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    def setMaxChargingCurrent(self, chargerId, newMaxChargingCurrentValue):
        try:
            response = requests.put(
                f"{self.baseUrl}v2/charger/{chargerId}",
                headers=self.headers,
                data=f'{{ "maxChargingCurrent":{newMaxChargingCurrentValue}}}',
                timeout=self._requestGetTimeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    def pauseChargingSession(self, chargerId):
        try:
            response = requests.post(
                f"{self.baseUrl}v3/chargers/{chargerId}/remote-action",
                headers=self.headers,
                data='{"action":2}',
                timeout=self._requestGetTimeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    def resumeChargingSession(self, chargerId):
        try:
            response = requests.post(
                f"{self.baseUrl}v3/chargers/{chargerId}/remote-action",
                headers=self.headers,
                data='{"action":1}',
                timeout=self._requestGetTimeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    def resumeSchedule(self, chargerId):
        try:
            response = requests.post(
                f"{self.baseUrl}v3/chargers/{chargerId}/remote-action",
                headers=self.headers,
                data='{"action":9}',
                timeout=self._requestGetTimeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    def restartCharger(self, chargerId):
        try:
            response = requests.post(
                f"{self.baseUrl}v3/chargers/{chargerId}/remote-action",
                headers=self.headers,
                data='{"action":3}',
                timeout=self._requestGetTimeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    def updateFirmware(self, chargerId):
        try:
            response = requests.post(
                f"{self.baseUrl}v3/chargers/{chargerId}/remote-action",
                headers=self.headers,
                data='{"action":5}',
                timeout=self._requestGetTimeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    def getSessionList(self, chargerId, startDate, endDate):
        try:
            payload = {'charger': chargerId, 'start_date': startDate.timestamp(), 'end_date': endDate.timestamp() }

            response = requests.get(
                f"{self.baseUrl}v4/sessions/stats",
                params=payload,
                headers=self.headers,
                timeout=self._requestGetTimeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    def setEnergyCost(self, chargerId, energyCost):
        try:
            response = requests.post(
                f"{self.baseUrl}chargers/config/{chargerId}",
                headers=self.headers,
                json={'energyCost': energyCost},
                timeout=self._requestGetTimeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)


    def setIcpMaxCurrent(self, chargerId, newIcpMaxCurrentValue):
        try:
            response = requests.post(
                f"{self.baseUrl}chargers/config/{chargerId}",
                headers=self.headers,
                json={'icp_max_current': newIcpMaxCurrentValue},
                timeout=self._requestGetTimeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)
    
    def getChargerSchedules(self, chargerId):
        try:
            response = requests.get(
                f"{self.baseUrl}chargers/{chargerId}/schedules",
                headers=self.headers,
                timeout=self._requestGetTimeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    def setChargerSchedules(self, chargerId, newSchedules):
        try:
            # Enforce chargerId
            for schedule in newSchedules.get('schedules', []):
                schedule['chargerId'] = chargerId

            response = requests.post(
                f"{self.baseUrl}chargers/{chargerId}/schedules",
                headers=self.headers,
                json=newSchedules,
                timeout=self._requestGetTimeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    def enableEcoSmart(self, chargerId, mode: int = 0):
        try:
            response = requests.put(
                f"{self.baseUrl}v4/chargers/{chargerId}/eco-smart",
                headers=self.headers,
                json={
                    "data": {
                        "attributes": {"enabled": 1, "mode": mode},
                        "type": "eco_smart",
                    },
                },
                timeout=self._requestGetTimeout,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return response.status_code

    def disableEcoSmart(self, chargerId):
        try:
            response = requests.put(
                f"{self.baseUrl}v4/chargers/{chargerId}/eco-smart",
                headers=self.headers,
                json={
                    "data": {
                        "attributes": {"enabled": 0, "mode": 0},
                        "type": "eco_smart",
                    }
                },
                timeout=self._requestGetTimeout,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return response.status_code
