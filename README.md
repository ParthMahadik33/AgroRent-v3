# 🚜 AgroRent - Agricultural Equipment Rental Platform

AgroRent is a modern, AI-powered platform designed to connect farmers with agricultural equipment owners. By enabling equipment sharing, we make advanced farming technology affordable and accessible to everyone, helping rural communities thrive.

## 🌟 Key Features

### 1. Equipment Rental Marketplace
- **Browse & Book**: Farmers can browse a variety of equipment including tractors, harvesters, pumps, and sprayers.
- **Dynamic Pricing**: Support for hourly, daily, and weekly rental options.
- **Real-time Availability**: Integrated calendar system for booking.

### 2. AI-Powered Assistant (Chatbot)
- **24/7 Support**: A Groq-powered chatbot (Llama 3.1) that answers questions about equipment, pricing, and platform services.
- **Agricultural Intelligence**: Provides advice on equipment selection based on land size and crop type.

### 3. WhatsApp Integration (Smart Bot)
- **Conversational Interface**: Chat with AgroRent directly on WhatsApp.
- **Multilingual NLU**: Understands English, Hindi, and Marathi.
- **Intent Extraction**: Automatically identifies if you want to search for equipment, get crop recommendations, or check your bookings.

### 4. AI Condition Inspector
- **Vision Analysis**: Uses Google Gemini to analyze machinery images and provide a "Condition Score" (0-10) and identify visible issues like rust or damage.

### 5. Secure Payments
- **Razorpay Integration**: Seamless and secure payment processing for rentals.
- **Refund Management**: Automated refund handling for cancellations.

---

## 🛠 Tech Stack

- **Backend**: Python / Flask
- **LLM Engine**: [Groq](https://groq.com/) (Llama 3.1 8B) & [Google Gemini](https://ai.google.dev/)
- **Database**: SQLite (SQLAlchemy)
- **Communications**: Twilio WhatsApp API
- **Payments**: Razorpay
- **Styling**: Vanilla CSS with modern responsive design

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Twilio Account & WhatsApp Sandbox
- Groq API Key
- Razorpay API Keys

### Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd AgroRent
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Setup**:
   Create a `.env` file in the root directory and add your keys:
   ```env
   GROQ_API_KEY=your_groq_key
   GEMINI_API_KEY=your_gemini_key
   RAZORPAY_KEY_ID=your_razorpay_id
   RAZORPAY_KEY_SECRET=your_razorpay_secret
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   ```

4. **Run the app**:
   ```bash
   python app.py
   ```

---

## 📱 How to Use the WhatsApp Feature

The WhatsApp bot is designed to be simple for farmers to use without needing to navigate a website.

### 1. Connect to the Sandbox
- Save the Twilio Sandbox number to your contacts (usually `+1 415 523 8886`).
- Send the message `join <your-sandbox-word>` (found in your Twilio Console) to start the session.

### 2. Basic Commands
You can talk to the bot in natural language (English, Hindi, or Marathi):
- **Search**: Type the name of the machine you need (e.g., *"Tractor"*, *"Pumpset"*, or *"ट्रॅक्टर"*).
- **Recommendations**: Type a crop name to see what equipment you need (e.g., *"Wheat"*, *"Cotton"*, or *"गहू"*).
- **Check Bookings**: Type *"My Bookings"* to see your active rentals.
- **Help**: Type *"Help"* or *"Hi"* to see the main menu.

### 3. Example Flow
1. **User**: "I need a tractor for wheat"
2. **Bot**: "🌱 For **Wheat**, you need: Harvester, Thresher, Tractor. Shall I search for **Harvester**?"
3. **User**: "Yes"
4. **Bot**: (Shows a list of available harvesters with prices and locations).
5. **User**: (Replies with "1" to get the owner's contact details).

---

## 📄 License
This project is for educational and hackathon purposes.
