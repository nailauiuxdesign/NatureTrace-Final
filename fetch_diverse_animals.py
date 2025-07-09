#!/usr/bin/env python3
"""
Fetch Enhanced Diverse Animal Data
Fetch 50+ diverse animals from iNaturalist with improved categorization
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fetch_initial_data import fetch_diverse_animals_by_category, fetch_multiple_species, save_observations_to_database, get_snowflake_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Fetch diverse animal data with enhanced options"""
    print("NatureTrace Enhanced Diverse Data Fetcher")
    print("=" * 55)
    print("This will fetch 50+ diverse animal species from iNaturalist")
    print("including birds, mammals, reptiles, amphibians, fish, and insects")
    
    try:
        # Test database connection
        conn = get_snowflake_connection()
        if not conn:
            print("❌ Cannot connect to Snowflake database. Please check your configuration.")
            return
        conn.close()
        print("✅ Database connection successful")
        
        # Show options
        print("\n📋 Data Fetching Options:")
        print("1. Quick diverse fetch (6 categories, ~50 animals)")
        print("2. Comprehensive fetch (specific species + categories, ~80+ animals)")
        print("3. Categories only (birds, mammals, etc.)")
        print("4. Specific species only (35+ predefined species)")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        all_observations = []
        
        if choice == "1":
            print("\n🔍 Fetching quick diverse animals by category...")
            observations = fetch_diverse_animals_by_category()
            all_observations.extend(observations)
            
        elif choice == "2":
            print("\n📡 Comprehensive fetch: both approaches...")
            
            print("  🎯 Fetching specific species...")
            species_obs = fetch_multiple_species()
            all_observations.extend(species_obs)
            
            print("  🔍 Fetching diverse categories...")
            diverse_obs = fetch_diverse_animals_by_category()
            all_observations.extend(diverse_obs)
            
        elif choice == "3":
            print("\n🔍 Fetching animals by categories only...")
            observations = fetch_diverse_animals_by_category()
            all_observations.extend(observations)
            
        elif choice == "4":
            print("\n🎯 Fetching specific species only...")
            observations = fetch_multiple_species()
            all_observations.extend(observations)
            
        else:
            print("❌ Invalid choice. Exiting.")
            return
        
        if not all_observations:
            print("❌ No observations fetched. Please check your internet connection.")
            return
        
        # Remove duplicates
        unique_observations = []
        seen_names = set()
        for obs in all_observations:
            name_key = obs["name"].lower().strip()
            if name_key not in seen_names:
                unique_observations.append(obs)
                seen_names.add(name_key)
        
        print(f"\n📊 Fetching Summary:")
        print(f"   Total fetched: {len(all_observations)} observations")
        print(f"   Unique animals: {len(unique_observations)} species")
        print(f"   Duplicates removed: {len(all_observations) - len(unique_observations)}")
        
        # Show categories
        categories = {}
        for obs in unique_observations:
            cat = obs.get("category", "Unknown")
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"\n🏷️ Category Breakdown:")
        for category, count in sorted(categories.items()):
            print(f"   {category}: {count} animals")
        
        # Confirm save
        proceed = input(f"\n💾 Save {len(unique_observations)} animals to database? (y/N): ").strip().lower()
        
        if proceed == 'y':
            print(f"\n💾 Saving {len(unique_observations)} unique animals to database...")
            success_count, error_count = save_observations_to_database(unique_observations)
            
            print(f"\n🎉 Enhanced diverse data fetch complete!")
            print(f"   ✅ Successfully saved: {success_count} animals")
            print(f"   ❌ Errors: {error_count} animals")
            print(f"   📈 Success rate: {(success_count/(success_count+error_count)*100):.1f}%" if (success_count+error_count) > 0 else "N/A")
            
            if success_count > 0:
                print(f"\n🚀 Your NatureTrace database now has diverse animal data!")
                print(f"   🔊 Run 'python batch_update_dashboard_sounds.py' to add sounds")
                print(f"   📱 View the data in your Streamlit dashboard")
                print(f"   🧪 Test with 'python test_freesound_integration.py'")
        else:
            print("❌ Save cancelled.")
        
    except Exception as e:
        logger.error(f"Error in enhanced data fetch: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Fetch interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
