#!/usr/bin/env python3
"""
Test iNaturalist sound fetching directly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.sound_utils import sound_fetcher

def test_inaturalist_sounds():
    """Test iNaturalist sound fetching directly"""
    
    # Test animals that might have sounds on iNaturalist
    test_animals = [
        "Canis lupus",  # Gray Wolf - scientific name
        "Wolf",         # Common name
        "Orcinus orca", # Orca - scientific name
        "Bubo bubo",    # Eagle Owl - scientific name
        "Owl",          # Common name
        "Rana temporaria" # Common Frog - scientific name
    ]
    
    print("🔊 Testing iNaturalist Sound Fetching")
    print("=" * 60)
    
    for animal in test_animals:
        print(f"\n🔍 Testing: {animal}")
        try:
            sound_url = sound_fetcher._query_inaturalist(animal, 30)
            if sound_url:
                print(f"   ✅ Found: {sound_url}")
            else:
                print(f"   ❌ No sound found")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_inaturalist_sounds()
