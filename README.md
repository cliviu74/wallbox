# wallbox

Python Module interface for Wallbox EV chargers api

## Requirements

Python 3.7 or older

Python module "requests>=2.22.0"

Python module "aenum>=3.1.8"

## Installation

```python
pip install wallbox
```

## Implemented methods

### authenticate()

- authenticates to the wallbox api.

### getChargersList()

- returns a list of chargers available to the account

### getChargerStatus(chargerID)

- returns a dictionary containing the charger status data

### unlockCharger(chargerId)

- unlocks charger

### lockCharger(chargerId)

- locks charger

### setMaxChargingCurrent(chargerId, chargingCurrentValue)

- sets charger Maximum Charging Current (Amps)

### pauseChargingSession(chargerId)

- pauses a charging session

### resumeChargingSession(chargerId)

- resumes a charging session

### resumeSchedule(chargerId)

- revert charger back to default schedule after manually starting a charging session, it reverts the charger back into "Eco Smart and Scheduled" charing mode, if used.

### getSessionList(chargerId, startDate, endDate)

- provides the list of charging sessions between startDate and endDate
- startDate and endDate are provided in Python datetime format (i.e. 2021-05-04 08:41:12.765644)

### setEnergyCost(chargerId, energyCost)

- sets the energy cost for the charger per kWh

### restartCharger(chargerId)

- restarts (reboots) charger
- a full charger reboot can take a few minutes. Charger status will be slow to update (ie: READY (10s) -> DISCONNECTED (90s) -> READY)
CAUTION: use this method with care!! Check if the charger is not in the middle of a firmware upgrade as this can brick your charger. 

### updateFirmware(chargerId)

- trigger a firmware update when available.

### setIcpMaxCurrent(chargerId, newIcpMaxCurrentValue)

- sets charger Maximum ICP Current available (Amps).

Please note that the wallbox may refuse this action if not setup properly of if not supported by your model


### getChargerSchedules(chargerId)

- gets the currently configured schedules for that charger. 

Response is a JSON structure like the following:

```json
{
    'schedules': [{
        'chargerId': 42,
        'enable': 1,
        'max_current': 1,
        'max_energy': 0,
        'days': {'friday': true, 'monday': true, 'saturday': true, 'sunday': true, 'thursday': true,
                    'tuesday': true, 'wednesday': true},
        'start': '2100',
        'stop': '0500'
    }]
}
```

### setChargerSchedules(chargerId, newSchedules)

- Create or replace an existing schedule. 

`newSchedules` is a dictionary like the following:

```json
{
    'schedules': [{
        'id': 0,
        'chargerId': 42,
        'enable': 1,
        'max_current': 1,
        'max_energy': 0,
        'days': {'friday': true, 'monday': true, 'saturday': true, 'sunday': true, 'thursday': true,
                    'tuesday': true, 'wednesday': true},
        'start': '2100',
        'stop': '0500'
    }]
}
```

As schedules returned by `getChargerSchedules` are positional, the `id` field in the payload represents the position of the schedule to add/replace.

### enableEcoSmart(chargerId, mode)

- Enable Eco Smart (called Solar Charging in the app)

Valid modes:
- 0: Eco smart
- 1: Full solar

### disableEcoSmart(chargerId)

- Disable Eco Smart (called Solar Charging in the app)


## Simple example

```python
from wallbox import Wallbox, Statuses
import time
import datetime

w = Wallbox("user@email", "password")

# Authenticate with the credentials above
w.authenticate()

# Print a list of chargers in the account
print(w.getChargersList())

# Get charger data for all chargers in the list, then lock and unlock chargers
for chargerId in w.getChargersList():
    chargerStatus = w.getChargerStatus(chargerId)
    print(f"Charger Status: {chargerStatus}")
    print(f"Lock Charger {chargerId}")
    endDate = datetime.datetime.now()
    startDate = endDate - datetime.timedelta(days = 30)
    sessionList = w.getSessionList(chargerId, startDate, endDate)
    print(f"Session List: {sessionList}")
    w.lockCharger(chargerId)
    time.sleep(10)
    chargerStatus = w.getChargerStatus(chargerId)
    print(f"Charger {chargerId} lock status {chargerStatus['config_data']['locked']}")
    print(f"Unlock Charger {chargerId}")
    w.unlockCharger(chargerId)
    time.sleep(10)
    chargerStatus = w.getChargerStatus(chargerId)
    print(f"Charger {chargerId} lock status {chargerStatus['config_data']['locked']}")
    # Set charger Energy Cost to 0.1€/kWh
    energyCost = w.setEnergyCost(chargerId, 0.1)
    print(f"Charger {chargerId} energy cost {energyCost['energy_price']} {energyCost['currency']['symbol']}")

    # Print the status the charger is currently in using the status id
    print(f"Charger Mode: {Statuses(chargerStatus['status_id']).name}")
```
