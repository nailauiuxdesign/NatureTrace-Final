#!/usr/bin/env python3
"""
Test script for a single animal to debug sources
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.sound_utils import test_multiple_sound_sources

def test_single_animal(animal_name="Wolf"):
    """Test a single animal to debug source issues"""
    
    print(f"🔊 Testing {animal_name}")
    print("=" * 50)
    
    # Test with enhanced system
    test_results = test_multiple_sound_sources(animal_name, "mammal")
    
    print(f"\n📊 Results for {animal_name}:")
    print(f"Best URL: {test_results.get('best_url', 'None')}")
    print(f"Best Source: {test_results.get('best_source', 'None')}")
    
    print("\n🔍 All Source Results:")
    for source, result in test_results.get('sources', {}).items():
        status = "✅" if result.get('valid') else "❌"
        error = f" - {result.get('error', '')}" if result.get('error') else ""
        url = result.get('url', 'No URL')
        print(f"  {status} {source}: {url}{error}")
    
    return test_results

if __name__ == "__main__":
    test_single_animal("Wolf")
