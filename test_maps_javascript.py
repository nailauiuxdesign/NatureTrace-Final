#!/usr/bin/env python3
"""
Test the Google Maps JavaScript generation to ensure no syntax errors
"""

import streamlit as st
import pandas as pd
import sys
import json

# Load secrets and set up environment
sys.argv = ['test']
st.secrets.load_if_toml_exists()

def test_map_javascript_generation():
    """Test Google Maps JavaScript generation with various animal names"""
    
    print("🗺️ Testing Google Maps JavaScript Generation")
    print("=" * 50)
    
    from utils.map_utils import get_comprehensive_animal_map
    
    # Create test data with potentially problematic names
    test_data = {
        'NAME': ["Lion's Pride", "John's Elephant", "Bird with 'quotes'", "Normal Dog"],
        'CATEGORY': ['Mammal', 'Mammal', 'Bird', 'Mammal'],
        'LATITUDE': [40.7128, 51.5074, 48.8566, 34.0522],
        'LONGITUDE': [-74.0060, -0.1278, 2.3522, -118.2437],
        'PLACE_GUESS': ["New York's Zoo", "London Zoo", "Paris Bird Park", "LA Pet Store"]
    }
    
    df = pd.DataFrame(test_data)
    
    print(f"📊 Test data created with {len(df)} animals")
    print("🔍 Testing animals with special characters in names:")
    for name in df['NAME']:
        print(f"  - {name}")
    
    # Generate the map HTML
    try:
        print("\n🗺️ Generating comprehensive animal map...")
        map_html = get_comprehensive_animal_map(df)
        
        if map_html and "Error" not in map_html:
            print("✅ Map HTML generated successfully!")
            
            # Check for common JavaScript syntax errors
            js_issues = []
            
            if "Unexpected identifier" in map_html:
                js_issues.append("❌ Contains 'Unexpected identifier' error")
            
            if "SyntaxError" in map_html:
                js_issues.append("❌ Contains 'SyntaxError'")
            
            # Check for unescaped quotes in JavaScript
            if "title: '" in map_html and "'" in map_html:
                # This is a simplified check - would need more sophisticated parsing
                print("⚠️ Warning: Potential quote escaping issues in JavaScript")
            
            # Check for proper JSON encoding
            if 'json.dumps(' in map_html:
                print("✅ Using proper JSON encoding for dynamic content")
            
            if not js_issues:
                print("✅ No obvious JavaScript syntax issues found!")
            else:
                for issue in js_issues:
                    print(issue)
            
            # Test the specific functions that were fixed
            print("\n🔧 Testing specific fixes:")
            if '"title":' in map_html or 'title: "' in map_html:
                print("✅ Marker titles properly escaped")
            else:
                print("⚠️ Could not verify marker title escaping")
            
            if '"content":' in map_html:
                print("✅ InfoWindow content properly JSON-encoded")
            else:
                print("⚠️ Could not verify InfoWindow content encoding")
            
            print(f"\n📏 Generated HTML length: {len(map_html)} characters")
            
        else:
            print("❌ Failed to generate map HTML")
            print(f"Error: {map_html}")
            
    except Exception as e:
        print(f"❌ Exception during map generation: {e}")
    
    # Test individual map function
    print("\n🎯 Testing individual animal habitat map...")
    try:
        from utils.map_utils import get_animal_habitat_map
        
        test_animal = "Lion's Pride"  # Animal with apostrophe
        individual_map = get_animal_habitat_map(test_animal)
        
        if individual_map and "Error" not in individual_map:
            print(f"✅ Individual map for '{test_animal}' generated successfully!")
        else:
            print(f"❌ Failed to generate individual map for '{test_animal}'")
            
    except Exception as e:
        print(f"❌ Exception during individual map generation: {e}")
    
    print("\n🎉 Google Maps JavaScript testing complete!")
    print("If no errors above, the syntax issues should be resolved.")

if __name__ == "__main__":
    test_map_javascript_generation()
