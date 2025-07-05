# utils/llama_utils.py

import requests
import os
import streamlit as st

def get_fun_fact(animal):
    api_key = st.secrets.get("groq_api_key")
    if not api_key:
        return "Missing Groq API key."

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that gives fun animal facts."},
                    {"role": "user", "content": f"Tell me a fun fact about a {animal}."}
                ]
            }
        )
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Couldn't fetch fun fact: {str(e)}"

def generate_description(animal):
    api_key = st.secrets.get("groq_api_key")
    if not api_key:
        return "Missing Groq API key."

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": "You describe animals in detail for educational purposes."},
                    {"role": "user", "content": f"Write a detailed description of a {animal}, including appearance, behavior, and habitat."}
                ]
            }
        )
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Couldn't fetch description: {str(e)}"
