#!/usr/bin/env python3
"""
Sound Database Updater - Automatically fetch and update sound URLs for animals in the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_utils import update_animal_sound_url, bulk_update_missing_sounds, get_snowflake_connection
from utils.sound_utils import batch_update_sounds_for_dashboard
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_single_animal(animal_name: str):
    """Update sound for a single animal by name"""
    print(f"\n🔊 Updating sound for: {animal_name}")
    print("=" * 50)
    
    result = update_animal_sound_url(animal_name=animal_name)
    
    if result["success"]:
        print(f"✅ SUCCESS!")
        print(f"   Animal: {animal_name}")
        print(f"   Sound URL: {result['sound_url']}")
        print(f"   Source: {result['source']}")
        print(f"   Message: {result['message']}")
    else:
        print(f"❌ FAILED!")
        print(f"   Animal: {animal_name}")
        print(f"   Error: {result['message']}")
    
    return result

def update_multiple_animals(animal_names: list):
    """Update sounds for multiple animals"""
    print(f"\n🔊 Updating sounds for {len(animal_names)} animals")
    print("=" * 60)
    
    results = []
    successful = 0
    failed = 0
    
    for i, animal_name in enumerate(animal_names, 1):
        print(f"\n[{i}/{len(animal_names)}] Processing: {animal_name}")
        result = update_animal_sound_url(animal_name=animal_name)
        results.append(result)
        
        if result["success"]:
            successful += 1
            print(f"   ✅ {result['source']} - {result['sound_url'][:50]}...")
        else:
            failed += 1
            print(f"   ❌ {result['message']}")
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total: {len(animal_names)}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    print(f"   Success Rate: {(successful/len(animal_names)*100):.1f}%")
    
    return results

def update_all_missing_sounds(limit=None):
    """Update all animals in database that don't have sounds"""
    print(f"\n🔊 Updating ALL missing sounds in database")
    if limit:
        print(f"   (Limited to {limit} animals)")
    print("=" * 60)
    
    result = bulk_update_missing_sounds(limit=limit)
    
    print(f"\n📊 BULK UPDATE SUMMARY:")
    print(f"   Total Processed: {result['total_processed']}")
    print(f"   Successful: {result['successful']}")
    print(f"   Failed: {result['failed']}")
    if result['total_processed'] > 0:
        print(f"   Success Rate: {(result['successful']/result['total_processed']*100):.1f}%")
    
    # Show details for failed ones
    if result['failed'] > 0:
        print(f"\n❌ FAILED ANIMALS:")
        for r in result['results']:
            if not r['success']:
                print(f"   • {r['name']}: {r['message']}")
    
    # Show successful ones
    if result['successful'] > 0:
        print(f"\n✅ SUCCESSFUL ANIMALS:")
        for r in result['results']:
            if r['success']:
                print(f"   • {r['name']}: {r['source']}")
    
    return result

def check_database_connection():
    """Check if database connection works"""
    print("\n🔌 Testing Database Connection")
    print("=" * 40)
    
    conn = get_snowflake_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM animal_insight_data")
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            print(f"✅ Database connection successful!")
            print(f"   Total animals in database: {count}")
            return True
        except Exception as e:
            print(f"❌ Database query failed: {e}")
            return False
    else:
        print("❌ Database connection failed!")
        return False

def main():
    """Main function with menu options"""
    print("🎵 NatureTrace Sound Database Updater")
    print("=" * 50)
    
    # Check database connection first
    if not check_database_connection():
        print("\nPlease check your database configuration and try again.")
        return
    
    while True:
        print("\n📋 OPTIONS:")
        print("1. Update sound for a single animal")
        print("2. Update sounds for multiple animals")
        print("3. Update all missing sounds (first 10)")
        print("4. Update all missing sounds (first 50)")
        print("5. Update ALL missing sounds (no limit)")
        print("6. Test with sample animals")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == "1":
            animal_name = input("Enter animal name: ").strip()
            if animal_name:
                update_single_animal(animal_name)
        
        elif choice == "2":
            animals_input = input("Enter animal names (comma-separated): ").strip()
            if animals_input:
                animal_names = [name.strip() for name in animals_input.split(",")]
                update_multiple_animals(animal_names)
        
        elif choice == "3":
            update_all_missing_sounds(limit=10)
        
        elif choice == "4":
            update_all_missing_sounds(limit=50)
        
        elif choice == "5":
            confirm = input("This will update ALL animals without sounds. Continue? (y/N): ").strip().lower()
            if confirm == 'y':
                update_all_missing_sounds()
        
        elif choice == "6":
            sample_animals = ["Wolf", "Eagle", "Lion", "Elephant", "Owl"]
            update_multiple_animals(sample_animals)
        
        elif choice == "7":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
