# utils/sound_utils.py

import requests

def generate_animal_sound(animal_name: str) -> str:
    """
    Attempt to fetch a valid sound file URL from multiple sources for a given animal name.
    Order of preference:
    1. Hugging Face Assets
    2. Xeno-Canto (Birds)
    3. Internet Archive
    """

    animal_name_clean = animal_name.lower().strip().replace(" ", "_")
    encoded_name = requests.utils.quote(animal_name)

    # 1. Hugging Face local hosted file
    hf_base = "https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME/resolve/main/assets/sounds/"
    for ext in [".mp3", ".wav"]:
        hf_url = f"{hf_base}{animal_name_clean}{ext}"
        try:
            r = requests.head(hf_url)
            if r.status_code == 200:
                return hf_url
        except:
            pass

    # 2. Xeno-Canto (for birds)
    try:
        xc_resp = requests.get(f"https://xeno-canto.org/api/2/recordings?query={encoded_name}")
        if xc_resp.ok:
            data = xc_resp.json()
            if data.get("recordings"):
                return f"https:{data['recordings'][0]['file']}"
    except:
        pass

    # 3. Internet Archive (wild fallback)
    try:
        ia_url = f"https://archive.org/advancedsearch.php?q={encoded_name}+AND+mediatype%3Aaudio&fl[]=identifier&output=json"
        ia_resp = requests.get(ia_url)
        if ia_resp.ok:
            docs = ia_resp.json().get(\"response\", {}).get(\"docs\", [])
            if docs:
                identifier = docs[0][\"identifier\"]
                return f\"https://archive.org/download/{identifier}/{identifier}.mp3\"
    except:
        pass

    # No sound found
    return \"\"
