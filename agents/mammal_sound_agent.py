# agents/mammal_sound_agent.py
from uagents import Agent, Context
from messages import SoundRequest, SoundResponse
import requests

mammal_sound_agent = Agent(
    name="mammal_sound_agent",
    port=8003,
    seed="mammal sound agent"
)

@mammal_sound_agent.on_message(model=SoundRequest)
async def get_mammal_sound(ctx: Context, msg: SoundRequest):
    animal = msg.animal.lower().replace(" ", "_")

    # 1. Try Hugging Face-hosted MP3
    base_url = "https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME/resolve/main/assets/sounds/"
    for ext in [".mp3", ".wav"]:
        url = f"{base_url}{animal}{ext}"
        try:
            if requests.head(url).status_code == 200:
                await ctx.send(msg.sender, SoundResponse(url=url))
                return
        except:
            pass

    # 2. Internet Archive fallback
    try:
        query = f"https://archive.org/advancedsearch.php?q={animal}+AND+mediatype%3Aaudio&fl[]=identifier&output=json"
        r = requests.get(query)
        docs = r.json().get("response", {}).get("docs", [])
        if docs:
            identifier = docs[0]["identifier"]
            audio_url = f"https://archive.org/download/{identifier}/{identifier}.mp3"
            await ctx.send(msg.sender, SoundResponse(url=audio_url))
            return
    except:
        pass

    await ctx.send(msg.sender, SoundResponse(url=""))
