from datetime import datetime, timezone, timedelta
import requests
from wallbox import Wallbox

from credentials_for_test_do_not_commit import PASSWORD, USER_NAME

if __name__ == "__main__":

    w = Wallbox(username=USER_NAME, password=PASSWORD, jwtTokenDrift=30)
    w.authenticate()
    chargers = w.getChargersList()
    d = w.getChargerStatus(chargers[0])

    energy_price = 0.23
    w.setEnergyCost(chargers[0], energy_price)
    d2 = w.getChargerStatus(chargers[0])
    if d2['config_data']['energy_price'] == energy_price:
        print("ok")

    charge_sessions = w.getSessionList(chargers[0], startDate=datetime.now() - timedelta(days=3), endDate=datetime.now())

    max_charging_current = 32
    w.setMaxChargingCurrent(chargers[0], max_charging_current)

    a = w.getChargerSchedules(chargers[0])

    d3 = w.getChargerStatus(chargers[0])
    if d3['config_data']['max_charging_current'] == max_charging_current:
        print("ok")

    #test timeout
    w._requestTimeout = 0.00001
    try:
        w.getChargerStatus(chargers[0])
    except requests.exceptions.Timeout as err:
        print("ok")



