import streamlit as st

def get_animal_habitat_map(animal_name):
    google_maps_key = st.secrets.get("GOO_TOKEN")

    if not google_maps_key:
        return "<p><strong>Error:</strong> Google Maps API key not found.</p>"

    query = f"habitat+of+{animal_name}"
    html = f"""
    <iframe
        width="100%"
        height="250"
        frameborder="0"
        style="border:0"
        src="https://www.google.com/maps/embed/v1/search?q={query}&key={google_maps_key}"
        allowfullscreen>
    </iframe>
    """
    return html
