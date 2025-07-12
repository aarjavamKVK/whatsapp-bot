from flask import Flask, request
from twilio.rest import Client
from dotenv import load_dotenv
import os
import requests
import logging

load_dotenv()

app = Flask(__name__)

# Setup logging
logging.basicConfig(filename='user_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

# Twilio credentials
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
FROM_WHATSAPP_NUMBER = "whatsapp:+919113287086"  # Twilio WhatsApp number

# Zoho credentials
ZOHO_ACCESS_TOKEN = os.environ.get("ZOHO_ACCESS_TOKEN")
ZOHO_ORGANIZATION_ID = os.environ.get("ZOHO_ORGANIZATION_ID")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    button_payload = request.form.get("ButtonPayload")
    sender = request.form.get("From")

    logging.info(f"Incoming message from: {sender}, Payload: {button_payload}")

    # Extract and clean phone number for Zoho
    if sender and sender.startswith("whatsapp:+91"):
        cleaned_number = sender.replace("whatsapp:+91", "")
    else:
        cleaned_number = sender

    # Log cleaned number
    logging.info(f"Cleaned phone number: {cleaned_number}")

    # Lookup in Zoho
    contact_info = get_contact_by_phone(cleaned_number, ZOHO_ACCESS_TOKEN, ZOHO_ORGANIZATION_ID)
    logging.info(f"Zoho Contact Lookup Result: {contact_info}")

    # Respond based on payload
    if button_payload == "new_cust":
        send_new_customer_flow(sender)
    elif button_payload == "existing_cust":
        send_existing_customer_menu(sender)
    elif button_payload == "place_order":
        send_product_list(sender)
    elif button_payload == "check_order":
        ask_for_order_id(sender)
    else:
        send_welcome_template(sender)

    return "OK", 200


def get_contact_by_phone(phone_number, access_token, organization_id):
    url = f"https://www.zohoapis.in/books/v3/contacts"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }
    params = {
        "phone": phone_number,
        "organization_id": organization_id
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.json()
    except Exception as e:
        logging.error(f"Error calling Zoho API: {e}")
        return {}

# === Templates ===

def send_welcome_template(to):
    client.messages.create(
        from_=FROM_WHATSAPP_NUMBER,
        to=to,
        content_sid="HX6a4c2a1dafe3d744f4d42bacd1ce5204"  # Welcome template ID with buttons
    )

def send_new_customer_flow(to):
    client.messages.create(
        from_=FROM_WHATSAPP_NUMBER,
        to=to,
        content_sid="HX1f2d86142ede8d5dcd03c810cb7ced08"  # Full flow content SID for New Customer
    )

def send_existing_customer_menu(to):
    client.messages.create(
        from_=FROM_WHATSAPP_NUMBER,
        to=to,
        content_sid="HXca0c40309b0fc113ceab8462e07aebe0"  # Existing Customer flow template
    )

def send_product_list(to):
    client.messages.create(
        from_=FROM_WHATSAPP_NUMBER,
        to=to,
        body="🛍️ Our Products:\n• Paper Cups\n• Plates\n• Napkins\n• Party Packs\n\nReply with the product name to order."
    )

def ask_for_order_id(to):
    client.messages.create(
        from_=FROM_WHATSAPP_NUMBER,
        to=to,
        body="🔍 Please enter your Order ID or Registered Number to check status."
    )

# if __name__ == "__main__":
#     app.run(port=8000, debug=True)
