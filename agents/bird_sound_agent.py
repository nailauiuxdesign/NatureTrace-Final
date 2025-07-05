from uagents import Agent, Context
from messages import SoundRequest, SoundResponse
import requests

bird_sound_agent = Agent(name="bird_sound_agent", port=8002, seed="bird sound agent")

@bird_sound_agent.on_message(model=SoundRequest)
async def get_bird_sound(ctx: Context, msg: SoundRequest):
    url = f"https://xeno-canto.org/api/2/recordings?query={msg.animal}"
    resp = requests.get(url)
    data = resp.json()
    if data.get("recordings"):
        sound_url = f"https:{data['recordings'][0]['file']}"
        await ctx.send(msg.sender, SoundResponse(url=sound_url))
    else:
        await ctx.send(msg.sender, SoundResponse(url=""))
