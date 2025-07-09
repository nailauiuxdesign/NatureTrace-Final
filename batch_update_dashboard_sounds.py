#!/usr/bin/env python3
"""
Batch Update All Dashboard Animals with Sounds
Run this script to update all animals in your dashboard with sound URLs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dashboard_sound_integration import dashboard_sound_manager
import time

def main():
    print("NatureTrace Dashboard - Batch Sound Update")
    print("=" * 50)
    
    # Get current status
    print("Getting current sound status...")
    status = dashboard_sound_manager.get_dashboard_sound_status()
    
    if "error" in status:
        print(f"❌ Error getting status: {status['error']}")
        return
    
    print(f"Total animals: {status['total_animals']}")
    print(f"Animals with sounds: {status['animals_with_sound']}")
    print(f"Animals without sounds: {status['animals_without_sound']}")
    print(f"Current coverage: {status['sound_coverage_percentage']}%")
    
    if status['animals_without_sound'] == 0:
        print("🎉 All animals already have sounds!")
        return
    
    # Ask user for confirmation
    print(f"\n🚀 Ready to update {status['animals_without_sound']} animals with sounds")
    
    # Ask for batch size
    try:
        batch_size = input(f"Enter batch size (or 'all' for all {status['animals_without_sound']} animals): ").strip()
        if batch_size.lower() == 'all':
            limit = None
        else:
            limit = int(batch_size)
    except ValueError:
        print("Invalid input. Using default batch size of 10.")
        limit = 10
    
    proceed = input(f"Proceed with updating {'all' if limit is None else limit} animals? (y/N): ").strip().lower()
    
    if proceed != 'y':
        print("Operation cancelled.")
        return
    
    print(f"\n🔄 Starting batch update...")
    start_time = time.time()
    
    # Perform the batch update
    result = dashboard_sound_manager.batch_update_all_missing_sounds(limit=limit)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n✅ Batch update completed in {duration:.1f} seconds")
    print(f"📊 Results:")
    print(f"   Total processed: {result['total_processed']}")
    print(f"   Successful: {result['successful']}")
    print(f"   Failed: {result['failed']}")
    print(f"   Success rate: {(result['successful']/result['total_processed']*100):.1f}%" if result['total_processed'] > 0 else "N/A")
    
    # Show detailed results
    if result['results']:
        print(f"\n📋 Detailed Results:")
        print("-" * 60)
        
        successful_results = [r for r in result['results'] if r['success']]
        failed_results = [r for r in result['results'] if not r['success']]
        
        if successful_results:
            print("✅ Successful updates:")
            for animal_result in successful_results[:10]:  # Show first 10
                print(f"   {animal_result['name']}: {animal_result['source']}")
            if len(successful_results) > 10:
                print(f"   ... and {len(successful_results) - 10} more")
        
        if failed_results:
            print("\n❌ Failed updates:")
            for animal_result in failed_results[:5]:  # Show first 5 failures
                print(f"   {animal_result['name']}: {animal_result['message']}")
            if len(failed_results) > 5:
                print(f"   ... and {len(failed_results) - 5} more failures")
    
    # Show updated status
    print(f"\n📊 Updated Status:")
    updated_status = dashboard_sound_manager.get_dashboard_sound_status()
    if "error" not in updated_status:
        print(f"Animals with sounds: {updated_status['animals_with_sound']}")
        print(f"Coverage: {updated_status['sound_coverage_percentage']}%")
        print(f"Sources breakdown: {updated_status['sources_breakdown']}")
    
    print(f"\n🎉 Update complete! Your dashboard now has more animal sounds.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Update interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please check your database connection and try again.")
