from flask import Blueprint, request
from twilio.twiml.messaging_response import MessagingResponse
from bot.handler import handle_whatsapp_message

whatsapp_bp = Blueprint('whatsapp', __name__)

@whatsapp_bp.route('/whatsapp', methods=['POST'])
def whatsapp_webhook():
    from_number = request.form.get('From', '')
    body = request.form.get('Body', '').strip()
    media_url = request.form.get('MediaUrl0', None)

    print(f"📱 Message from {from_number}: {body}")

    reply = handle_whatsapp_message(from_number, body, media_url)

    resp = MessagingResponse()
    resp.message(reply)
    return str(resp)
