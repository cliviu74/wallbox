from datetime import datetime, timezone, timedelta
import requests
from wallbox import Wallbox
#from wallbox import SmartEcoModes
import requests
import json
import time

from credentials_for_test_do_not_commit import PASSWORD, USER_NAME

if __name__ == "__main__":

    w = Wallbox(username=USER_NAME, password=PASSWORD, jwtTokenDrift=30)
    w.authenticate()
    chargers = w.getChargersList()
    d = w.getChargerStatus(chargers[0])

    #w.setEcoMode(chargers[0], enable=True, ecoMode=SmartEcoModes.GREEN)

    max_charging_current = 31
    w.setMaxChargingCurrent(chargers[0], max_charging_current)

    d3 = w.getChargerStatus(chargers[0])
    if d3['config_data']['max_charging_current'] == max_charging_current:
        print("ok 1")
    else:
        print("fail 1")

   # max_charging_current = 30
   # w.setMaxChargingCurrentNew(chargers[0], max_charging_current)

   # d3 = w.getChargerStatus(chargers[0])
   # if d3['config_data']['max_charging_current'] == max_charging_current:
   #     print("ok")

    for i in range(4):
        st = time.time()
        max_charging_current = 32 - i
        w.setMaxChargingCurrent(chargers[0], max_charging_current)

        et = time.time()

        elapsed_time = et - st
        print('Execution time:', elapsed_time, 'seconds')


    max_charging_current = 32
    w.setMaxChargingCurrent(chargers[0], max_charging_current)

    if True:

        # action 9: resume ecosmart the session as to be stopped first and in the correct state after an action: 1
        # it seems that if the status was 181 (car not asking for charge): it does nothing and we can't launch an action 2
        # status has to be 182 "paused" to be able to use action 9
        #response = w._post_helper(url=f"{w.baseUrl}v3/chargers/{chargers[0]}/remote-action", data='{"action":9}')
        #d = json.loads(response.text)

        #w.resumeChargingSession(chargers[0])

        #d = w.getChargerStatus(chargers[0])


        #w.pauseChargingSession(chargers[0])

        d = w.getChargerStatus(chargers[0])



        energy_price = 0.24
        w.setEnergyCost(chargers[0], energy_price)
        d2 = w.getChargerStatus(chargers[0])
        if d2['config_data']['energy_price'] == energy_price:
            print("ok 2")
        else:
            print("fail 2")

        charge_sessions = w.getSessionList(chargers[0], startDate=datetime.now() - timedelta(days=3), endDate=datetime.now())

        max_charging_current = 32
        w.setMaxChargingCurrent(chargers[0], max_charging_current)

        #a = w.getChargerSchedules(chargers[0])

        d3 = w.getChargerStatus(chargers[0])
        if d3['config_data']['max_charging_current'] == max_charging_current:
            print("ok 3")
        else:
            print("fail 3")

        #test timeout
        w._requestGetTimeout = 0.00001
        try:
            w.getChargerStatus(chargers[0])
        except requests.exceptions.Timeout as err:
            print("ok 4")

        print("end")


    from enum import Enum


    class SmartEcoModes(Enum):
        ECO = 0
        GREEN = 1

    def setMaxChargingCurrentNew(self, chargerId, newMaxChargingCurrentValue):
        try:
            response = requests.post(
                f"{self.baseUrl}chargers/config/{chargerId}",
                headers=self.headers,
                data=f'{{ "max_charging_current":{newMaxChargingCurrentValue}}}',
                timeout=self._requestGetTimeout,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        return json.loads(response.text)

    def setEcoMode(self, chargerId, enable, ecoMode=SmartEcoModes.ECO):
        if enable:
            enable = 1
        else:
            enable = 0
        try:
            response = requests.put(
                f"{self.baseUrl}v4/chargers/{chargerId}/eco-smart",
                headers=self.headers,
                data=f'{{  "data": {{ "attributes": {{ "percentage": 100, "enabled": {enable}, "mode": {ecoMode.value}  }}, "type": "eco_smart" }} }}',
                timeout=self._requestGetTimeout,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise (err)
        #return json.loads(response.text)