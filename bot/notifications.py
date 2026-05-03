from twilio.rest import Client

from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM

_twilio_client = None


def _get_twilio_client():
    global _twilio_client
    if _twilio_client is None:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            raise RuntimeError('TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN not configured')
        _twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    return _twilio_client


def send_whatsapp(to_phone, message):
    """Send WhatsApp message via Twilio"""
    try:
        phone = str(to_phone).strip()
        if not phone.startswith('+'):
            phone = '+91' + phone.lstrip('0')

        from_num = TWILIO_WHATSAPP_FROM or 'whatsapp:+14155238886'
        if not str(from_num).startswith('whatsapp:'):
            from_num = f'whatsapp:{from_num}'
        to_addr = phone if str(phone).startswith('whatsapp:') else f'whatsapp:{phone}'
        _get_twilio_client().messages.create(
            from_=from_num,
            to=to_addr,
            body=message,
        )
        print(f'✅ WhatsApp sent to {phone}')
    except Exception as e:
        print(f'❌ WhatsApp send error: {e}')


def notify_owner_new_booking(rental):
    """Notify owner when farmer books and pays (rental is a mapping/dict)."""
    message = (
        f'🎉 *New Booking on AgroRent!*\n\n'
        f'Equipment: *{rental["title"]}*\n'
        f'Farmer: {rental["farmer_name"]}\n'
        f'Farmer Phone: {rental["farmer_phone"]}\n'
        f'Dates: {rental["start_date"]} → {rental["end_date"]}\n'
        f'Amount: ₹{rental["total_amount"]} ✅ PAID\n\n'
        f'⏰ You have *2 hours* to cancel if unavailable.\n'
        f'After 2 hours booking auto-confirms.\n\n'
        f'To cancel reply: *CANCEL {rental["id"]}*\n'
        f'Or visit: agrorent-r3i4.onrender.com/listdashboard'
    )
    send_whatsapp(rental['owner_phone'], message)


def notify_farmer_cancelled(rental):
    """Notify farmer when owner cancels."""
    message = (
        f'❌ *Booking Cancelled*\n\n'
        f'Equipment: *{rental["title"]}*\n'
        f'Owner: {rental["owner_name"]}\n\n'
        f'💰 Full refund of ₹{rental["total_amount"]} initiated.\n'
        f'Refund will appear in 5-7 business days.\n\n'
        f"We're sorry for the inconvenience.\n"
        f'Search for other equipment:\n'
        f'agrorent-r3i4.onrender.com/renting'
    )
    send_whatsapp(rental['farmer_phone'], message)


def notify_farmer_confirmed(rental):
    """Notify farmer when booking auto-confirms after 2 hours."""
    message = (
        f'✅ *Booking Confirmed!*\n\n'
        f'Equipment: *{rental["title"]}*\n'
        f'Owner: {rental["owner_name"]}\n'
        f'Owner Phone: {rental["owner_phone"]}\n'
        f'Dates: {rental["start_date"]} → {rental["end_date"]}\n'
        f'Amount Paid: ₹{rental["total_amount"]}\n\n'
        f'Have a great harvest! 🌾\n'
        f'_Powered by AgroRent_'
    )
    send_whatsapp(rental['farmer_phone'], message)
