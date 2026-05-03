import json
import os
import re
from flask import jsonify
from google import genai
from google.genai import types
from config import GEMINI_API_KEY
from database import get_db

_client = None


def _get_client():
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is missing. Check your .env file.")
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client

ANALYSIS_PROMPT = """You are an AI machinery condition inspector. Analyze the machine shown in the image.

Tasks:
1. Identify all visible issues such as rust, dents, scratches, broken parts, worn tires, paint fade, leaks, or structural damage.
2. Based on your analysis, generate a "Condition Score" from 0 to 10:
   - 9–10: Excellent condition, almost no damage
   - 7–8: Good condition, minor cosmetic issues
   - 5–6: Moderate condition, noticeable wear or rust
   - 3–4: Poor condition, obvious damage, maintenance needed
   - 0–2: Very bad condition, unsafe or unusable
3. Provide a detailed explanation of why you gave that score.
4. Keep output in structured JSON format:

{
  "condition_score": <number>,
  "issues_found": [list of problems - keep each very short, max 5 items],
  "summary": "Short explanation of condition (one sentence)",
  "recommendation": "What the renter should know (one sentence)"
}

Analyze only what is visible in the image. Keep issues_found list items very brief (3-5 words each)."""

def analyze_machine_condition(listing_id):
    """Analyze machine condition from listing image"""
    try:
        conn = get_db()
        listing = conn.execute('SELECT * FROM listings WHERE id = ?', (listing_id,)).fetchone()
        conn.close()
        
        if not listing:
            return jsonify({'error': 'Listing not found'}), 404
        
        if not listing['main_image']:
            return jsonify({'error': 'No image available for analysis'}), 400
        
        # Read image from file system
        image_path = os.path.join('static', listing['main_image'])
        if not os.path.exists(image_path):
            return jsonify({'error': 'Image file not found'}), 404
        
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        # Determine MIME type from file extension
        file_ext = os.path.splitext(image_path)[1].lower()
        mime_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        mime_type = mime_type_map.get(file_ext, 'image/jpeg')
        
        # Create image part for Gemini
        image = types.Part.from_bytes(
            data=image_bytes,
            mime_type=mime_type
        )
        
        # Generate content with Gemini
        response = _get_client().models.generate_content(
            model="gemini-2.5-flash",
            contents=[ANALYSIS_PROMPT, image],
        )
        
        # Parse the response
        response_text = response.text
        
        # Try to extract JSON from the response
        # Gemini might wrap JSON in markdown code blocks
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            json_str = json_match.group(0)
            try:
                result = json.loads(json_str)
                # Ensure all required fields exist
                if 'condition_score' not in result:
                    result['condition_score'] = None
                if 'issues_found' not in result:
                    result['issues_found'] = []
                if 'summary' not in result:
                    result['summary'] = response_text[:100] if response_text else 'Analysis completed'
                if 'recommendation' not in result:
                    result['recommendation'] = 'Review the equipment before renting'
                
                return jsonify(result)
            except json.JSONDecodeError:
                # If JSON parsing fails, return structured response with raw text
                return jsonify({
                    'condition_score': None,
                    'issues_found': [],
                    'summary': response_text[:150] if len(response_text) > 150 else response_text,
                    'recommendation': 'Could not parse structured response. Please review the equipment manually.',
                    'raw_response': response_text
                })
        else:
            # If no JSON found, return structured response
            return jsonify({
                'condition_score': None,
                'issues_found': [],
                'summary': response_text[:150] if len(response_text) > 150 else response_text,
                'recommendation': 'Could not parse structured response. Please review the equipment manually.',
                'raw_response': response_text
            })
            
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500
