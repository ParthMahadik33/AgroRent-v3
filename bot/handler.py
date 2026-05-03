from bot.nlu import extract_intent, translate_to_language, get_crop_equipment
from database import get_db

# Store last search results per user (simple in-memory)
user_sessions = {}

def handle_whatsapp_message(from_number, body, media_url=None):
    """Main bot handler with Gemini NLU"""

    # Get user session
    session = user_sessions.get(from_number, {})

    # Extract intent using Gemini
    nlu = extract_intent(body)
    intent = nlu.get('intent', 'unknown')
    language = nlu.get('language', 'en')
    equipment_type = nlu.get('equipment_type')
    crop = nlu.get('crop')
    selection_number = nlu.get('selection_number')

    # Save language preference
    session['language'] = language
    user_sessions[from_number] = session

    # Route to correct handler
    if intent == 'help':
        reply = build_help_menu()

    elif intent == 'search_equipment' and equipment_type:
        results = search_equipment(equipment_type)
        session['last_results'] = results['data']
        user_sessions[from_number] = session
        reply = results['message']

    elif intent == 'crop_recommendation' and crop:
        equipment_list = get_crop_equipment(crop)
        if equipment_list:
            reply = f"🌱 For *{crop}*, you need:\n"
            reply += "\n".join(f"  • {e.title()}" for e in equipment_list)
            reply += f"\n\nShall I search for *{equipment_list[0]}*? Reply *yes* or type equipment name."
            session['suggested_equipment'] = equipment_list[0]
            user_sessions[from_number] = session
        else:
            reply = f"Try searching directly: *tractor*, *harvester*, *pump*"

    elif intent == 'my_bookings':
        reply = get_my_bookings(from_number)

    elif selection_number:
        last_results = session.get('last_results', [])
        idx = selection_number - 1
        if 0 <= idx < len(last_results):
            item = last_results[idx]
            reply = build_listing_detail(item, idx + 1)
        else:
            reply = "Invalid selection. Please pick a number from the list."

    elif body.strip().lower() in ('yes', 'haan', 'ho', 'ha'):
        suggested = session.get('suggested_equipment')
        if suggested:
            results = search_equipment(suggested)
            session['last_results'] = results['data']
            user_sessions[from_number] = session
            reply = results['message']
        else:
            reply = build_help_menu()

    else:
        reply = (
            "I didn't understand 🤔\n\n"
            "Try:\n"
            "• *tractor* — find tractors\n"
            "• *wheat* — crop recommendations\n"
            "• *my bookings* — your rentals\n"
            "• *help* — full menu"
        )

    # Translate to farmer's language
    if language not in ('en', 'english'):
        reply = translate_to_language(reply, language)

    return reply


def build_help_menu():
    return (
        "🌾 *Welcome to AgroRent!*\n"
        "India's trusted farm machinery rental platform.\n\n"
        "*What can I do?*\n\n"
        "🚜 Find equipment — type name\n"
        "   _tractor, harvester, pump, sprayer_\n\n"
        "🌱 Crop recommendations\n"
        "   _wheat, rice, sugarcane, cotton_\n\n"
        "📋 My bookings — type _my bookings_\n\n"
        "🌍 Works in Hindi, Marathi & more!\n\n"
        "_Powered by AgroRent_ 🌿"
    )


def search_equipment(equipment_type):
    """Search DB and return results with data for session storage"""
    try:
        conn = get_db()
        rows = conn.execute('''
            SELECT l.id, l.title, l.price, l.pricing_type, l.state,
                   l.district, l.village_city, l.owner_name,
                   l.condition, l.transport_included, l.phone
            FROM listings l
            WHERE l.status = "available"
            AND (LOWER(l.category) LIKE ?
            OR LOWER(l.equipment_name) LIKE ?
            OR LOWER(l.title) LIKE ?)
            LIMIT 3
        ''', (f'%{equipment_type}%', f'%{equipment_type}%', f'%{equipment_type}%')).fetchall()
        conn.close()

        data = [dict(r) for r in rows]

        if not data:
            return {
                'message': f"😔 No *{equipment_type}* available right now.\n\nVisit: agrorent-r3i4.onrender.com",
                'data': []
            }

        msg = f"🚜 *Available {equipment_type.title()}s:*\n\n"
        for i, r in enumerate(data, 1):
            msg += (
                f"*{i}. {r['title']}*\n"
                f"   📍 {r['village_city']}, {r['district']}\n"
                f"   💰 ₹{r['price']}/{r['pricing_type']}\n"
                f"   👤 {r['owner_name']}\n"
                f"   🔧 {r['condition']}\n\n"
            )
        msg += "Reply *1*, *2*, or *3* for full details & owner contact."
        return {'message': msg, 'data': data}

    except Exception as e:
        print(f"DB Error: {e}")
        return {'message': "Something went wrong. Please try again.", 'data': []}


def build_listing_detail(item, number):
    """Build detailed view of a single listing"""
    return (
        f"🚜 *{item['title']}*\n\n"
        f"📍 {item['village_city']}, {item['district']}, {item['state']}\n"
        f"💰 ₹{item['price']} per {item['pricing_type']}\n"
        f"🔧 Condition: {item['condition']}\n"
        f"🚚 Transport: {item['transport_included']}\n"
        f"👤 Owner: {item['owner_name']}\n"
        f"📞 Contact: {item['phone']}\n\n"
        f"🔗 Book online: agrorent-r3i4.onrender.com\n\n"
        f"Type *help* to search more equipment."
    )


def get_my_bookings(from_number):
    """Get active bookings for this phone number"""
    try:
        phone = from_number.replace('whatsapp:+91', '').replace('whatsapp:+', '')
        conn = get_db()
        rows = conn.execute('''
            SELECT r.id, l.title, r.start_date, r.end_date,
                   r.total_amount, r.status
            FROM rentals r
            JOIN listings l ON r.listing_id = l.id
            JOIN users u ON r.user_id = u.id
            WHERE u.phone = ?
            AND r.status IN ("Active", "Pending")
            ORDER BY r.created_at DESC
            LIMIT 5
        ''', (phone,)).fetchall()
        conn.close()

        if not rows:
            return (
                "📋 No active bookings found.\n\n"
                "Search for equipment:\n"
                "*tractor*, *harvester*, *pump*"
            )

        msg = "📋 *Your Active Bookings:*\n\n"
        for r in rows:
            msg += (
                f"• *{r['title']}*\n"
                f"  {r['start_date']} → {r['end_date']}\n"
                f"  ₹{r['total_amount']} | {r['status']}\n\n"
            )
        return msg

    except Exception as e:
        print(f"Bookings error: {e}")
        return "Could not fetch bookings. Try again later."
