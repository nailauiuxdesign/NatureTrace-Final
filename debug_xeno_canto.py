#!/usr/bin/env python3
"""
Debug Xeno-Canto API directly
"""

import requests
import json

def test_xeno_canto_directly():
    """Test Xeno-Canto API directly"""
    
    animal_name = "Bald Eagle"
    clean_name = animal_name.replace(" ", "+")
    url = f"https://xeno-canto.org/api/2/recordings?query={clean_name}"
    
    print(f"🔍 Testing Xeno-Canto directly for: {animal_name}")
    print(f"URL: {url}")
    print("=" * 80)
    
    try:
        response = requests.get(url, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            recordings = data.get('recordings', [])
            print(f"Number of recordings found: {len(recordings)}")
            
            if recordings:
                print("\nFirst 3 recordings:")
                for i, recording in enumerate(recordings[:3]):
                    print(f"\n{i+1}. {recording.get('en', 'Unknown')}")
                    print(f"   Quality: {recording.get('q', 'N/A')}")
                    print(f"   Length: {recording.get('length', 'N/A')} seconds")
                    print(f"   Type: {recording.get('type', 'N/A')}")
                    print(f"   File: {recording.get('file', 'N/A')}")
            else:
                print("No recordings found")
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_xeno_canto_directly()
