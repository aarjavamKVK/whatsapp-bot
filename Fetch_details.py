import requests

def get_contact_by_phone(phone_number):
    access_token = " 1000.09ff2d6dd9a2955192e0636c53c6018c.397ff4813b06f7840b16f7cb5286afc5"  # Replace with your latest access token
    organization_id = "60038296879"  # Replace with your actual Zoho Books organization ID

    url = "https://www.zohoapis.in/books/v3/contacts"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }
    params = {
        "phone": phone_number,
        "organization_id": organization_id
    }

    response = requests.get(url, headers=headers, params=params)
    return response.json()
