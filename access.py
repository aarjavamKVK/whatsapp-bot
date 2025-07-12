import requests

def get_access_token():
    url = "https://accounts.zoho.in/oauth/v2/token"
    data = {
        "refresh_token": "1000.5d5cb2f376abf74f9c4d870f312ec097.345177059cd6dc0acdf877c380d8721c",        # ← Replace this
        "client_id": "1000.44ZMWPUT9QUOUHMPHA32CTQ8DW5CYP",                # ← Replace this
        "client_secret": "4c43bec113ed302c36eb7b1c66c9e4be99d7acd1f2",        # ← Replace this
        "grant_type": "refresh_token"
    }

    print("Sending request to get access token...")
    response = requests.post(url, data=data)

    print("Status Code:", response.status_code)

    try:
        json_data = response.json()
        print("Response:", json_data)
        if "access_token" in json_data:
            return json_data["access_token"]
        else:
            print("Error in response. Message:", json_data.get("error"))
            return None
    except Exception as e:
        print("Failed to parse JSON:", e)
        print("Raw response:", response.text)
        return None


# Run this function
token = get_access_token()
print("Access Token:", token)

