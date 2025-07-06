#!/usr/bin/env python3
"""
Test FreeSound Integration
Test the FreeSound API integration and sound backup functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.freesound_client import freesound_client
from utils.sound_utils import sound_fetcher, test_multiple_sound_sources
import time

def test_freesound_connection():
    """Test basic FreeSound API connection"""
    print("🔗 Testing FreeSound API connection...")
    
    result = freesound_client.test_connection()
    
    if result["success"]:
        print(f"✅ FreeSound API connection successful")
        print(f"   Username: {result.get('username', 'Unknown')}")
        return True
    else:
        print(f"❌ FreeSound API connection failed: {result['error']}")
        return False

def test_freesound_animal_sounds():
    """Test FreeSound animal sound fetching"""
    print("\n🎵 Testing FreeSound animal sound fetching...")
    
    test_animals = [
        "robin",
        "elephant",
        "wolf",
        "dolphin",
        "owl",
        "cat",
        "dog",
        "lion"
    ]
    
    successful = 0
    total = len(test_animals)
    
    for animal in test_animals:
        print(f"\n🔍 Testing: {animal}")
        
        try:
            sound_url = freesound_client.get_best_animal_sound(animal, max_duration=30)
            
            if sound_url:
                print(f"✅ Found sound: {sound_url[:50]}...")
                successful += 1
            else:
                print(f"⚠️ No sound found for {animal}")
                
        except Exception as e:
            print(f"❌ Error testing {animal}: {e}")
    
    print(f"\n📊 FreeSound Test Results:")
    print(f"   Successful: {successful}/{total} ({successful/total*100:.1f}%)")
    
    return successful > 0

def test_sound_system_with_freesound():
    """Test the complete sound system including FreeSound backup"""
    print("\n🔊 Testing complete sound system with FreeSound backup...")
    
    test_animals = [
        {"name": "robin", "type": "bird"},
        {"name": "elephant", "type": "mammal"},
        {"name": "frog", "type": "amphibian"},
        {"name": "cricket", "type": "insect"}
    ]
    
    for animal_info in test_animals:
        animal_name = animal_info["name"]
        animal_type = animal_info["type"]
        
        print(f"\n🧪 Testing complete system for: {animal_name} ({animal_type})")
        
        # Test all sources
        results = test_multiple_sound_sources(animal_name, animal_type)
        
        print(f"   Sources tested: {len(results['sources'])}")
        print(f"   Best source: {results.get('best_source', 'None')}")
        
        if results["best_url"]:
            print(f"   ✅ Sound found: {results['best_url'][:50]}...")
            
            # Check if FreeSound was used
            freesound_result = results["sources"].get("freesound", {})
            if freesound_result.get("valid"):
                print(f"   🎯 FreeSound backup worked!")
            else:
                print(f"   ℹ️ FreeSound result: {freesound_result.get('error', 'No error info')}")
        else:
            print(f"   ❌ No sound found from any source")
        
        time.sleep(1)  # Be respectful to APIs

def test_sound_backup_scenario():
    """Test FreeSound as backup when primary sources fail"""
    print("\n🔄 Testing FreeSound as backup source...")
    
    # Test with animals that might not be in primary sources
    backup_test_animals = [
        "domestic cat",
        "house sparrow", 
        "american robin",
        "grey wolf",
        "bottlenose dolphin"
    ]
    
    for animal in backup_test_animals:
        print(f"\n🔍 Testing backup scenario: {animal}")
        
        # Try to get sound from complete system
        sound_url = sound_fetcher.fetch_sound(animal, max_duration=30, animal_type="unknown")
        
        if sound_url:
            print(f"✅ Sound found (some source): {sound_url[:50]}...")
            
            # Check specifically if FreeSound found something
            freesound_url = freesound_client.get_best_animal_sound(animal, max_duration=30)
            if freesound_url:
                print(f"   🎯 FreeSound also has this animal")
            else:
                print(f"   ℹ️ FreeSound doesn't have this animal")
        else:
            print(f"❌ No sound found from any source")

def run_freesound_tests():
    """Run all FreeSound integration tests"""
    print("🧪 FreeSound Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("FreeSound API Connection", test_freesound_connection),
        ("FreeSound Animal Sounds", test_freesound_animal_sounds),
        ("Complete Sound System", test_sound_system_with_freesound),
        ("Backup Source Scenario", test_sound_backup_scenario),
    ]
    
    results = {}
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔬 Running: {test_name}")
        print("-" * 40)
        
        try:
            result = test_func()
            results[test_name] = result
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Test error: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n📋 FreeSound Test Summary")
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total*100):.1f}%")
    
    print(f"\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    if passed == total:
        print(f"\n🎉 All FreeSound tests passed! Your backup sound system is ready.")
    elif passed > 0:
        print(f"\n⚠️ Some tests passed. FreeSound backup is partially working.")
    else:
        print(f"\n❌ FreeSound tests failed. Check your API key and connection.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_freesound_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected test error: {e}")
        exit(1)
