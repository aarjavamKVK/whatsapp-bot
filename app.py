from flask import Flask, request
from twilio.rest import Client
import os
import requests
import logging
import gspread

app = Flask(__name__)

# Setup logging
logging.basicConfig(filename='user_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

# Twilio credentials from Render Environment Variables
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
FROM_WHATSAPP_NUMBER = "whatsapp:+919113287086"

# Zoho credentials from Render Environment Variables
ZOHO_ACCESS_TOKEN = os.environ.get("ZOHO_ACCESS_TOKEN")
ZOHO_ORGANIZATION_ID = os.environ.get("ZOHO_ORGANIZATION_ID")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    button_payload = request.form.get("ButtonPayload")
    sender = request.form.get("From")

    logging.info(f"Incoming message from: {sender}, Payload: {button_payload}")

    # Extract and clean phone number
    cleaned_number = sender.replace("whatsapp:+91", "") if sender and sender.startswith("whatsapp:+91") else sender
    logging.info(f"Cleaned phone number: {cleaned_number}")

    try:
        # Connect to Google Sheets
        gc = gspread.service_account(filename="/etc/secrets/credentials.json")
        sh = gc.open("WhatsappBotUsers")

        # Append to Sheet1 (log number)
        sheet1 = sh.sheet1
        sheet1.append_row([cleaned_number])
        logging.info("Saved number to Sheet1")

        # Check Sheet2 column D for existing number
        sheet2 = sh.get_worksheet(1)  # Sheet2 (index 1)
        column_d = sheet2.col_values(4)[1:]  # Skip header in D1
        column_d = [num.strip() for num in column_d if num.strip()]

        if cleaned_number in column_d:
            logging.info("Number exists in Sheet2 → sending existing customer menu")
            send_existing_customer_menu(sender)
        else:
            logging.info("Number not in Sheet2 → sending welcome template")
            send_welcome_template(sender)

    except Exception as e:
        logging.error(f"Google Sheets error: {e}")
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
        content_sid="HX6a4c2a1dafe3d744f4d42bacd1ce5204"
    )

def send_new_customer_flow(to):
    client.messages.create(
        from_=FROM_WHATSAPP_NUMBER,
        to=to,
        content_sid="HX1f2d86142ede8d5dcd03c810cb7ced08"
    )

def send_existing_customer_menu(to):
    client.messages.create(
        from_=FROM_WHATSAPP_NUMBER,
        to=to,
        content_sid="HXca0c40309b0fc113ceab8462e07aebe0"
    )

def send_product_list(to):
    client.messages.create(
        from_=FROM_WHATSAPP_NUMBER,
        to=to,
        body="🍭️ Our Products:\n• Paper Cups\n• Plates\n• Napkins\n• Party Packs\n\nReply with the product name to order."
    )

def ask_for_order_id(to):
    client.messages.create(
        from_=FROM_WHATSAPP_NUMBER,
        to=to,
        body="🔍 Please enter your Order ID or Registered Number to check status."
    )

# Uncomment for local testing
# if __name__ == "__main__":
#     app.run(port=8000, debug=True)