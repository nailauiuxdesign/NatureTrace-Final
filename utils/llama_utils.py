# utils/llama_utils.py
import streamlit as st
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {st.secrets.get('groq_api_key', '')}",
    "Content-Type": "application/json"
}

# Use LLaMA model via Groq (llama3-8b or llama3-70b)
LLAMA_MODEL = "llama3-70b-8192"

def generate_animal_facts(animal_name):
    prompt = (
        f"Give me an interesting educational fact about a {animal_name}. "
        "Make it child-friendly, curious, and one or two sentences max."
    )

    body = {
        "model": LLAMA_MODEL,
        "messages": [
            {"role": "system", "content": "You are a fun and educational zoologist."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(GROQ_API_URL, headers=HEADERS, json=body)
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Couldn't fetch fun fact: {str(e)}"
