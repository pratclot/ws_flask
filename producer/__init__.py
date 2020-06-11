import json

from pip._vendor import requests

from vars import API_PROTO, API_SERVER, API_PATH, TEMPERATURE_ENDPOINTS, RELAY_ENDPOINTS


def producer():
    url = API_PROTO + API_SERVER + API_PATH
    data1 = {k: requests.get(f'{url}{v}').content.decode().strip() for k, v in TEMPERATURE_ENDPOINTS.items()}
    data2 = {k: requests.get(f'{url}{v}').content.decode().strip() for k, v in RELAY_ENDPOINTS.items()}
    return json.dumps({**data1, **data2})


def act_on_heater(api_endpoint):
    url = API_PROTO + API_SERVER + API_PATH + api_endpoint
    response = json.dumps(requests.get(url).content.decode().strip())
    return response
