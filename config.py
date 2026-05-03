import os
from pathlib import Path
from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().with_name(".env")
# Load from project-root `.env` deterministically (fixes CWD / interpreter differences).
load_dotenv(dotenv_path=_ENV_PATH, override=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "agrorent.db")
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))
GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or "").strip() or None
GROQ_API_KEY = (os.environ.get("GROQ_API_KEY") or "").strip() or None
RAZORPAY_KEY_ID = (os.environ.get("RAZORPAY_KEY_ID") or "").strip() or None
RAZORPAY_KEY_SECRET = (os.environ.get("RAZORPAY_KEY_SECRET") or "").strip() or None
TWILIO_ACCOUNT_SID = (os.environ.get("TWILIO_ACCOUNT_SID") or "").strip() or None
TWILIO_AUTH_TOKEN = (os.environ.get("TWILIO_AUTH_TOKEN") or "").strip() or None
TWILIO_WHATSAPP_FROM = (os.environ.get("TWILIO_WHATSAPP_FROM") or "").strip() or None
SUPPORTED_LANGUAGES = ["en", "hi", "mr"]
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "??????",
    "mr": "?????",
}
DEFAULT_LOCALE = "en"
MECHANIC_SPECIALIZATIONS = [
    "Tractor", "Harvester", "Pump", "Sprayer", "Tiller", "General Farm Machinery",
]
MECHANIC_REQUEST_STATUSES = ["Pending", "Accepted", "Completed"]
