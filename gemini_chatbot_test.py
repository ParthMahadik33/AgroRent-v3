import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai


PLATFORM_DATA = """
AgroRent Platform Information:

About AgroRent:
AgroRent is a comprehensive agricultural equipment rental platform connecting farmers with equipment owners. We make farming more affordable and accessible by enabling equipment sharing.

Services Offered:
1. Equipment Rental - Tractors, harvesters, plows, seeders, sprayers
2. Booking System - Easy online booking with calendar availability
3. Delivery Service - Equipment delivered to your location
4. Maintenance Support - All equipment is well-maintained and insured
5. Flexible Pricing - Hourly, daily, and weekly rental options
"""


AGRORENT_SYSTEM_PROMPT = f"""You are a helpful assistant for AgroRent, an agricultural equipment rental platform.

{PLATFORM_DATA}

Instructions:
- Be friendly, helpful, and concise
- Answer questions about equipment, pricing, booking, and services
- Keep responses brief unless detailed information is requested
"""


def main():
    env_path = Path(__file__).resolve().with_name(".env")
    load_dotenv(dotenv_path=env_path, override=True)

    safe_env_path = env_path.as_posix().encode("unicode_escape").decode("ascii")
    print(f"Loaded .env from: {safe_env_path}")

    key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set (check your .env).")

    print(f"GEMINI_API_KEY fingerprint: prefix={key[:6]!r}, suffix={key[-4:]!r}, len={len(key)}")

    client = genai.Client(api_key=key)

    user_message = "Hello. I want to rent a tractor for 2 days. What should I do?"
    full_prompt = f"{AGRORENT_SYSTEM_PROMPT}\n\nUser: {user_message}\nAssistant:"

    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=full_prompt,
    )

    print("\nGemini chatbot response:\n")
    print(resp.text if hasattr(resp, "text") else resp)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Chatbot test failed:")
        try:
            print(repr(e))
        except Exception:
            print(str(e).encode("unicode_escape").decode("ascii"))
        raise

