# wallbox

Python Module interface for Wallbox EV chargers api

## Usage

### Requirements

Python 3.7 or older
Python modules "requests>=2.22.0", "simplejson>=3.16.0"

### Installation

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

## Simple example

```python
from wallbox import Wallbox

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
    w.lockCharger(chargerId)
    time.sleep(10)
    chargerStatus = w.getChargerStatus(chargerId)
    print(f"Charger {chargerId} lock status {chargerStatus['config_data']['locked']}")
    print(f"Unlock Charger {chargerId}")
    w.unlockCharger(chargerId)
    time.sleep(10)
    chargerStatus = w.getChargerStatus(chargerId)
    print(f"Charger {chargerId} lock status {chargerStatus['config_data']['locked']}")
```
