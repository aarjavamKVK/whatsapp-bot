import requests

def get_tokens():
    url = "https://accounts.zoho.in/oauth/v2/token"
    params = {
        "grant_type": "authorization_code",
        "client_id": "1000.44ZMWPUT9QUOUHMPHA32CTQ8DW5CYP",
        "client_secret": "4c43bec113ed302c36eb7b1c66c9e4be99d7acd1f2",
        "redirect_uri": "https://localhost/callback",
        "code": "1000.07c4391a3d2b7f3da9c0da989eb2e278.a8f6b74bb4e0f4c75b7fcc172769ea9a"
    }

    response = requests.post(url, params=params)
    print("Status:", response.status_code)
    print("Response:", response.json())

get_tokens()
