#!/usr/bin/env python3
"""
Quick test script to check multiple animals for sound availability
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.sound_utils import test_multiple_sound_sources, generate_animal_sound
import time

def test_animals_quickly():
    """Test a variety of animals to see sound availability"""
    
    # Test animals likely to have good sound coverage
    test_animals = [
        "Orca",           # Marine mammal - should work well
        "Wolf",           # Common mammal
        "Lion",           # Popular animal
        "Eagle",          # Bird - should work with Xeno-Canto
        "Owl",            # Bird with distinctive calls
        "Elephant",       # Large mammal
        "Dolphin",        # Marine mammal
        "Crow",           # Common bird
        "Frog",           # Amphibian
        "Polar Bear"      # Previously problematic
    ]
    
    print("🔊 Quick Animal Sound Test")
    print("=" * 50)
    print(f"Testing {len(test_animals)} animals with enhanced 7-source system...")
    print()
    
    results = []
    
    for i, animal in enumerate(test_animals, 1):
        print(f"[{i}/{len(test_animals)}] Testing {animal}...")
        
        try:
            # Test with enhanced system
            test_results = test_multiple_sound_sources(animal, "unknown")
            
            if test_results.get("best_url"):
                status = "✅ SUCCESS"
                best_source = test_results.get("best_source", "unknown")
                url = test_results["best_url"]
                
                # Check for quality metrics
                quality_info = ""
                if "quality_score" in test_results:
                    quality_info = f" (Quality: {test_results['quality_score']}/7)"
                
                # Check duration requirement
                duration_info = ""
                if "meets_1_second_requirement" in test_results:
                    req_status = test_results["meets_1_second_requirement"]
                    if req_status == True:
                        duration_info = " 🎯 Perfect ≤1s"
                    elif req_status == False:
                        duration_info = " ⚠️ >1s"
                
                print(f"   {status} - {best_source}{quality_info}{duration_info}")
                print(f"   URL: {url}")
                
                results.append({
                    "animal": animal,
                    "success": True,
                    "source": best_source,
                    "url": url,
                    "quality_score": test_results.get("quality_score"),
                    "meets_duration": test_results.get("meets_1_second_requirement")
                })
            else:
                print(f"   ❌ FAILED - No valid sources found")
                results.append({
                    "animal": animal,
                    "success": False,
                    "source": None,
                    "url": None
                })
                
        except Exception as e:
            print(f"   ❌ ERROR - {str(e)}")
            results.append({
                "animal": animal,
                "success": False,
                "source": None,
                "url": None,
                "error": str(e)
            })
        
        # Small delay to avoid overwhelming APIs
        time.sleep(0.5)
        print()
    
    # Summary
    print("=" * 50)
    print("📊 SUMMARY RESULTS")
    print("=" * 50)
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    print(f"✅ Successful: {len(successful)}/{len(test_animals)} ({len(successful)/len(test_animals)*100:.1f}%)")
    print(f"❌ Failed: {len(failed)}/{len(test_animals)} ({len(failed)/len(test_animals)*100:.1f}%)")
    print()
    
    if successful:
        print("🎉 WORKING ANIMALS:")
        for result in successful:
            quality_str = f" (Q:{result['quality_score']}/7)" if result.get('quality_score') else ""
            duration_str = ""
            if result.get('meets_duration') == True:
                duration_str = " 🎯"
            elif result.get('meets_duration') == False:
                duration_str = " ⚠️"
            
            print(f"   • {result['animal']} - {result['source']}{quality_str}{duration_str}")
    
    if failed:
        print()
        print("❌ FAILED ANIMALS:")
        for result in failed:
            error_str = f" ({result.get('error', 'No sources found')})" if result.get('error') else ""
            print(f"   • {result['animal']}{error_str}")
    
    # Source effectiveness
    print()
    print("📈 SOURCE EFFECTIVENESS:")
    source_counts = {}
    for result in successful:
        source = result['source']
        source_counts[source] = source_counts.get(source, 0) + 1
    
    for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {source}: {count} animals")
    
    return results

if __name__ == "__main__":
    test_animals_quickly()
