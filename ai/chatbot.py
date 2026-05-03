from flask import jsonify, request
from google import genai
from config import GEMINI_API_KEY

_client = None


def _get_client():
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is missing. Check your .env file.")
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client

PLATFORM_DATA = """
AgroRent Platform Information:

About AgroRent:
AgroRent is a comprehensive agricultural equipment rental platform connecting farmers with equipment owners. We make farming more affordable and accessible by enabling equipment sharing.

Services Offered:
1. Equipment Rental - Tractors, harvesters, plows, seeders, sprayers
2. Booking System - Easy online booking with calendar availability
3. Delivery Service - Equipment delivered to your farm
4. Maintenance Support - All equipment is well-maintained and insured
5. Flexible Pricing - Hourly, daily, and weekly rental options

How to Book:
1. Browse available equipment
2. Check availability calendar
3. Select rental duration
4. Complete payment
5. Equipment delivered to your location

Websites links for traversal:
Renting: https://agrorent-r3i4.onrender.com/renting
About: https://agrorent-r3i4.onrender.com/about
Market overview: https://agrorent-r3i4.onrender.com/market
Listings: https://agrorent-r3i4.onrender.com/listing
Heatmap: https://agrorent-r3i4.onrender.com/heatmap
Mechanics: https://agrorent-r3i4.onrender.com/mechanics

Contact Information:
- Phone: +91 9930235462
- Email: parthmahadik752@gmail.com
- Hours: 24/7 customer support

Coverage Area:
We serve rural and agricultural areas across multiple states. Check availability in your region.

Benefits:
- Save money on expensive equipment purchases
- Access latest farming technology
- No maintenance hassles
- Flexible rental periods
- Trained operators available on request
"""

AGRORENT_SYSTEM_PROMPT = f"""You are a helpful assistant for AgroRent, an agricultural equipment rental platform.

{PLATFORM_DATA}

Instructions:
- Be friendly, helpful, and concise
- Answer questions about equipment, pricing, booking, and services
- Any farming related questions, answer them with the most relevant information from your intelligence example:" have x acres of land what equipemnt should i rent".
- If asked about something not in the data, politely say you'll connect them with support
- Keep responses brief (2-3 sentences) unless detailed information is requested
- Use a warm, professional tone suitable for farmers
- If someone wants to book, guide them through the process
- If someone wants to rent equipment, guide them through the process and provide links from platform data
- IMPORTANT: When providing links, include the full URL (e.g., https://agrorent-r3i4.onrender.com/renting) so they become clickable. You can use markdown format [link text](url) or just include the URL directly."""

def chat():
    """Handle chat messages from the frontend"""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Combine system prompt with user message
        full_prompt = f"{AGRORENT_SYSTEM_PROMPT}\n\nUser: {user_message}\nAssistant:"
        
        # Generate response using Gemini
        response = _get_client().models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt
        )
        
        # Extract the response text
        bot_response = response.text if hasattr(response, 'text') else str(response)
        
        return jsonify({
            'response': bot_response,
            'status': 'success'
        })
    
    except Exception as e:
        return jsonify({
            'error': f'An error occurred: {str(e)}',
            'status': 'error'
        }), 500
