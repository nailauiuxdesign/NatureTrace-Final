from uagents import Model

class SoundRequest(Model):
    animal: str
    type: str  # 'bird', 'mammal', 'unknown'
    sender: str

class SoundResponse(Model):
    url: str
