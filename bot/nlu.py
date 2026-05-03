import json
import groq
from config import GROQ_API_KEY

_client = None


def _get_client():
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is missing. Check your .env file.")
        _client = groq.Groq(api_key=GROQ_API_KEY)
    return _client


SYSTEM_PROMPT = """
You are an intent extraction engine for AgroRent - an Indian farm machinery rental platform.
A farmer sent a WhatsApp message. Extract structured info and return ONLY valid JSON, nothing else.

Return exactly this structure:
{
  "intent": one of [search_equipment, my_bookings, crop_recommendation, help, unknown],
  "language": detected language code (hi, mr, pa, gu, kn, te, ta, bn, en),
  "equipment_type": null or string (tractor, harvester, pump, sprayer, tiller),
  "crop": null or string (wheat, rice, sugarcane, cotton, soybean),
  "location": null or string,
  "selection_number": null or integer (if user replied with a number like 1, 2, 3)
}

Examples:
"hi" → intent: help, language: en
"mujhe tractor chahiye" → intent: search_equipment, language: hi, equipment_type: tractor
"ट्रॅक्टर हवा आहे" → intent: search_equipment, language: mr, equipment_type: tractor
"gehun ke liye kya chahiye" → intent: crop_recommendation, language: hi, crop: wheat
"my bookings" → intent: my_bookings, language: en
"1" → intent: unknown, selection_number: 1, language: en
"pehla wala" → intent: unknown, selection_number: 1, language: hi
"""

CROP_TO_EQUIPMENT = {
    'wheat': ['harvester', 'thresher', 'tractor'],
    'rice': ['transplanter', 'harvester', 'pump'],
    'sugarcane': ['harvester', 'tractor', 'cutter'],
    'cotton': ['sprayer', 'tractor', 'picker'],
    'soybean': ['harvester', 'sprayer', 'tractor'],
    'corn': ['planter', 'harvester', 'tractor'],
    'onion': ['transplanter', 'sprayer', 'tractor'],
}


def extract_intent(message: str) -> dict:
    """Send message to Groq and get structured intent back"""
    try:
        response = _get_client().chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Farmer message: {message}"}
            ],
            temperature=0.0  # Keep extraction deterministic
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        if '```' in raw:
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        print(f"NLU error: {e}")
        return {
            "intent": "unknown",
            "language": "en",
            "equipment_type": None,
            "crop": None,
            "location": None,
            "selection_number": None
        }


def translate_to_language(text: str, language: str) -> str:
    """Translate bot response to farmer's language"""
    if language in ('en', 'english', None):
        return text
    try:
        response = _get_client().chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Translate this WhatsApp message to language code '{language}'. "
                        "Keep emojis, numbers, phone numbers, and *bold* formatting. "
                        "Return ONLY the translated text, nothing else."
                    )
                },
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Translation error: {e}")
        return text


def get_crop_equipment(crop: str) -> list:
    """Return recommended equipment list for a crop"""
    return CROP_TO_EQUIPMENT.get(crop.lower(), [])
