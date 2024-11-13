import requests
import json

def get_homes_data():
    url = "https://app.netatmo.net/api/homesdata"
    
    headers = {
        'Accept-Encoding': 'gzip',
        'Authorization': 'Bearer 641f1221ea8e82cd940a2e6b|6d17c7f6d75d55026453daae4f58c18a',
        'Connection': 'Keep-Alive',
        'Content-Type': 'application/json; charset=utf-8',
        'Host': 'app.netatmo.net',
        'User-Agent': 'NetatmoApp(Security/v4.1.1.3/4401103) Android(15/Google/sdk_gphone64_arm64)'
    }

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Errore nella richiesta: {e}")
        return None

def get_token():
    url = "https://app.netatmo.net/oauth2/token"
    
    headers = {
        'Accept-Encoding': 'gzip',
        'Connection': 'Keep-Alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'app.netatmo.net',
        'User-Agent': 'NetatmoApp(Security/v4.1.1.3/4401103) Android(15/Google/sdk_gphone64_arm64)'
    }

    data = {
        'password': '!Spirit02zx',
        'app_version': '4.1.1.3',
        'grant_type': 'password', 
        'scope': 'security_scopes',
        'client_secret': '8ab584d62ca2a77e37ccc6b2c7e4f29e',
        'client_id': 'na_client_android_welcome',
        'username': 'vismara.lorenzo@gmail.com'
    }

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Errore nella richiesta del token: {e}")
        return None

print(get_token())