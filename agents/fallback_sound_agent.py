# agents/fallback_sound_agent.py
from uagents import Agent, Context
from messages import SoundRequest, SoundResponse
import requests
import os

fallback_sound_agent = Agent(
    name="fallback_sound_agent",
    port=8004,
    seed="fallback sound agent"
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

@fallback_sound_agent.on_message(model=SoundRequest)
async def fallback_tts(ctx: Context, msg: SoundRequest):
    if not GROQ_API_KEY:
        await ctx.send(msg.sender, SoundResponse(url=""))
        return

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that creates short educational animal sound facts."},
                    {"role": "user", "content": f"Generate a fun fact about the sound of a {msg.animal} in one sentence."}
                ]
            }
        )
        result = response.json()
        fact = result["choices"][0]["message"]["content"]

        # OPTIONAL: Use TTS API to convert fact to audio and return .mp3 URL
        # For now, we'll just simulate a silent audio file link or fact placeholder
        await ctx.send(msg.sender, SoundResponse(url="https://example.com/placeholder.mp3"))

    except Exception as e:
        await ctx.send(msg.sender, SoundResponse(url=""))
