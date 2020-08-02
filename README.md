# wallbox
Python Module interface for Wallbox EV chargers api

## Usage
#### Installation
`pip install wallbox`

#### Simple example
```python
from wallbox import Wallbox

from wallbox import Wallbox
w = Wallbox("email@domain.tld","password")

# Authenticate with the credentials above
w.authenticate()

# Print a list of chargers in the account
print(w.getChargersList())

# Get charger data for all chargers in the list 
for chargerId in w.getChargersList():
    print(w.getChargerData(chargerId))
```

