#!/usr/bin/env python3
"""
Test Google Maps functionality after fixing the maptype parameter issue
"""

import streamlit as st
from utils.map_utils import get_animal_habitat_map, get_animal_habitat_map_enhanced, get_interactive_map_with_controls

def test_google_maps():
    st.title("🗺️ Google Maps API Test")
    st.markdown("Testing Google Maps functionality after fixing the maptype parameter issue.")
    
    # Test animal
    test_animal = "African Lion"
    
    st.subheader("1. Basic Map Function")
    try:
        basic_map = get_animal_habitat_map(test_animal)
        st.components.v1.html(basic_map, height=450)
        st.success("✅ Basic map function working!")
    except Exception as e:
        st.error(f"❌ Basic map failed: {e}")
    
    st.subheader("2. Enhanced Map Function")
    try:
        enhanced_map = get_animal_habitat_map_enhanced(test_animal)
        st.components.v1.html(enhanced_map, height=500)
        st.success("✅ Enhanced map function working!")
    except Exception as e:
        st.error(f"❌ Enhanced map failed: {e}")
    
    st.subheader("3. Interactive Map with Controls")
    try:
        interactive_map = get_interactive_map_with_controls(test_animal)
        st.components.v1.html(interactive_map, height=550)
        st.success("✅ Interactive map function working!")
    except Exception as e:
        st.error(f"❌ Interactive map failed: {e}")
    
    st.subheader("4. API Key Validation")
    google_maps_key = st.secrets.get("google_maps_key")
    if google_maps_key:
        st.success(f"✅ Google Maps API key found: {google_maps_key[:10]}...")
        st.info("🔗 Maps should now load without 'Invalid maptype parameter' errors")
    else:
        st.error("❌ Google Maps API key not found in secrets")

if __name__ == "__main__":
    test_google_maps()
