import requests
import json
import logging

_LOGGER = logging.getLogger(__name__)


def get_homes_data():
    url = "https://app.netatmo.net/api/homesdata"

    headers = {
        "Accept-Encoding": "gzip",
        "Authorization": "Bearer 641f1221ea8e82cd940a2e6b|6d17c7f6d75d55026453daae4f58c18a",
        "Connection": "Keep-Alive",
        "Content-Type": "application/json; charset=utf-8",
        "Host": "app.netatmo.net",
        "User-Agent": "NetatmoApp(Security/v4.1.1.3/4401103) Android(15/Google/sdk_gphone64_arm64)",
    }

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        _LOGGER.error(f"Errore nella richiesta: {e}")
        return None


def get_token(username, password):
    url = "https://app.netatmo.net/oauth2/token"

    headers = {
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "app.netatmo.net",
        "User-Agent": "NetatmoApp(Security/v4.1.1.3/4401103) Android(15/Google/sdk_gphone64_arm64)",
    }

    data = {
        "password": password,
        "app_version": "4.1.1.3",
        "grant_type": "password",
        "scope": "security_scopes",
        "client_secret": "8ab584d62ca2a77e37ccc6b2c7e4f29e",
        "client_id": "na_client_android_welcome",
        "username": username,
    }

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        _LOGGER.error(f"Errore nella richiesta del token: {e}")
        return None


def open_door(access_token, home_id, bridge, bridge_id, lock_state):
    """Imposta lo stato della serratura."""
    url = "https://app.netatmo.net/syncapi/v1/setstate"

    headers = {
        "Accept-Encoding": "gzip",
        "Authorization": f"Bearer {access_token}",
        "Connection": "Keep-Alive",
        "Content-Type": "application/json; charset=utf-8",
        "Host": "app.netatmo.net",
        "User-Agent": "NetatmoApp(Security/v4.1.1.3/4401103) Android(15/Google/sdk_gphone64_arm64)",
    }

    body = {
        "app_type": "app_camera",
        "app_version": "4.1.1.3",
        "home": {
            "timezone": "Europe/Rome",
            "id": home_id,
            "modules": [{"bridge": bridge, "lock": lock_state, "id": bridge_id}],
        },
    }

    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        _LOGGER.error(f"Errore nell'impostazione dello stato: {e}")
        return None


def getNDL(access_token):
    """Ottiene i dati delle serrature NDL."""
    url = "https://app.netatmo.net/api/homesdata"

    headers = {
        "Accept-Encoding": "gzip",
        "Authorization": f"Bearer {access_token}",
        "Connection": "Keep-Alive",
        "Content-Type": "application/json; charset=utf-8",
        "Host": "app.netatmo.net",
        "User-Agent": "NetatmoApp(Security/v4.1.1.3/4401103) Android(15/Google/sdk_gphone64_arm64)",
    }

    body = {
        "app_type": "app_camera",
        "app_version": "4.1.1.3",
        "device_types": [
            "BNMH",
            "BNCX",
            "BFII",
            "BPAC",
            "BPVC",
            "BNC1",
            "BDIY",
            "BNHY",
            "NACamera",
            "NOC",
            "NDB",
            "NSD",
            "NCO",
            "NDL",
        ],
        "sync_measurements": False,
    }

    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        _LOGGER.info(response.json())
        return response.json()
    except requests.exceptions.RequestException as e:
        _LOGGER.error(f"Errore nel recupero dei dati NDL: {e}")
        return None
