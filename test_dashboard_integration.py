#!/usr/bin/env python3
"""
Test Dashboard Sound Integration
Comprehensive test of the dashboard sound management system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dashboard_sound_integration import dashboard_sound_manager
from utils.data_utils import get_snowflake_connection
import time

def test_database_connection():
    """Test basic database connectivity"""
    print("🔗 Testing database connection...")
    conn = get_snowflake_connection()
    if conn:
        print("✅ Database connection successful")
        conn.close()
        return True
    else:
        print("❌ Database connection failed")
        return False

def test_sound_status():
    """Test getting dashboard sound status"""
    print("Testing sound status retrieval...")
    status = dashboard_sound_manager.get_dashboard_sound_status()
    
    if "error" in status:
        print(f"❌ Error getting status: {status['error']}")
        return False
    
    print("✅ Sound status retrieved successfully")
    print(f"   Total animals: {status['total_animals']}")
    print(f"   With sounds: {status['animals_with_sound']}")
    print(f"   Coverage: {status['sound_coverage_percentage']}%")
    
    if status['sources_breakdown']:
        print(f"   Sources: {list(status['sources_breakdown'].keys())}")
    
    return True

def test_animals_without_sounds():
    """Test getting animals without sounds"""
    print("Testing animals without sounds retrieval...")
    animals = dashboard_sound_manager.get_animals_without_sounds(limit=5)
    
    if animals:
        print(f"✅ Found {len(animals)} animals without sounds")
        for animal in animals[:3]:
            print(f"   - {animal['name']} (ID: {animal['id']})")
    else:
        print("✅ No animals without sounds found (or all have sounds)")
    
    return True

def test_single_animal_update():
    """Test updating sound for a single animal"""
    print("Testing single animal sound update...")
    
    # Get an animal without sound first
    animals = dashboard_sound_manager.get_animals_without_sounds(limit=1)
    
    if not animals:
        print("ℹ️ No animals without sounds to test with")
        return True
    
    test_animal = animals[0]
    print(f"Testing with: {test_animal['name']} (ID: {test_animal['id']})")
    
    # Try to update the sound
    result = dashboard_sound_manager.update_existing_animal_sound(test_animal['id'])
    
    if result['success']:
        print(f"✅ Successfully updated sound for {test_animal['name']}")
        print(f"   Source: {result['source']}")
        print(f"   URL: {result['sound_url'][:50]}...")
    else:
        print(f"⚠️ Could not find sound for {test_animal['name']}: {result['message']}")
    
    return True

def test_add_new_animal():
    """Test adding a new animal with automatic sound fetching"""
    print("➕ Testing new animal addition with sound...")
    
    # Use a test animal that should have sounds available
    test_name = f"test_robin_{int(time.time())}"
    
    result = dashboard_sound_manager.add_animal_with_sound(
        filename=f"{test_name}.jpg",
        name="Robin",
        description="A small bird with a red breast",
        facts="Robins are known for their melodic song",
        category="Bird",
        auto_fetch_sound=True
    )
    
    if result['success']:
        print(f"✅ Successfully added test animal (ID: {result['animal_id']})")
        if result['sound_result'] and result['sound_result']['success']:
            print(f"   Sound found: {result['sound_result']['source']}")
        else:
            print("   No sound found")
    else:
        print(f"❌ Failed to add test animal")
    
    # Clean up - delete the test animal
    if result['success'] and result['animal_id']:
        print("🧹 Cleaning up test animal...")
        conn = get_snowflake_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM animal_insight_data WHERE id = %s", (result['animal_id'],))
                cursor.close()
                print("✅ Test animal cleaned up")
            except Exception as e:
                print(f"⚠️ Could not clean up test animal: {e}")
            finally:
                conn.close()
    
    return result['success']

def test_sound_sources():
    """Test sound source availability"""
    print("🎵 Testing sound sources...")
    
    results = dashboard_sound_manager.test_sound_sources("robin")
    
    working_sources = []
    for source, result in results.items():
        if result['success']:
            print(f"✅ {source}: Working")
            working_sources.append(source)
        else:
            print(f"❌ {source}: {result.get('error', 'Failed')}")
    
    print(f"Working sources: {len(working_sources)}/{len(results)}")
    return len(working_sources) > 0

def run_all_tests():
    """Run all tests"""
    print("🧪 NatureTrace Dashboard Sound Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Sound Status", test_sound_status),
        ("Animals Without Sounds", test_animals_without_sounds),
        ("Single Animal Update", test_single_animal_update),
        ("Sound Sources", test_sound_sources),
        ("New Animal Addition", test_add_new_animal),
    ]
    
    results = {}
    total_tests = len(tests)
    passed_tests = 0
    
    for test_name, test_func in tests:
        print(f"\n🔬 Running: {test_name}")
        print("-" * 40)
        
        try:
            result = test_func()
            results[test_name] = result
            if result:
                passed_tests += 1
        except Exception as e:
            print(f"❌ Test error: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n📋 Test Summary")
    print("=" * 60)
    print(f"Tests passed: {passed_tests}/{total_tests}")
    print(f"Success rate: {(passed_tests/total_tests*100):.1f}%")
    
    print(f"\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    if passed_tests == total_tests:
        print(f"\n🎉 All tests passed! Your dashboard sound integration is ready to use.")
    else:
        print(f"\n⚠️ Some tests failed. Please check the errors above.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected test error: {e}")
        exit(1)
