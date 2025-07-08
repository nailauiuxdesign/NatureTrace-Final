import requests
import json
import time
from utils.data_utils import get_snowflake_connection
import logging

# Enable detailed logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def remove_duplicate_names():
    """Remove duplicate records with the same name, keeping only the latest one"""
    print("🧹 Removing duplicate records with same names...")
    
    conn = get_snowflake_connection()
    if not conn:
        print("❌ Cannot connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        # First, let's see what duplicates we have
        cursor.execute("""
            SELECT name, COUNT(*) as count 
            FROM animal_insight_data 
            GROUP BY name 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """)
        
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"Found {len(duplicates)} names with duplicates:")
            for name, count in duplicates:
                print(f"   - {name}: {count} records")
            
            # Remove duplicates, keeping only the record with the highest ID (latest)
            cursor.execute("""
                DELETE FROM animal_insight_data 
                WHERE id NOT IN (
                    SELECT MAX(id) 
                    FROM animal_insight_data 
                    GROUP BY name
                )
            """)
            
            deleted_count = cursor.rowcount
            print(f"✅ Removed {deleted_count} duplicate records")
        else:
            print("✅ No duplicates found")
        
        # Get final count
        cursor.execute("SELECT COUNT(*) FROM animal_insight_data")
        final_count = cursor.fetchone()[0]
        print(f"📊 Database now has {final_count} unique records")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error removing duplicates: {e}")
        return False

def get_wikipedia_data(wikipedia_url):
    """Extract data from Wikipedia API using the Wikipedia URL"""
    try:
        if not wikipedia_url:
            return {}
        
        # Extract page title from URL
        page_title = wikipedia_url.split("/")[-1]
        
        # Wikipedia API endpoint for page summary and image
        api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{page_title}"
        
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract the required fields
        wikipedia_data = {
            "original_image": data.get("originalimage", {}).get("source", ""),
            "species": data.get("description", ""),
            "summary": data.get("extract", "")
        }
        
        logger.info(f"Successfully fetched Wikipedia data for {page_title}")
        return wikipedia_data
        
    except Exception as e:
        logger.error(f"Error fetching Wikipedia data for {wikipedia_url}: {e}")
        return {
            "original_image": "",
            "species": "",
            "summary": ""
        }

def get_existing_names():
    """Get list of existing animal names to avoid duplicates"""
    conn = get_snowflake_connection()
    if not conn:
        return set()
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT name FROM animal_insight_data WHERE name IS NOT NULL")
        existing_names = {row[0].lower() for row in cursor.fetchall()}
        cursor.close()
        conn.close()
        return existing_names
    except Exception as e:
        logger.error(f"Error getting existing names: {e}")
        return set()

def fetch_diverse_species_data():
    """Fetch data for a diverse range of species"""
    
    # Expanded list of diverse species
    species_list = [
        # More mammals
        ("Panthera tigris", "Tiger"),
        ("Elephas maximus", "Asian Elephant"),
        ("Ursus maritimus", "Polar Bear"),
        ("Pongo pygmaeus", "Bornean Orangutan"),
        ("Acinonyx jubatus", "Cheetah"),
        ("Giraffa camelopardalis", "Giraffe"),
        ("Hippopotamus amphibius", "Hippopotamus"),
        ("Rhinoceros unicornis", "Indian Rhinoceros"),
        
        # Birds
        ("Haliaeetus leucocephalus", "Bald Eagle"),
        ("Strix nebulosa", "Great Grey Owl"),
        ("Phoenicopterus roseus", "Greater Flamingo"),
        ("Aptenodytes forsteri", "Emperor Penguin"),
        ("Falco peregrinus", "Peregrine Falcon"),
        ("Corvus corax", "Common Raven"),
        
        # Reptiles
        ("Crocodylus niloticus", "Nile Crocodile"),
        ("Python reticulatus", "Reticulated Python"),
        ("Iguana iguana", "Green Iguana"),
        ("Chelonia mydas", "Green Sea Turtle"),
        
        # Marine life
        ("Carcharodon carcharias", "Great White Shark"),
        ("Orcinus orca", "Orca"),
        ("Physeter macrocephalus", "Sperm Whale"),
        ("Octopus vulgaris", "Common Octopus"),
        
        # Insects and others
        ("Danaus plexippus", "Monarch Butterfly"),
        ("Apis mellifera", "European Honey Bee")
    ]
    
    existing_names = get_existing_names()
    all_observations = []
    
    for scientific_name, common_name in species_list:
        # Skip if we already have this species
        if common_name.lower() in existing_names:
            logger.info(f"Skipping {common_name} - already exists")
            continue
            
        logger.info(f"\n--- Fetching data for {scientific_name} ({common_name}) ---")
        
        try:
            # iNaturalist API URL
            url = f"https://api.inaturalist.org/v1/observations?taxon_name={scientific_name}&quality_grade=research&has_photo=true&per_page=3"
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("results"):
                logger.warning(f"No observations found for {scientific_name}")
                continue
            
            # Take only the first observation to avoid duplicates
            observation = data["results"][0]
            taxon = observation.get("taxon", {})
            
            # Extract iNaturalist data
            inaturalist_data = {
                "category": taxon.get("iconic_taxon_name", ""),
                "name": taxon.get("preferred_common_name", common_name),
                "inatural_pic": taxon.get("default_photo", {}).get("medium_url", ""),
                "wikipedia_url": taxon.get("wikipedia_url", "")
            }
            
            # Get Wikipedia data if URL exists
            wikipedia_data = get_wikipedia_data(inaturalist_data["wikipedia_url"])
            
            # Combine all data
            combined_data = {
                "filename": f"inaturalist_{scientific_name.replace(' ', '_')}.jpg",
                "name": inaturalist_data["name"] or common_name,
                "description": wikipedia_data.get("species", f"iNaturalist observation of {scientific_name}"),
                "facts": f"Scientific name: {scientific_name}. Category: {inaturalist_data['category']}. " + wikipedia_data.get("summary", "")[:400],
                "sound_url": "",  # Will be populated later if needed
                "category": inaturalist_data["category"],
                "inatural_pic": inaturalist_data["inatural_pic"],
                "wikipedia_url": inaturalist_data["wikipedia_url"],
                "original_image": wikipedia_data.get("original_image", ""),
                "species": wikipedia_data.get("species", ""),
                "summary": wikipedia_data.get("summary", "")
            }
            
            all_observations.append(combined_data)
            logger.info(f"Processed: {combined_data['name']}")
            
            # Add delay to be respectful to APIs
            time.sleep(2)
            
            # Stop if we have enough new records
            if len(all_observations) >= 20:
                break
                
        except Exception as e:
            logger.error(f"Error processing {scientific_name}: {e}")
            continue
    
    logger.info(f"Successfully prepared {len(all_observations)} new observations")
    return all_observations

def save_new_observations(observations):
    """Save new observations to Snowflake database"""
    success_count = 0
    error_count = 0
    
    for observation in observations:
        try:
            conn = get_snowflake_connection()
            if not conn:
                error_count += 1
                continue
                
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO animal_insight_data (
                    filename, name, description, facts, sound_url, 
                    category, inatural_pic, wikipedia_url, original_image, species, summary
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                observation.get('filename', ''),
                observation.get('name', ''),
                observation.get('description', ''),
                observation.get('facts', ''),
                observation.get('sound_url', ''),
                observation.get('category', ''),
                observation.get('inatural_pic', ''),
                observation.get('wikipedia_url', ''),
                observation.get('original_image', ''),
                observation.get('species', ''),
                observation.get('summary', '')
            ))
            
            cursor.close()
            conn.close()
            success_count += 1
            logger.info(f"Successfully saved: {observation['name']}")
            
        except Exception as e:
            error_count += 1
            logger.error(f"Error saving observation {observation['name']}: {e}")
    
    logger.info(f"Database save complete: {success_count} successful, {error_count} errors")
    return success_count, error_count

def main():
    """Main function to cleanup duplicates and add new diverse data"""
    print("🌿 NatureTrace Data Cleanup and Expansion")
    print("=" * 50)
    
    try:
        # Step 1: Remove duplicates
        if not remove_duplicate_names():
            print("❌ Failed to remove duplicates")
            return
        
        # Step 2: Fetch new diverse species data
        print("\n📡 Fetching diverse species data...")
        observations = fetch_diverse_species_data()
        
        if not observations:
            print("❌ No new observations fetched")
            return
        
        # Step 3: Save new observations
        print(f"\n💾 Saving {len(observations)} new observations to database...")
        success_count, error_count = save_new_observations(observations)
        
        print(f"\n🎉 Data cleanup and expansion complete!")
        print(f"   ✅ Successfully added: {success_count} new records")
        print(f"   ❌ Errors: {error_count} records")
        
        if success_count > 0:
            print(f"\n🚀 Your NatureTrace database now has more diverse animal data!")
            print(f"   Run 'python verify_data.py' to see the updated statistics.")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
