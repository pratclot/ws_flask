from pip._vendor import requests

from vars import GOOGLE_DISCOVERY_URL


def frange(start, stop, step=1.0):
    while start < stop:
        yield start
        start += step


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()
