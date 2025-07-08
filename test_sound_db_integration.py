#!/usr/bin/env python3
"""
Test the new sound database integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_utils import update_animal_sound_url, save_to_snowflake_with_sound

def test_sound_database_integration():
    """Test the new sound database functions"""
    
    print("🧪 Testing Sound Database Integration")
    print("=" * 50)
    
    # Test 1: Update sound for an existing animal
    print("\n1️⃣ Testing sound update for existing animal...")
    result = update_animal_sound_url(animal_name="Wolf")
    print(f"   Result: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
    if result['success']:
        print(f"   Sound URL: {result['sound_url']}")
        print(f"   Source: {result['source']}")
    else:
        print(f"   Error: {result['message']}")
    
    # Test 2: Save new animal with automatic sound fetching
    print("\n2️⃣ Testing new animal save with sound fetching...")
    try:
        save_result = save_to_snowflake_with_sound(
            filename="test_tiger.jpg",
            name="Tiger Test",
            description="Test tiger for sound integration",
            facts="Test facts about tigers",
            category="Mammal",
            fetch_sound=True
        )
        
        print(f"   Save Result: {'✅ SUCCESS' if save_result['success'] else '❌ FAILED'}")
        if save_result['success']:
            print(f"   Animal ID: {save_result['animal_id']}")
            if save_result['sound_result']:
                print(f"   Sound Result: {'✅ SUCCESS' if save_result['sound_result']['success'] else '❌ FAILED'}")
                if save_result['sound_result']['success']:
                    print(f"   Sound URL: {save_result['sound_result']['sound_url']}")
                    print(f"   Sound Source: {save_result['sound_result']['source']}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_sound_database_integration()
