
"""

Wallbox class

"""

from requests.auth import HTTPBasicAuth
import requests 
import json

class Wallbox:
    def __init__ (self, username, password):
      self.username = username
      self.password = password
      self.baseUrl = 'https://api.wall-box.com/'
      self.jwtToken = ''
      self.headers = {
        "Accept": "application/json",
        "Content-Type": "application/json;charset=UTF-8",
        }
    
    def authenticate(self):
        try:
            response = requests.get(f"{self.baseUrl}auth/token/user", auth=HTTPBasicAuth(self.username, self.password))
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise(err)
        self.jwtToken = json.loads(response.text)["jwt"]
        self.headers["Authorization"] = f"Bearer {self.jwtToken}"
    
    def getChargersList(self):
        chargerIds = []
        try:
            response = requests.get(f"{self.baseUrl}v3/chargers/groups", headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise(err) 
        for group in json.loads(response.text)["result"]["groups"]:
            for charger in group["chargers"]:
                chargerIds.append(charger["id"])
        return chargerIds
    
    def getChargerStatus(self,chargerId):
        try:
            response = requests.get(f"{self.baseUrl}chargers/status/{chargerId}", headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise(err) 
        return json.loads(response.text)
    
    def unlockCharger(self,chargerId):
        try:
            response = requests.put(f"{self.baseUrl}v2/charger/{chargerId}", headers=self.headers, data='{"locked":0}')
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise(err)
        return json.loads(response.text)

    def lockCharger(self,chargerId):
        try:
            response = requests.put(f"{self.baseUrl}v2/charger/{chargerId}", headers=self.headers, data='{"locked":1}')
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise(err)
        return json.loads(response.text)