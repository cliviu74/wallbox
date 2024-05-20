from wallbox import Wallbox, Statuses
from dotenv import load_dotenv
import os


if "WALLBOX_USER" not in os.environ:
  load_dotenv()

wallboxUsername = os.getenv("WALLBOX_USER")
wallboxPassword = os.getenv("WALLBOX_PASS")

w = Wallbox(wallboxUsername, wallboxPassword)

# Authenticate with the credentials above
w.authenticate()

# Print a list of chargers in the account
print(f"Chargers under the account {wallboxUsername}: {w.getChargersList()}")

for chargerId in w.getChargersList():
  print(f"Charger status for {chargerId}: {Statuses(w.getChargerStatus(chargerId)['status_id']).name}")
