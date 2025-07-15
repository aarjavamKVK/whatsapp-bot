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
    print("Full Payload:", request.form)

    button_payload = request.form.get("ButtonPayload")
    sender = request.form.get("From")

    logging.info(f"Incoming message from: {sender}, Payload: {button_payload}")

    # Extract and clean phone number
    cleaned_number = sender.replace("whatsapp:+91", "") if sender and sender.startswith("whatsapp:+91") else sender
    logging.info(f"Cleaned phone number: {cleaned_number}")

    # Connect to Google Sheet and check if number exists in Sheet2 column D
    try:
        gc = gspread.service_account(filename="/etc/secrets/credentials.json")
        sh = gc.open("WhatsappBotUsers")
        worksheet_main = sh.sheet1
        worksheet_main.append_row([cleaned_number])  # Log incoming number to Sheet1

        worksheet_db = sh.worksheet("Sheet2")
        db_numbers = worksheet_db.col_values(4)[1:]  # Column D, skipping header
        logging.info("Fetched database numbers from Sheet2")
    except Exception as e:
        logging.error(f"Google Sheets error: {e}")
        db_numbers = []

    # Lookup in Zoho (optional)
    contact_info = get_contact_by_phone(cleaned_number, ZOHO_ACCESS_TOKEN, ZOHO_ORGANIZATION_ID)
    logging.info(f"Zoho Contact Lookup Result: {contact_info}")

    print("Sender:", sender)
    print("Cleaned Number:", cleaned_number)
    print("Zoho Response:", contact_info)

    # === Updated Flow ===
    if cleaned_number in db_numbers:
        if button_payload == "place_order":
            send_product_list(sender)
        elif button_payload == "check_order":
            ask_for_order_id(sender)
        elif button_payload == "contact_support":
            send_support_message(sender)
        else:
            send_existing_customer_menu(sender)
    else:
        if button_payload == "new_cust":
            send_new_customer_flow(sender)
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
    product_message = (
        "🛍️ *Our Product Categories:*\n\n"
        "*Fabric Products:*\n"
        • BOPP Laminated Bags\n"
        • PP Woven Bags\n"
        "   - PP Woven Cement Bags\n"
        "   - PP Woven Sugar Bags\n"
        "   - PP Woven Chemical | Fertiliser Bags\n"
        • Leno | Mesh Bags\n"
        • PP Woven Rolls\n"
        • Leno Fabric\n"
        • PP Woven Handle Bags\n"
        • FIBC Bags\n"
        • Multifilament Yarn\n\n"

        "*Paper Products:*\n"
        • Paper Bags\n"
        • Paper Cups\n"
        • Paper Food Boxes\n"
        • Paper Food Containers\n"
        • Burger Boxes\n"
        • Cake Boxes\n"
        • Boat Trays\n\n"

        "*Agricultural Products:*\n"
        • Drip Irrigation Pipe, Level Tube, Braided Hose, And Suction Hose\n"
        • Layflat Tube\n"
        • Mulch Film\n"
        • Pond Liner\n"
        • Shade Net\n"
        • Tapes\n"
        • Tarpaulin\n\n"

        "*Flex and Sign Boards:*\n"
        • Backlit Flex Banner\n"
        • PVC Foam Board\n"
        • Aluminium Composite Panel\n\n"

        "*Raw Materials*"
    )

    client.messages.create(
        from_=FROM_WHATSAPP_NUMBER,
        to=to,
        body=product_message
    )

def ask_for_order_id(to):
    client.messages.create(
        from_=FROM_WHATSAPP_NUMBER,
        to=to,
        body="🔍 Please enter your Order ID or Registered Number to check status."
    )

def send_support_message(to):
    client.messages.create(
        from_=FROM_WHATSAPP_NUMBER,
        to=to,
        body="📞 Our support team will contact you shortly. You may also call us directly at +91-XXXXXXXXXX."
    )

# Optional for local testing
# if __name__ == "__main__":
#     app.run(port=8000, debug=True)

