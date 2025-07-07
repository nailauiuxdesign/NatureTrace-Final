#!/usr/bin/env python3
"""
Test Azure Computer Vision with a real animal image
"""

import streamlit as st
import sys
import requests
import io

# Load secrets
sys.argv = ['test']
st.secrets.load_if_toml_exists()

def test_azure_with_animal_image():
    """Test Azure with a real animal image"""
    
    print("🐕 Testing Azure Computer Vision with Real Animal Image")
    print("=" * 60)
    
    from utils.azure_vision import get_azure_image_analysis
    
    # Use a different image source that allows downloads
    image_url = "https://images.unsplash.com/photo-1552053831-71594a27632d?w=400"
    
    try:
        print(f"📥 Downloading test image: {image_url}")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(image_url, timeout=10, headers=headers)
        if response.status_code == 200:
            image_data = io.BytesIO(response.content)
            print("✅ Image downloaded successfully")
            
            # Test Azure analysis
            print("\n🔍 Analyzing with Azure Computer Vision...")
            azure_result = get_azure_image_analysis(image_data)
            
            if azure_result.get('success'):
                print("✅ Azure Computer Vision Analysis Results:")
                print(f"📊 Total animals detected: {len(azure_result.get('animals', []))}")
                print(f"🏷️ Categories found: {len(azure_result.get('categories', []))}")
                print(f"🎯 Max confidence: {azure_result.get('confidence', 0):.2%}")
                
                # Show detected animals
                animals = azure_result.get('animals', [])
                if animals:
                    print("\n🐾 Animals Detected:")
                    for i, animal in enumerate(animals):
                        print(f"  {i+1}. {animal['name']} (confidence: {animal['confidence']:.2%}, source: {animal['source']})")
                
                # Show categories
                categories = azure_result.get('categories', [])
                if categories:
                    print("\n📂 Categories:")
                    for cat in categories[:5]:  # Top 5
                        print(f"  - {cat['name']} (confidence: {cat['confidence']:.2%})")
                
                # Show all tags
                all_tags = azure_result.get('all_tags', [])
                if all_tags:
                    print("\n🏷️ All Tags (Top 10):")
                    for tag in all_tags[:10]:
                        print(f"  - {tag['name']} (confidence: {tag['confidence']:.2%})")
                
                print(f"\n🎉 Azure Computer Vision is working perfectly!")
                print(f"   The API successfully analyzed the animal image")
                print(f"   and provided {len(animals)} animal detection(s)")
                
            else:
                print(f"❌ Azure Error: {azure_result.get('error')}")
                
        else:
            print(f"❌ Failed to download image: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_azure_with_animal_image()
