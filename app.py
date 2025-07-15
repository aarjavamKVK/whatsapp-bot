from flask import Flask, request
from twilio.rest import Client
import os
import requests
import logging
import gspread

app = Flask(__name__)

# Setup logging
logging.basicConfig(filename='user_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

# Twilio credentials
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
FROM_WHATSAPP_NUMBER = "whatsapp:+919113287086"

# Zoho credentials
ZOHO_ACCESS_TOKEN = os.environ.get("ZOHO_ACCESS_TOKEN")
ZOHO_ORGANIZATION_ID = os.environ.get("ZOHO_ORGANIZATION_ID")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    print("Full Payload:", request.form)

    button_payload = request.form.get("ButtonPayload")
    incoming_msg = request.form.get("Body", "").strip().lower()
    sender = request.form.get("From")

    cleaned_number = sender.replace("whatsapp:+91", "") if sender and sender.startswith("whatsapp:+91") else sender
    logging.info(f"Incoming from: {cleaned_number}, Payload: {button_payload}, Message: {incoming_msg}")

    try:
        gc = gspread.service_account(filename="/etc/secrets/credentials.json")
        sh = gc.open("WhatsappBotUsers")
        worksheet_main = sh.sheet1
        worksheet_main.append_row([cleaned_number])  # Log all numbers in Sheet1

        worksheet_db = sh.worksheet("Sheet2")
        db_numbers = worksheet_db.col_values(4)[1:]  # Column D
    except Exception as e:
        logging.error(f"Google Sheets Error: {e}")
        db_numbers = []

    contact_info = get_contact_by_phone(cleaned_number, ZOHO_ACCESS_TOKEN, ZOHO_ORGANIZATION_ID)

    # ===== FINAL BOT FLOW LOGIC =====
    if cleaned_number in db_numbers:
        # Existing customer — only respond if they say "hi"
        if incoming_msg == "hi":
            send_existing_customer_menu(sender)
        else:
            logging.info("Existing user message ignored unless 'hi'")
    else:
        # New customer flow
        if button_payload == "new_cust":
            send_new_customer_flow(sender)
            try:
                if cleaned_number not in db_numbers:
                    worksheet_db.append_row(["", "", "", cleaned_number])  # Add to Sheet2 (col D)
                    logging.info("Added new customer to Sheet2")
            except Exception as e:
                logging.error(f"Error saving to Sheet2: {e}")
        elif button_payload == "product_catalogue":
            send_catalogue_pdf(sender)
        else:
            send_welcome_template(sender)

    return "OK", 200

def get_contact_by_phone(phone_number, access_token, organization_id):
    url = f"https://www.zohoapis.in/books/v3/contacts"
    headers = { "Authorization": f"Zoho-oauthtoken {access_token}" }
    params = { "phone": phone_number, "organization_id": organization_id }
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.json()
    except Exception as e:
        logging.error(f"Error calling Zoho API: {e}")
        return {}

# === WhatsApp Message Handlers ===

def send_welcome_template(to):
    client.messages.create(
        from_=FROM_WHATSAPP_NUMBER,
        to=to,
        content_sid="HX157e72799d3feb8a8a3533f0a4c0c9db"
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

def send_catalogue_pdf(to):
    client.messages.create(
        from_=FROM_WHATSAPP_NUMBER,
        to=to,
        body=(
            "📄 *Here's our Product Catalogue:*\n\n"
            "https://www.canva.com/design/DAGA-qWSGWQ/iOPAUG5ny7cLGNkUukTdkA/"
        )
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

# === End ===
