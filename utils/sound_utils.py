# utils/sound_utils.py
import streamlit as st
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {st.secrets.get('groq_api_key', '')}",
    "Content-Type": "application/json"
}

LLAMA_MODEL = "llama3-8b-8192"

# A very basic mockup text-to-sound approach using descriptions. You can integrate real sound libraries later.
def generate_animal_sound(animal_name):
    prompt = f"Describe what the sound of a {animal_name} would be like. Keep it vivid and short."

    body = {
        "model": LLAMA_MODEL,
        "messages": [
            {"role": "system", "content": "You are a wildlife sound researcher."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.6
    }

    try:
        response = requests.post(GROQ_API_URL, headers=HEADERS, json=body)
        response.raise_for_status()
        data = response.json()
        text_description = data['choices'][0]['message']['content'].strip()
        # Optional: return description only if no real audio synthesis used
        return f"data:audio/mp3;base64,PLACEHOLDER_BASE64"  # You can later hook this to real TTS MP3
    except Exception as e:
        return None
