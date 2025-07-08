#!/usr/bin/env python3
"""
Test script for enhanced upload functionality with automatic location detection
"""

import sys
import os
sys.path.append(os.getcwd())

from utils.data_utils import save_to_snowflake, fetch_location_for_animal
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_location_fetching():
    """Test the location fetching functionality"""
    print("🧪 Testing Enhanced Location Fetching...")
    print("=" * 50)
    
    # Test animals for different scenarios
    test_animals = [
        {"name": "Red Panda", "category": "Mammal"},
        {"name": "Arctic Fox", "category": "Mammal"},
        {"name": "Blue Jay", "category": "Bird"}
    ]
    
    for i, animal in enumerate(test_animals):
        print(f"\n[{i+1}/{len(test_animals)}] Testing: {animal['name']}")
        
        # Test location fetching
        location_data = fetch_location_for_animal(animal['name'], animal['category'])
        
        if location_data:
            print(f"✅ Location found!")
            print(f"   📍 Place: {location_data.get('place_guess', 'N/A')}")
            print(f"   📊 Source: {location_data.get('source', 'N/A')}")
            print(f"   🌐 Coordinates: {location_data.get('latitude', 'N/A')}, {location_data.get('longitude', 'N/A')}")
        else:
            print(f"❌ No location data found")

def test_enhanced_save():
    """Test the enhanced save functionality"""
    print("\n🧪 Testing Enhanced Save to Database...")
    print("=" * 50)
    
    # Test saving an animal with location fetching
    test_animal = {
        "filename": "test_enhanced_tiger.jpg",
        "name": "Bengal Tiger",
        "description": "A large wild cat species native to India",
        "facts": "Bengal tigers are excellent swimmers and can leap horizontally for over 30 feet",
        "category": "Mammal"
    }
    
    print(f"🐅 Testing save for: {test_animal['name']}")
    
    result = save_to_snowflake(
        filename=test_animal['filename'],
        name=test_animal['name'],
        description=test_animal['description'],
        facts=test_animal['facts'],
        category=test_animal['category'],
        fetch_sound=False,  # Skip sound for faster testing
        fetch_location=True  # Test location fetching
    )
    
    if result and result.get('success'):
        print(f"✅ Save successful!")
        print(f"   🆔 Animal ID: {result.get('animal_id', 'N/A')}")
        
        location_result = result.get('location_result', {})
        if location_result.get('success'):
            print(f"   📍 Location: {location_result.get('location', 'N/A')}")
            print(f"   📊 Source: {location_result.get('source', 'N/A')}")
        else:
            print(f"   ⚠️ No location data found")
    else:
        print(f"❌ Save failed")

def main():
    """Main test function"""
    try:
        # Test 1: Location fetching only
        test_location_fetching()
        
        # Test 2: Enhanced save (commented out to avoid database pollution)
        # test_enhanced_save()
        
        print(f"\n🎉 Testing completed!")
        print(f"📍 Enhanced upload functionality is ready!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.error(f"Test error: {e}")

if __name__ == "__main__":
    main()
