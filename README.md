# 🌾 AgroRent — Farm Machinery Rental Platform

<div align="center">

![AgroRent](https://img.shields.io/badge/AgroRent-v2.0-green?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0.0-black?style=for-the-badge&logo=flask)
![WhatsApp](https://img.shields.io/badge/WhatsApp-Bot-25D366?style=for-the-badge&logo=whatsapp)
![Razorpay](https://img.shields.io/badge/Razorpay-Integrated-02042B?style=for-the-badge)
![Gemini](https://img.shields.io/badge/Gemini-AI-4285F4?style=for-the-badge&logo=google)

**India's first AI-powered farm machinery rental marketplace**

*Validated by Scitech Innovation Park (Government Body) — 1st Prize Winner*
*Problem validated through direct farmer interviews across Maharashtra*

[Live Demo](https://agrorent-v3.onrender.com) · [Report Bug](https://github.com/ParthMahadik33/AgroRent-V2/issues) · [Request Feature](https://github.com/ParthMahadik33/AgroRent-V2/issues)

</div>

---

## 📋 Table of Contents

- [About the Project](#-about-the-project)
- [The Problem](#-the-problem)
- [Our Solution](#-our-solution)
- [Validation](#-validation)
- [Features](#-features)
- [WhatsApp Bot](#-whatsapp-bot)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Project Structure](#-project-structure)
- [API Routes](#-api-routes)
- [WhatsApp Bot Commands](#-whatsapp-bot-commands)
- [Payment Flow](#-payment-flow)
- [Deployment](#-deployment)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌱 About the Project

AgroRent is a two-sided marketplace that connects **farmers (renters)** with **equipment owners (lenders)** through a transparent, multilingual, and fully digital platform. Farmers can discover available machinery, verify its condition using AI, and complete the entire rental transaction — including payment — without visiting any physical location.

What makes AgroRent unique is its **WhatsApp-first approach**: a farmer with a basic smartphone can search for equipment, get results in their local language, and book machinery entirely through WhatsApp — no app download required.

---

## 🚨 The Problem

India has **140 million farming households**. Over **86% are small or marginal farmers** who cannot afford to own equipment costing ₹5–50 lakhs. The current farm equipment rental market is:

| Pain Point | Reality |
|---|---|
| **No price transparency** | Farmers pay arbitrary, exploitative rates |
| **Unknown equipment condition** | Damage discovered only after renting |
| **Language barrier** | Most platforms only work in English |
| **No digital access** | Farmers don't use apps, but use WhatsApp |
| **Informal discovery** | Calling 5-10 neighbors, takes 1-2 days |
| **No dispute resolution** | No recourse if cheated |

> *"We interviewed farmers across Maharashtra and found they spend more time finding equipment than actually using it."*

---

## 💡 Our Solution

AgroRent digitizes the entire farm equipment rental lifecycle:

```
Farmer searches on WhatsApp (in their language)
              ↓
AI shows available equipment with condition scores
              ↓
Farmer books and pays via UPI/Razorpay
              ↓
Owner gets WhatsApp notification
              ↓
Owner can cancel within 2 hours (with auto-refund)
              ↓
Booking confirmed — both parties notified
```

---

## 🏆 Validation

AgroRent is not just an idea — it is a **validated solution**:

### 1. Government Validation
> **🥇 1st Prize — Scitech Innovation Park**
> Scitech Innovation Park is a Government of India recognized innovation body. AgroRent was awarded first place, validating both the problem statement and our approach to solving it.

### 2. Farmer Interviews
Direct interviews with farmers across Maharashtra revealed:
- Farmers pay **20-40% above fair market rate** due to no price visibility
- **Equipment condition disputes** are the #1 cause of rental conflicts
- **100%** of interviewed farmers were active WhatsApp users
- **Language barrier** is the primary reason for avoiding digital platforms
- Most rentals arranged via phone calls, taking **1-2 days**

---

## ✨ Features

### 🌐 Web Platform
- **Equipment Listing & Browsing** — Search by category, location, price
- **Multilingual UI** — English, Hindi, Marathi (10+ languages via AI)
- **AI Machinery Condition Check** — Upload photo → Get AI condition score (0-10) with component breakdown
- **Booking System** — Date selection, conflict detection, contract generation
- **Razorpay Payment Integration** — UPI, Cards, Netbanking, Wallets
- **Farmer Dashboard** — Active rentals, booking history, spending analytics
- **Owner Dashboard** — Listed equipment, booking requests, earnings tracker
- **Supply Heatmap** — Visual map showing equipment availability by region
- **Mechanic Directory** — Find certified mechanics for equipment repair
- **Notification System** — Real-time alerts for bookings, approvals, payments

### 🤖 WhatsApp Bot
- **Multilingual AI** — Understands Hindi, Marathi, Punjabi, and 10+ Indian languages
- **Real-time DB Search** — Live equipment listings from database
- **Smart Intent Detection** — Powered by Gemini AI
- **Instant Keyword Shortcuts** — Common queries handled without AI (faster)
- **Crop-to-Equipment Recommendations** — Tell the bot your crop, get equipment suggestions
- **My Bookings** — Check active rentals via WhatsApp
- **Owner Notifications** — Instant WhatsApp alerts for new bookings
- **Booking Cancellation** — Owner can cancel via WhatsApp reply

### 🔒 Security & Trust
- **AI Condition Scores** — Photo-based equipment health verification
- **Owner Ratings** — Post-rental review system
- **2-Hour Cancellation Window** — Owner can cancel with automatic refund
- **Signature Verification** — Razorpay webhook signature validation
- **Secure Auth** — Bcrypt password hashing, session management

---

## 🤖 WhatsApp Bot

The WhatsApp bot is AgroRent's flagship feature — it brings the platform to farmers who don't use apps.

### How It Works

```
Farmer: "mujhe tractor chahiye"  (Hindi)
Bot:    🚜 Available Tractors:
        1. Mahindra Tractor 575
           📍 Mulshi, Pune
           💰 ₹900/day
           👤 Parth Mahadik

Farmer: "1"
Bot:    Full details + owner contact + booking link

Farmer: "wheat"
Bot:    🌱 For wheat, you need:
           • Harvester
           • Thresher
           • Tractor
        Shall I search for Harvester?

Farmer: "yes"
Bot:    [Shows available harvesters]
```

### Language Support

The bot automatically detects and responds in the farmer's language:

| Farmer sends | Bot responds in |
|---|---|
| "tractor chahiye" | Hindi |
| "ट्रॅक्टर हवा आहे" | Marathi |
| "tractor" | English |
| Any Indian language | Same language |

### Performance Optimization

90% of common messages are handled **without calling Gemini AI** (instant response):

| Message Type | Gemini Used? | Response Time |
|---|---|---|
| hi, hello, help | ❌ Static | ⚡ Instant |
| tractor, pump, harvester | ❌ Static | ⚡ Instant |
| 1, 2, 3 (selection) | ❌ Static | ⚡ Instant |
| wheat, rice, sugarcane | ❌ Static | ⚡ Instant |
| "mujhe tractor chahiye" | ✅ Gemini | ~1 sec |
| Complex sentences | ✅ Gemini | ~1 sec |

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend** | Python Flask 3.0 | REST API + WhatsApp webhook |
| **Database** | SQLite (dev) / PostgreSQL (prod) | Equipment, users, bookings |
| **Frontend** | HTML/CSS/JavaScript | Responsive web UI |
| **AI — Condition Check** | Google Gemini 2.0 Flash | Photo → condition score |
| **AI — WhatsApp NLU** | Google Gemini 2.0 Flash | Intent detection, translation |
| **WhatsApp** | Twilio WhatsApp Sandbox | Bot messaging |
| **Payments** | Razorpay | UPI, cards, netbanking |
| **i18n** | Flask-Babel + custom JSON | 10+ Indian languages |
| **PDF Generation** | ReportLab | Rental contracts |
| **Auth** | Werkzeug + Flask Sessions | Secure authentication |
| **CORS** | Flask-CORS | API security |
| **Hosting** | Render | Cloud deployment |
| **Tunnel (dev)** | ngrok | Local WhatsApp testing |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   FARMER / OWNER                     │
│          Web Browser    WhatsApp Phone               │
└──────────────┬─────────────────┬────────────────────┘
               │                 │
               ▼                 ▼
┌──────────────────┐   ┌─────────────────────┐
│   Flask Web App  │   │   Twilio WhatsApp   │
│   (Render Host)  │   │      Sandbox        │
└────────┬─────────┘   └──────────┬──────────┘
         │                        │
         ▼                        ▼
┌─────────────────────────────────────────────┐
│              Flask Backend                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  routes/ │  │   bot/   │  │   ai/    │  │
│  │ auth     │  │ handler  │  │condition │  │
│  │ listings │  │ nlu      │  │ check    │  │
│  │ rentals  │  │ sessions │  │          │  │
│  │ payments │  │notifcns  │  │          │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└────────┬───────────────┬────────────────────┘
         │               │
         ▼               ▼
┌──────────────┐  ┌──────────────────────────┐
│  SQLite DB   │  │     External APIs         │
│  ─────────   │  │  ┌────────────────────┐  │
│  users       │  │  │ Google Gemini API  │  │
│  listings    │  │  ├────────────────────┤  │
│  rentals     │  │  │ Razorpay API       │  │
│  mechanics   │  │  ├────────────────────┤  │
│  notifcns    │  │  │ Twilio API         │  │
└──────────────┘  │  └────────────────────┘  │
                  └──────────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- pip
- Git
- ngrok (for WhatsApp bot local testing)
- Twilio account (free sandbox)
- Google AI Studio account (for Gemini API)
- Razorpay account (test mode)

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/ParthMahadik33/AgroRent-V2.git
cd AgroRent-V2
```

**2. Create virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your actual API keys (see Environment Variables section)
```

**5. Initialize and seed the database**
```bash
python seed.py
```

**6. Run the application**
```bash
python app.py
```

**7. Open in browser**
```
http://localhost:5000
```

---

## 🔐 Environment Variables

Create a `.env` file in the root directory:

```env
# Flask
FLASK_SECRET_KEY=your-random-secret-key-here

# Google Gemini AI
GEMINI_API_KEY=AIzaSy...

# Twilio WhatsApp
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Razorpay Payments
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxx

# App URL (for WhatsApp image sending)
BASE_URL=https://agrorent-v3.onrender.com
```

### Where to get each key:

| Variable | Where to get |
|---|---|
| `FLASK_SECRET_KEY` | Any random string (use `python -c "import secrets; print(secrets.token_hex())"`) |
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com) → Get API Key |
| `TWILIO_ACCOUNT_SID` | [console.twilio.com](https://console.twilio.com) → Account Dashboard |
| `TWILIO_AUTH_TOKEN` | [console.twilio.com](https://console.twilio.com) → Account Dashboard |
| `RAZORPAY_KEY_ID` | [dashboard.razorpay.com](https://dashboard.razorpay.com) → Settings → API Keys |
| `RAZORPAY_KEY_SECRET` | Same as above (shown once on generation) |
| `BASE_URL` | Your Render deployment URL |

---

## 📁 Project Structure

```
AgroRent-V2/
├── app.py                          # App factory — registers blueprints
├── config.py                       # Configuration & env variables
├── database.py                     # DB connection, init_db(), schema
├── seed.py                         # Demo data seeder (auto-skips if data exists)
├── requirements.txt                # Python dependencies
├── .env                            # Secret keys (never commit)
├── .env.example                    # Safe template for .env
├── .gitignore                      # Ignores .env, __pycache__, etc.
│
├── routes/                         # Flask Blueprints
│   ├── __init__.py
│   ├── auth.py                     # Login, signup, logout
│   ├── listings.py                 # Create, browse, search equipment
│   ├── rentals.py                  # Booking creation, rental management
│   ├── dashboard.py                # Farmer + owner dashboards
│   ├── mechanics.py                # Mechanic directory routes
│   ├── notifications.py            # Notification routes
│   ├── payments.py                 # Razorpay order creation + verification
│   └── whatsapp.py                 # WhatsApp webhook endpoint
│
├── bot/                            # WhatsApp Bot
│   ├── __init__.py
│   ├── handler.py                  # Main message router (static + Gemini)
│   ├── nlu.py                      # Gemini intent extraction + translation
│   └── notifications.py            # Twilio message sender (text + images)
│
├── ai/                             # AI Features
│   ├── __init__.py
│   ├── condition_check.py          # Gemini image analysis → condition score
│   └── chatbot.py                  # AI chatbot logic
│
├── i18n/                           # Translations
│   ├── en.json                     # English
│   ├── hi.json                     # Hindi
│   └── mr.json                     # Marathi
│
├── static/
│   ├── css/                        # Stylesheets
│   ├── js/                         # JavaScript (renting.js, dashboard.js)
│   └── uploads/                    # Equipment photos (uploaded by owners)
│
└── templates/                      # Jinja2 HTML templates
    ├── base.html                   # Base layout
    ├── index.html                  # Landing page
    ├── renting.html                # Equipment browse + booking
    ├── rentdashboard.html          # Farmer dashboard
    ├── owner_dashboard.html        # Owner dashboard
    ├── create_listing.html         # Add/edit equipment listing
    └── ...
```

---

## 🔌 API Routes

### Authentication
| Method | Route | Description |
|---|---|---|
| GET/POST | `/login` | User login |
| GET/POST | `/signup` | User registration |
| GET | `/logout` | User logout |

### Listings
| Method | Route | Description |
|---|---|---|
| GET | `/renting` | Browse equipment listings |
| GET | `/api/listings` | Get listings JSON (with filters) |
| POST | `/create_listing` | Create/update equipment listing |
| GET | `/listing/<id>` | View single listing detail |

### Rentals & Payments
| Method | Route | Description |
|---|---|---|
| POST | `/rent_equipment` | Create booking request |
| POST | `/create_order` | Create Razorpay payment order |
| POST | `/payment_success` | Verify payment + activate rental |
| POST | `/cancel_booking/<id>` | Owner cancels + initiates refund |

### AI Features
| Method | Route | Description |
|---|---|---|
| POST | `/analyze_condition` | Upload photo → AI condition score |
| GET | `/api/rentals/<id>/contract-preview` | Generate rental contract |

### WhatsApp
| Method | Route | Description |
|---|---|---|
| POST | `/whatsapp` | Twilio webhook — receives all bot messages |

### Dashboard
| Method | Route | Description |
|---|---|---|
| GET | `/rent_dashboard` | Farmer's booking dashboard |
| GET | `/owner_dashboard` | Owner's equipment + earnings dashboard |
| GET | `/api/notifications/count` | Unread notification count |

---

## 📱 WhatsApp Bot Commands

### For Farmers

| Command | Example | Response |
|---|---|---|
| Greeting | `hi`, `hello`, `नमस्ते` | Welcome menu |
| Search equipment | `tractor`, `pump`, `harvester` | Available listings |
| Hindi search | `mujhe tractor chahiye` | Results in Hindi |
| Marathi search | `ट्रॅक्टर हवा आहे` | Results in Marathi |
| Select listing | `1`, `2`, `3` | Full details + contact |
| Crop recommendation | `wheat`, `rice`, `sugarcane` | Equipment suggestions |
| My bookings | `my bookings` | Active rental list |
| Help | `help`, `menu` | Full command menu |

### For Equipment Owners

| Command | Example | Response |
|---|---|---|
| Cancel booking | `CANCEL 42` | Cancels booking #42 + initiates refund |

---

## 💳 Payment Flow

```
1. Farmer selects equipment + dates on website
            ↓
2. POST /rent_equipment → Creates rental (status: "Pending")
            ↓
3. POST /create_order → Razorpay order created (amount in paise)
            ↓
4. Razorpay Checkout opens (UPI / Card / Netbanking)
            ↓
5. Farmer completes payment
            ↓
6. POST /payment_success → Signature verified → Rental → "Active"
            ↓
7. Owner notified via WhatsApp:
   "🎉 New Booking! ₹2,000 received. CANCEL 42 to reject."
            ↓
8. Owner has 2 hours to cancel (with auto-refund)
            ↓
9. After 2 hours → Auto-confirmed
```

### Test Mode Credentials

For testing payments in development:

```
Netbanking: State Bank of India → Click "Success"
UPI:        success@razorpay (mobile browser only)
```

---

## 🌐 Deployment

### Deploy to Render

**1. Push to GitHub**
```bash
git add .
git commit -m "deploy: production ready"
git push origin main
```

**2. Create Render Web Service**
- Go to [render.com](https://render.com)
- New → Web Service → Connect GitHub repo
- Runtime: Python 3
- Build Command: `pip install -r requirements.txt`
- Start Command: `python app.py`

**3. Add Environment Variables on Render**
Add all variables from `.env` in Render dashboard → Environment

**4. Update Twilio Webhook**
After deploy, update Twilio sandbox webhook:
```
https://agrorent-v3.onrender.com/whatsapp
```

**5. Keep App Warm (Free Tier)**
Add uptime monitor at [uptimerobot.com](https://uptimerobot.com):
- Monitor URL: `https://agrorent-v3.onrender.com`
- Interval: 5 minutes
- Prevents cold starts during demo

### Local WhatsApp Testing (ngrok)

```bash
# Terminal 1 — Flask app
python app.py

# Terminal 2 — ngrok tunnel
ngrok http 5000
# Copy https://xxxx.ngrok-free.app URL

# Update Twilio sandbox webhook to:
# https://xxxx.ngrok-free.app/whatsapp
```

---

## 🗺️ Roadmap

### ✅ Phase 0 — MVP (Complete)
- User authentication (Farmer / Owner roles)
- Equipment listing and browsing
- Booking and rental management
- Farmer and Owner dashboards
- Supply heatmap
- AI machinery condition check
- Multilingual support (Hindi, Marathi, English)
- PDF contract generation
- Mechanic directory

### 🔄 Phase 1 — Bot & Payments (Current)
- WhatsApp AI bot with Gemini NLU
- Razorpay payment integration
- Owner WhatsApp notifications
- 2-hour cancellation with auto-refund
- Full WhatsApp booking + payment flow

### 📋 Phase 2 — Scale (Q3 2026)
- Meta WhatsApp Business API (replace Twilio sandbox)
- Redis session management for bot
- Proactive notifications (reminders, seasonal alerts)
- PostgreSQL migration
- AI rental price suggester

### 🚀 Phase 3 — Expansion (Q4 2026)
- Multi-state rollout (Punjab, UP, Karnataka)
- Rental insurance add-on
- B2B API for agri-input companies
- Credit/BNPL for farmers
- Mobile app (React Native)

### 🌍 Phase 4 — Platform (2027)
- Government scheme integrations (PM Kisan)
- Logistics/delivery network integration
- 22 official Indian language support
- Equipment financing marketplace

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'feat: Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Commit Message Convention
```
feat:     New feature
fix:      Bug fix
docs:     Documentation update
refactor: Code restructuring
test:     Adding tests
```

---

## 📊 Impact Metrics (Targets)

| Metric | Year 1 | Year 3 |
|---|---|---|
| Farmers on platform | 10,000 | 500,000 |
| Equipment owners | 2,000 | 100,000 |
| Transactions | 50,000 | 5,000,000 |
| Avg. savings vs informal market | ₹200/rental | ₹500/rental |
| States covered | 2 | 15+ |
| Languages supported | 3 | 22 |

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 👨‍💻 Team

**Parth Mahadik** — Full Stack Developer & Product Lead
- GitHub: [@ParthMahadik33](https://github.com/ParthMahadik33)

---

## 🙏 Acknowledgements

- [Scitech Innovation Park](https://scitechinnovationpark.in) — Government validation & 1st Prize
- [EFOS SkillUp India Hackathon 2026](https://efos.in) — Open Innovation Track
- Farmers of Maharashtra — For their time and invaluable insights
- [Google Gemini](https://ai.google.dev) — AI backbone
- [Twilio](https://twilio.com) — WhatsApp API
- [Razorpay](https://razorpay.com) — Payment gateway

---

<div align="center">

**🌾 AgroRent — Empowering Indian Farmers Through Technology**

*"A farmer anywhere in India — speaking any language, using any phone — should be able to access the machinery they need, at a fair price, within minutes."*

[![Made with ❤️ for Indian Farmers](https://img.shields.io/badge/Made%20with%20%E2%9D%A4%EF%B8%8F%20for-Indian%20Farmers-orange?style=for-the-badge)](https://agrorent-v3.onrender.com)

</div>
