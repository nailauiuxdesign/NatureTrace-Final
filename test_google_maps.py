# test_google_maps.py
import streamlit as st
from utils.map_utils import get_animal_habitat_map, get_interactive_map_with_controls

def test_google_maps():
    """Test Google Maps integration"""
    st.title("🗺️ Google Maps API Test")
    
    # Check if API key exists
    api_key = st.secrets.get("google_maps_key")
    if api_key:
        st.success(f"✅ Google Maps API key found: {api_key[:10]}...")
        
        # Test with a sample animal
        test_animal = "African Lion"
        st.subheader(f"Testing with: {test_animal}")
        
        # Test basic map
        st.write("**Basic Map:**")
        basic_map = get_animal_habitat_map(test_animal)
        st.components.v1.html(basic_map, height=400)
        
        # Test enhanced map
        st.write("**Enhanced Interactive Map:**")
        enhanced_map = get_interactive_map_with_controls(test_animal)
        st.components.v1.html(enhanced_map, height=650)
        
    else:
        st.error("❌ Google Maps API key not found in secrets!")
        st.write("Please check your .streamlit/secrets.toml file")

if __name__ == "__main__":
    test_google_maps()
