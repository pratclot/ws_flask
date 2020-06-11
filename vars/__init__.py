import logging
import os

SLEEP_TIMEOUT = 5
SLEEP_STEP = 0.1
LOCAL_PORT = os.environ["LOCAL_PORT"]
API_PROTO = "http://"
API_SERVER = os.environ["API_SERVER"]
API_PATH = "/go-CP"
TEMPERATURE_ENDPOINTS = {
    "temp_cauldron": "/updateTemp-28-021600873fff",
    "temp_heater": "/updateTemp-28-021600a351ff"
}
RELAY_ENDPOINTS = {
    "heater_status": "/heaterStatus",
    "pump_status": "/pumpStatus"
}
CONTROL_ENDPOINTS = {
    "turn_heater_on": "/turnHeaterOn",
    "turn_heater_off": "/turnHeaterOff"
}
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger()

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)
