# Testing AgroRent Chatbot Locally

## Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

## Step 1: Install Dependencies

Open a terminal/command prompt in your project directory and run:

```bash
pip install -r requirements.txt
```

Or if you're using a virtual environment (recommended):

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
venv\Scripts\activate.bat
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Set API Key (Optional)

The API key is already hardcoded in `app.py`, so it should work out of the box. However, if you want to use an environment variable instead:

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="AIzaSyDHpTcJAYkrxQWh6bY0kvhYzuhsQDUCtf4"
```

**Windows (CMD):**
```cmd
set GEMINI_API_KEY=AIzaSyDHpTcJAYkrxQWh6bY0kvhYzuhsQDUCtf4
```

**Linux/Mac:**
```bash
export GEMINI_API_KEY="AIzaSyDHpTcJAYkrxQWh6bY0kvhYzuhsQDUCtf4"
```

## Step 3: Run the Application

```bash
python app.py
```

You should see output like:
```
 * Running on http://0.0.0.0:5000
 * Running on http://127.0.0.1:5000
```

## Step 4: Test the Chatbot

1. Open your browser and go to: **http://localhost:5000** or **http://127.0.0.1:5000**

2. Look for the chatbot button in the bottom-right corner (green chat icon)

3. Click the chatbot button to open it

4. Try asking questions like:
   - "What equipment can I rent?"
   - "How do I book equipment?"
   - "Show me the renting page"
   - "I have 5 acres of land, what equipment should I rent?"

5. Test clickable links:
   - Ask: "Show me the renting page" or "Where can I see listings?"
   - The chatbot should respond with clickable links

## Troubleshooting

### Port Already in Use
If port 5000 is already in use, you can change it in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change 5000 to 5001
```

### API Key Error
If you see an API key error:
- Make sure the API key in `app.py` is correct
- Or set the `GEMINI_API_KEY` environment variable

### Dependencies Not Found
If you get import errors:
```bash
pip install --upgrade -r requirements.txt
```

### Chatbot Not Appearing
- Check browser console for JavaScript errors (F12)
- Make sure `static/js/chatbot.js` is loading
- Check that `static/css/chatbot.css` is loading

## Testing Chatbot Features

### Test Link Detection
Try these messages to test clickable links:
- "Show me the renting page"
- "Where can I find listings?"
- "What's the market overview page?"
- "I need to see mechanics"

The chatbot should respond with URLs that become clickable links.

### Test Markdown Links
The chatbot can also use markdown format. If the AI responds with `[link text](url)`, it should also become clickable.

## Stopping the Server

Press `Ctrl + C` in the terminal to stop the Flask server.

