#!/usr/bin/env python3
"""
Test Azure Computer Vision API with a real image to debug the response format
"""

import requests
import streamlit as st
import sys
import json
from PIL import Image
import io

# Load secrets
st.secrets.load_if_toml_exists()

def test_azure_with_real_image():
    """Test Azure API with a real image"""
    
    endpoint = st.secrets.get("AZURE_COMPUTER_VISION_ENDPOINT")
    key = st.secrets.get("AZURE_COMPUTER_VISION_KEY")
    
    print(f"Endpoint: {endpoint}")
    print(f"Key: {key[:10]}...")
    
    if not endpoint or not key:
        print("❌ Azure credentials not found")
        return
    
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes = img_bytes.getvalue()
    
    # Try different API endpoints
    api_versions = [
        "2023-02-01-preview",
        "2023-04-01-preview", 
        "2022-10-12-preview",
        "4.0"
    ]
    
    endpoints_to_try = [
        "{}/computervision/imageanalysis:analyze?api-version={}",
        "{}/vision/v3.2/analyze",
        "{}/computervision/imageanalysis:analyze?api-version={}&features=caption,objects,tags"
    ]
    
    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Content-Type': 'application/octet-stream'
    }
    
    for endpoint_template in endpoints_to_try:
        if "{}" in endpoint_template and endpoint_template.count("{}") == 2:
            # Has API version
            for version in api_versions:
                test_url = endpoint_template.format(endpoint.rstrip('/'), version)
                print(f"\n🔍 Testing: {test_url}")
                
                try:
                    response = requests.post(test_url, headers=headers, data=img_bytes, timeout=30)
                    print(f"Status Code: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        print("✅ SUCCESS! Response structure:")
                        print(json.dumps(result, indent=2)[:500] + "...")
                        return result
                    else:
                        print(f"❌ Error: {response.text}")
                        
                except Exception as e:
                    print(f"❌ Exception: {e}")
        else:
            # No API version
            test_url = endpoint_template.format(endpoint.rstrip('/'))
            print(f"\n🔍 Testing: {test_url}")
            
            try:
                # Try with different parameters
                params_to_try = [
                    {'visualFeatures': 'Categories,Description,Objects,Tags'},
                    {'features': 'caption,objects,tags'},
                    {}
                ]
                
                for params in params_to_try:
                    print(f"  Params: {params}")
                    response = requests.post(test_url, headers=headers, params=params, data=img_bytes, timeout=30)
                    print(f"  Status Code: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        print("✅ SUCCESS! Response structure:")
                        print(json.dumps(result, indent=2)[:500] + "...")
                        return result
                    else:
                        print(f"  ❌ Error: {response.text[:200]}")
                        
            except Exception as e:
                print(f"❌ Exception: {e}")
    
    print("\n❌ All API endpoints failed")
    return None

if __name__ == "__main__":
    test_azure_with_real_image()
