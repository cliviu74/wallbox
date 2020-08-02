from requests.auth import HTTPBasicAuth
import requests 
import json

"""

Wallbox class

"""

wallboxApiBaseUrl = 'https://api.wall-box.com/'

class Wallbox:
    def __init__ (self, username, password):
      self.username = username
      self.password = password

    def authenticate(self):
        try:
            response = requests.get(wallboxApiBaseUrl + 'auth/token/user', auth=HTTPBasicAuth(self.username, self.password))
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise(err)
        self.jwtToken = json.loads(response.text)["jwt"]
        self.headers = {'Authorization': "Bearer " + self.jwtToken}
    
    def getChargersList(self):
        chargerIds = []
        try:
            response = requests.get(wallboxApiBaseUrl + 'v3/chargers/groups', headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise(err) 
        for group in json.loads(response.text)["result"]["groups"]:
            for charger in group["chargers"]:
                chargerIds.append(charger["id"])
        return chargerIds
    
    def getChargerData(self,chargerId):
        try:
            response = requests.get(wallboxApiBaseUrl + 'v2/charger/' + str(chargerId), headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise(err) 
        return json.loads(response.text)["data"]["chargerData"]