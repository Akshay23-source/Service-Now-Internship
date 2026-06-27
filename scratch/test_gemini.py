import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get('GEMINI_API_KEY')
print(f"API Key from environment: {api_key[:5]}...{api_key[-5:] if api_key else ''} (length {len(api_key) if api_key else 0})")

# 1. Try listing models
list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
try:
    r = requests.get(list_url, timeout=10)
    print(f"List Models Status: {r.status_code}")
    models_data = r.json()
    for m in models_data.get('models', []):
        print(f"Available Model: {m['name']}")
except Exception as e:
    print(f"List Models Error: {e}")

# 2. Try generating content with all available models from list response
payload = {
    "contents": [{"parts": [{"text": "Hello, write a one-word greeting."}]}]
}

try:
    r_list = requests.get(list_url, timeout=10)
    models_data = r_list.json()
    for m in models_data.get('models', []):
        model_name = m['name']  # E.g., 'models/gemini-2.5-flash'
        # Skip embedding/image/veo/imagen models as they don't support text generateContent
        if any(keyword in model_name for keyword in ['embedding', 'imagen', 'veo', 'lyria', 'image', 'tts', 'robotics']):
            continue
            
        gen_url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={api_key}"
        try:
            r = requests.post(gen_url, json=payload, timeout=10)
            print(f"Model: {model_name} -> Status: {r.status_code}")
            if r.status_code == 200:
                print(f"SUCCESS with {model_name}! Response: {r.json()}")
                break
            else:
                err_msg = r.json().get('error', {}).get('message', '')[:100]
                print(f"  Error message: {err_msg}")
        except Exception as e:
            print(f"  Error testing {model_name}: {e}")
except Exception as e:
    print(f"Error in testing loop: {e}")


