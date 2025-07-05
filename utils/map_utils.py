# utils/map_utils.py

def get_animal_habitat_map(animal_name):
    html = f"""
    <iframe
        width="100%"
        height="250"
        frameborder="0"
        style="border:0"
        src="https://www.google.com/maps/embed/v1/search?q=habitat+of+{animal_name}&key=YOUR_GOOGLE_MAPS_API_KEY"
        allowfullscreen>
    </iframe>
    """
    return html
