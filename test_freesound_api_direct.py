#!/usr/bin/env python3
"""
Direct test of FreeSound API key to verify authentication
"""

import requests
import json
import os

def test_freesound_api():
    """Test the FreeSound API key directly"""
    
    # API key from environment variables
    api_key = os.getenv('FREESOUND_API_KEY', 'YOUR_API_KEY_HERE')
    base_url = 'https://freesound.org/apiv2'
    
    headers = {
        'Authorization': f'Token {api_key}',
        'User-Agent': 'NatureTrace/1.0 (Educational Research)'
    }
    
    print('🔑 Testing FreeSound API Key Directly')
    print('=' * 50)
    print(f'API Key: {api_key[:20]}...{api_key[-10:]}')
    print(f'Base URL: {base_url}')
    print()
    
    try:
        # Test the /me/ endpoint to verify authentication
        print('📡 Testing authentication with /me/ endpoint...')
        response = requests.get(f'{base_url}/me/', headers=headers, timeout=10)
        print(f'Status Code: {response.status_code}')
        
        if response.status_code == 200:
            user_data = response.json()
            print(f'✅ API Key Valid! Username: {user_data.get("username", "Unknown")}')
            print(f'   User ID: {user_data.get("id", "Unknown")}')
            return True
            
        elif response.status_code == 401:
            print('❌ API Key Invalid (401 Unauthorized)')
            print(f'Response: {response.text[:200]}')
            return False
            
        else:
            print(f'⚠️ Unexpected response: {response.status_code}')
            print(f'Response: {response.text[:200]}')
            return False
            
    except requests.exceptions.RequestException as e:
        print(f'❌ Connection Error: {str(e)}')
        return False
    
    except Exception as e:
        print(f'❌ Unexpected Error: {str(e)}')
        return False

def test_search_functionality():
    """Test basic search functionality if authentication works"""
    
    api_key = os.getenv('FREESOUND_API_KEY', 'YOUR_API_KEY_HERE')
    base_url = 'https://freesound.org/apiv2'
    
    headers = {
        'Authorization': f'Token {api_key}',
        'User-Agent': 'NatureTrace/1.0 (Educational Research)'
    }
    
    print('\n🔍 Testing search functionality...')
    
    try:
        # Test a simple search
        search_params = {
            'query': 'wolf howl',
            'filter': 'duration:[1.0 TO 10.0]',
            'fields': 'id,name,url,download,previews,duration,avg_rating',
            'page_size': 5
        }
        
        response = requests.get(f'{base_url}/search/text/', 
                              headers=headers, 
                              params=search_params, 
                              timeout=15)
        
        print(f'Search Status Code: {response.status_code}')
        
        if response.status_code == 200:
            search_data = response.json()
            count = search_data.get('count', 0)
            results = search_data.get('results', [])
            
            print(f'✅ Search successful! Found {count} results')
            if results:
                first_result = results[0]
                print(f'   First result: {first_result.get("name", "Unknown")}')
                print(f'   Duration: {first_result.get("duration", "Unknown")}s')
                print(f'   Rating: {first_result.get("avg_rating", "N/A")}')
            return True
            
        else:
            print(f'❌ Search failed: {response.status_code}')
            print(f'Response: {response.text[:200]}')
            return False
            
    except Exception as e:
        print(f'❌ Search Error: {str(e)}')
        return False

if __name__ == "__main__":
    print("🎵 FreeSound API Direct Test")
    print("=" * 60)
    
    # Test authentication
    auth_success = test_freesound_api()
    
    # If auth works, test search
    if auth_success:
        test_search_functionality()
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
