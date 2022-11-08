"""

Wallbox class

"""

from datetime import datetime
from time import timezone
from requests.auth import HTTPBasicAuth
import requests
import json


class Wallbox:
    def __init__(self, username, password, requestGetTimeout = None, jwtTokenDrift = 0):
        self.username = username
        self.password = password
        self._requestGetTimeout = requestGetTimeout
        self.baseUrl = "https://api.wall-box.com/"
        self.authUrl = "https://user-api.wall-box.com/"
        self.jwtTokenDrift = jwtTokenDrift
        self.jwtToken = ""
        self.jwtTokenTtl = 0
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8",
        }

    @property
    def requestGetTimeout(self):
        return self._requestGetTimeout

    def authenticate(self):
        if self.jwtToken != "" and round(
            (self.jwtTokenTtl / 1000) - jwtTokenDrift, 0
        ) > datetime.timestamp(datetime.now()):
            return

        try:
            response = requests.get(
                f"{self.authUrl}users/signin",
                auth=HTTPBasicAuth(self.username, self.password),
                headers={'Partner': 'wallbox'},
                timeout=self._requestGetTimeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        self.jwtToken = json.loads(response.text)["data"]["attributes"]["token"]
        self.jwtTokenTtl = json.loads(response.text)["data"]["attributes"]["ttl"]
        self.headers["Authorization"] = f"Bearer {self.jwtToken}"

    def getChargersList(self):
        chargerIds = []
        try:
            response = requests.get(
                f"{self.baseUrl}v3/chargers/groups", headers=self.headers,
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
                f"{self.baseUrl}chargers/status/{chargerId}", headers=self.headers,
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
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    def getSessionList(self, chargerId, startDate, endDate):
        try:
            payload = {'charger': chargerId, 'start_date': startDate.timestamp(), 'end_date': endDate.timestamp() }

            response = requests.get(
                f"{self.baseUrl}v4/sessions/stats", params=payload, headers=self.headers,
                timeout=self._requestGetTimeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)
