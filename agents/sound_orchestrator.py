# agents/sound_orchestrator.py
from uagents import Agent, Context
from messages import SoundRequest, SoundResponse

orchestrator = Agent(
    name="sound_orchestrator",
    port=8001,
    seed="orchestrator seed",
    endpoint=["http://127.0.0.1:8001/submit"]
)

@orchestrator.on_message(model=SoundRequest)
async def route_sound_request(ctx: Context, msg: SoundRequest):
    if msg.type == "bird":
        await ctx.send("bird_sound_agent", msg)
    elif msg.type == "mammal":
        await ctx.send("mammal_sound_agent", msg)
    else:
        await ctx.send("fallback_sound_agent", msg)
