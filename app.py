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

    # Google Sheets: log to Sheet1 & check Sheet2
    try:
        gc = gspread.service_account(filename="/etc/secrets/credentials.json")
        sh = gc.open("WhatsappBotUsers")
        worksheet_main = sh.sheet1
        worksheet_main.append_row([cleaned_number])

        worksheet_db = sh.worksheet("Sheet2")
        db_numbers = worksheet_db.col_values(4)[1:]  # Column D, skip header
    except Exception as e:
        logging.error(f"Google Sheets Error: {e}")
        db_numbers = []

    # Optional: Zoho contact lookup
    contact_info = get_contact_by_phone(cleaned_number, ZOHO_ACCESS_TOKEN, ZOHO_ORGANIZATION_ID)

    # ===== Logic Flow =====
    if button_payload:
        if button_payload == "place_order":
            send_product_list(sender)
        elif button_payload == "check_order":
            ask_for_order_id(sender)
        elif button_payload == "contact_support":
            send_support_message(sender)
        elif button_payload == "product_catalogue":
            send_catalogue_pdf(sender)
        elif button_payload == "new_cust":
            send_new_customer_flow(sender)
            try:
                if cleaned_number not in db_numbers:
                    worksheet_db.append_row(["", "", "", cleaned_number])
                    logging.info("Added new number to Sheet2")
            except Exception as e:
                logging.error(f"Failed to append to Sheet2: {e}")
        else:
            send_welcome_template(sender)

    elif incoming_msg == "hi":
        if cleaned_number in db_numbers:
            send_existing_customer_menu(sender)
        else:
            send_welcome_template(sender)
    else:
        logging.info("Message ignored: not 'hi' or valid button")

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

# === Message Handlers ===

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

def send_product_list(to):
    product_message = (
        "🛍️ *Our Product Categories:*\n\n"
        "*Fabric Products:*\n"
        "• BOPP Laminated Bags\n"
        "• PP Woven Bags\n"
        "   - Cement | Sugar | Fertilizer Bags\n"
        "• Leno Bags & Rolls\n"
        "• FIBC | Yarn\n\n"
        "*Paper Products:*\n"
        "• Paper Bags, Cups, Boxes, Trays\n\n"
        "*Agro & Signage:*\n"
        "• Irrigation Pipe, Mulch Film, Flex, ACP Sheets\n"
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

def send_catalogue_pdf(to):
    client.messages.create(
        from_=FROM_WHATSAPP_NUMBER,
        to=to,
        body=(
            "📄 *Here's our Product Catalogue:*\n\n"
            "https://www.canva.com/design/DAGA-qWSGWQ/iOPAUG5ny7cLGNkUukTdkA/view?utm_content=DAGA-qWSGWQ&utm_campaign=designshare&utm_medium=link&utm_source=editor#31"
        )
    )
