import streamlit as st

def get_animal_habitat_map(animal_name):
    google_maps_key = st.secrets.get("google_maps_key")

    if not google_maps_key:
        return "<p><strong>Error:</strong> Google Maps API key not found. Please check your secrets.toml file.</p>"

    # Clean the animal name for URL
    query = f"habitat+of+{animal_name.replace(' ', '+')}"
    
    html = f"""
    <iframe
        width="100%"
        height="400"
        frameborder="0"
        style="border:0"
        src="https://www.google.com/maps/embed/v1/search?q={query}&key={google_maps_key}"
        allowfullscreen>
    </iframe>
    """
    return html

def get_animal_habitat_map_enhanced(animal_name, map_type="search"):
    """
    Enhanced Google Maps function with multiple map types and better habitat queries
    
    Args:
        animal_name: Name of the animal
        map_type: Type of map - 'search', 'place', or 'streetview'
    """
    google_maps_key = st.secrets.get("google_maps_key")

    if not google_maps_key:
        return "<p><strong>Error:</strong> Google Maps API key not found. Please check your secrets.toml file.</p>"

    # Create habitat-specific queries
    habitat_queries = {
        "search": f"{animal_name}+habitat+ecosystem+natural+environment",
        "conservation": f"{animal_name}+conservation+area+national+park+wildlife+reserve",
        "distribution": f"{animal_name}+range+distribution+native+habitat"
    }
    
    query = habitat_queries.get("search", f"habitat+of+{animal_name.replace(' ', '+')}")
    
    if map_type == "search":
        embed_url = f"https://www.google.com/maps/embed/v1/search?q={query}&key={google_maps_key}"
    elif map_type == "place":
        embed_url = f"https://www.google.com/maps/embed/v1/place?q={query}&key={google_maps_key}"
    else:
        embed_url = f"https://www.google.com/maps/embed/v1/search?q={query}&key={google_maps_key}"
    
    html = f"""
    <div style="border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
        <iframe
            width="100%"
            height="450"
            frameborder="0"
            style="border:0"
            src="{embed_url}"
            allowfullscreen>
        </iframe>
    </div>
    <p style="text-align: center; margin-top: 10px; color: #666; font-size: 0.9em;">
        🗺️ Showing habitat and conservation areas for <strong>{animal_name}</strong>
    </p>
    """
    return html

def get_interactive_map_with_controls(animal_name):
    """
    Interactive map with multiple view options
    """
    google_maps_key = st.secrets.get("google_maps_key")

    if not google_maps_key:
        return "<p><strong>Error:</strong> Google Maps API key not found. Please check your secrets.toml file.</p>"

    # Multiple search queries for comprehensive results
    queries = [
        f"{animal_name}+habitat+ecosystem",
        f"{animal_name}+national+park+wildlife",
        f"{animal_name}+conservation+area",
        f"{animal_name}+natural+environment"
    ]
    
    html = f"""
    <div style="border-radius: 15px; overflow: hidden; box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; text-align: center;">
            <h3 style="margin: 0; font-size: 1.2em;">🌍 {animal_name} Habitat Map</h3>
            <p style="margin: 5px 0 0 0; font-size: 0.9em; opacity: 0.9;">Explore natural habitats and conservation areas</p>
        </div>
        <iframe
            width="100%"
            height="500"
            frameborder="0"
            style="border:0"
            src="https://www.google.com/maps/embed/v1/search?q={queries[0].replace(' ', '+')}&key={google_maps_key}&zoom=6"
            allowfullscreen>
        </iframe>
        <div style="background: #f8f9fa; padding: 10px; text-align: center; border-top: 1px solid #e9ecef;">
            <small style="color: #6c757d;">🔍 Search includes habitats, national parks, and conservation areas</small>
        </div>
    </div>
    """
    return html
