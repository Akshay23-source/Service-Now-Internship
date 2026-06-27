import requests
from flask import current_app

class AIService:
    """
    Service layer providing unified access to external LLMs (Google Gemini API).
    Includes exception handling, input validations, and error fallbacks.
    """
    @staticmethod
    def mock_summarize(text):
        """Generates a realistic simulated bullet-point summary from the input text."""
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        bullets = []
        for p in paragraphs[:3]:
            # Take the first sentence of the paragraph
            sentences = [s.strip() for s in p.split('.') if s.strip()]
            if sentences:
                bullets.append(f"- {sentences[0]}.")
        if not bullets:
            bullets = [
                "- Key concept outlined in the note body.",
                "- Analysis of the primary subjects discussed.",
                "- Summary of core learning points and revision goals."
            ]
        return "\n".join(bullets)

    @staticmethod
    def mock_generate_title(text):
        """Generates a creative short title from the first few words of the text."""
        words = [w.strip(',.()"\'-').title() for w in text.split() if w.isalnum()]
        if len(words) >= 3:
            return " ".join(words[:4])
        return "Smart Revision Note"

    @staticmethod
    def mock_generate_quiz(text):
        """Generates a realistic 3-question multiple-choice quiz JSON dynamically."""
        import json
        words = [w.strip(',.()"\'-').lower() for w in text.split() if len(w) > 5]
        keyword = words[0].capitalize() if words else "Concept"
        keyword2 = words[1] if len(words) > 1 else "study"
        
        mock_data = [
            {
                "question": f"What is the primary definition or focus of {keyword}?",
                "options": [
                    f"It is a core {keyword2} used to describe major system activities.",
                    "It is a temporary storage or cache mechanism.",
                    "It is a secondary validation algorithm.",
                    "It is a network routing protocols standard."
                ],
                "correct": 0
            },
            {
                "question": f"Which of the following is most closely associated with {keyword2}?",
                "options": [
                    "A compiler error or exception trace.",
                    "An external integration endpoint.",
                    f"The main implementation detail of {keyword}.",
                    "A database schema migration."
                ],
                "correct": 2
            },
            {
                "question": f"How is {keyword} typically validated or verified?",
                "options": [
                    "By running static analysis check blocks.",
                    f"By evaluating its impact on {keyword2} and metrics.",
                    "By deploying it to a staging sandbox.",
                    "All of the above"
                ],
                "correct": 3
            }
        ]
        return json.dumps(mock_data)

    @staticmethod
    def summarize(text):
        """
        Invokes Google Gemini 1.5 Flash REST endpoint to summarize note text.
        Handles API connection errors and unconfigured keys gracefully.
        """
        # Verify text presence
        text = (text or '').strip()
        if not text:
            return "Error: Note content is empty. Cannot generate a summary."

        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key or api_key.strip() == "" or api_key.startswith('AQ.'):
            from flask import flash
            flash("Notice: Simulated AI response generated locally (no valid GEMINI_API_KEY configured in .env).", "warning")
            return AIService.mock_summarize(text)
        
        # Setup Google Generative AI endpoint URL and headers
        model = current_app.config.get('GEMINI_MODEL', 'gemini-2.0-flash')
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Formulate instruction prompt
        prompt = f"Summarize the following text in a concise, bullet-point list:\n\n{text}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }

        try:
            # Execute HTTP POST request with a 10-second timeout limit
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            # Raise an exception for 4xx/5xx responses
            response.raise_for_status()
            
            res_data = response.json()
            
            # Safely navigate the nested Gemini response structure:
            candidates = res_data.get('candidates', [])
            if candidates:
                content = candidates[0].get('content', {})
                parts = content.get('parts', [])
                if parts:
                    summary_text = parts[0].get('text', '')
                    if summary_text:
                        return summary_text.strip()
            
            return "Error: Empty or unparsable response structure returned from Gemini API."
            
        except requests.exceptions.Timeout:
            from flask import flash
            flash("Notice: Gemini request timed out. Using local simulated AI fallback response.", "warning")
            return AIService.mock_summarize(text)
        except requests.exceptions.RequestException as e:
            from flask import flash
            err_status = response.status_code if ('response' in locals() and response is not None) else str(e)
            flash(f"Notice: Gemini API returned error status {err_status}. Using local simulated AI fallback response.", "warning")
            return AIService.mock_summarize(text)

    @staticmethod
    def generate_title(text):
        """
        Invokes Google Gemini 1.5 Flash REST endpoint to generate a creative short title.
        Handles API connection errors and unconfigured keys gracefully.
        """
        # Verify text presence
        text = (text or '').strip()
        if not text:
            return "Error: Note content is empty. Cannot generate a title."

        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key or api_key.strip() == "" or api_key.startswith('AQ.'):
            from flask import flash
            flash("Notice: Simulated AI response generated locally (no valid GEMINI_API_KEY configured in .env).", "warning")
            return AIService.mock_generate_title(text)

        # Setup Google Generative AI endpoint URL and headers
        model = current_app.config.get('GEMINI_MODEL', 'gemini-2.0-flash')
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Formulate instruction prompt with strict constraints
        prompt = f"Based on the following text content, generate a short, creative note title (maximum 5 words). Do not include quotes, formatting, or surrounding text:\n\n{text}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }

        try:
            # Execute HTTP POST request with a 10-second timeout limit
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            # Raise an exception for 4xx/5xx responses
            response.raise_for_status()
            
            res_data = response.json()
            
            # Safely navigate the nested Gemini response structure
            candidates = res_data.get('candidates', [])
            if candidates:
                content = candidates[0].get('content', {})
                parts = content.get('parts', [])
                if parts:
                    title_text = parts[0].get('text', '')
                    if title_text:
                        # Clean and return the title, removing surrounding quotes if the model added them anyway
                        cleaned_title = title_text.strip().strip('"').strip("'")
                        return cleaned_title
            
            return "Error: Empty or unparsable response structure returned from Gemini API."
            
        except requests.exceptions.Timeout:
            from flask import flash
            flash("Notice: Gemini request timed out. Using local simulated AI fallback response.", "warning")
            return AIService.mock_generate_title(text)
        except requests.exceptions.RequestException as e:
            from flask import flash
            err_status = response.status_code if ('response' in locals() and response is not None) else str(e)
            flash(f"Notice: Gemini API returned error status {err_status}. Using local simulated AI fallback response.", "warning")
            return AIService.mock_generate_title(text)

    @staticmethod
    def generate_quiz(text):
        """
        Invokes Google Gemini 1.5 Flash REST endpoint to generate a multiple choice quiz of 3 questions.
        Validates output is valid JSON list of objects matching the schema.
        Handles API connection errors and unconfigured keys gracefully.
        """
        # Verify text presence
        text = (text or '').strip()
        if not text:
            return "Error: Note content is empty. Cannot generate a quiz."

        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key or api_key.strip() == "" or api_key.startswith('AQ.'):
            from flask import flash
            flash("Notice: Simulated AI response generated locally (no valid GEMINI_API_KEY configured in .env).", "warning")
            return AIService.mock_generate_quiz(text)

        # Setup Google Generative AI endpoint URL and headers
        model = current_app.config.get('GEMINI_MODEL', 'gemini-2.0-flash')
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Formulate instruction prompt with strict constraints
        prompt = (
            f"Based on the following text content, generate a quiz with exactly 3 multiple-choice questions. "
            f"Output your response STRICTLY as a raw JSON array of objects. Do not wrap the output in markdown code blocks (like ```json). "
            f"Each question object must contain these fields: 'question' (string), 'options' (array of 4 strings), and 'correct' (integer, index 0 to 3 representing the correct option).\n\n"
            f"Text content: {text}"
        )
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }

        try:
            # Execute HTTP POST request with a 10-second timeout limit
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            # Raise an exception for 4xx/5xx responses
            response.raise_for_status()
            
            res_data = response.json()
            
            # Safely navigate the nested Gemini response structure
            candidates = res_data.get('candidates', [])
            if candidates:
                content = candidates[0].get('content', {})
                parts = content.get('parts', [])
                if parts:
                    quiz_text = parts[0].get('text', '')
                    if quiz_text:
                        # Clean and return the quiz, verifying it parses as JSON and has the correct format
                        quiz_text_clean = quiz_text.strip()
                        # If wrapped in markdown json block, clean it
                        if quiz_text_clean.startswith("```json"):
                            quiz_text_clean = quiz_text_clean[7:]
                        if quiz_text_clean.endswith("```"):
                            quiz_text_clean = quiz_text_clean[:-3]
                        quiz_text_clean = quiz_text_clean.strip()
                        
                        import json
                        try:
                            data = json.loads(quiz_text_clean)
                            if not isinstance(data, list):
                                return "Error: AI response is not a valid list. Expected a JSON array."
                            if len(data) != 3:
                                return f"Error: AI response did not contain exactly 3 questions. Got {len(data)}."
                            for idx, q in enumerate(data):
                                if not isinstance(q, dict):
                                    return f"Error: Question {idx+1} is not a valid object."
                                if 'question' not in q or not isinstance(q['question'], str):
                                    return f"Error: Question {idx+1} is missing a valid 'question' field."
                                if 'options' not in q or not isinstance(q['options'], list) or len(q['options']) != 4:
                                    return f"Error: Question {idx+1} must contain exactly 4 options."
                                if 'correct' not in q or not isinstance(q['correct'], int) or not (0 <= q['correct'] <= 3):
                                    return f"Error: Question {idx+1} must contain a 'correct' integer option index between 0 and 3."
                            
                            # Re-serialize to guarantee clean, standard JSON storage
                            return json.dumps(data)
                        except json.JSONDecodeError as je:
                            return f"Error: Failed to parse generated quiz JSON ({str(je)}). Raw response: {quiz_text_clean[:200]}"
            
            return "Error: Empty or unparsable response structure returned from Gemini API."
            
        except requests.exceptions.Timeout:
            from flask import flash
            flash("Notice: Gemini request timed out. Using local simulated AI fallback response.", "warning")
            return AIService.mock_generate_quiz(text)
        except requests.exceptions.RequestException as e:
            from flask import flash
            err_status = response.status_code if ('response' in locals() and response is not None) else str(e)
            flash(f"Notice: Gemini API returned error status {err_status}. Using local simulated AI fallback response.", "warning")
            return AIService.mock_generate_quiz(text)
