import requests
import json
import time
from utils.data_utils import save_inaturalist_data_to_snowflake, get_snowflake_connection
import logging

# Enable detailed logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_wikipedia_data(wikipedia_url):
    """Extract data from Wikipedia API using the Wikipedia URL"""
    try:
        if not wikipedia_url:
            return {}
        
        # Extract page title from URL
        page_title = wikipedia_url.split("/")[-1]
        
        # Wikipedia API endpoint for page summary and image
        api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{page_title}"
        
        # Set proper User-Agent to comply with Wikimedia policy
        headers = {
            'User-Agent': 'NatureTrace/1.0 (flora.jiang1990@gmail.com)'
        }
        
        response = requests.get(api_url, timeout=10, headers=headers)
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

def fetch_inaturalist_observations(taxon_name="Canis lupus", limit=50):
    """Fetch observations from iNaturalist API with increased limit for more diversity"""
    try:
        # iNaturalist API URL with higher limit for more diverse species
        url = f"https://api.inaturalist.org/v1/observations?taxon_name={taxon_name}&quality_grade=research&has_photo=true&per_page={limit}&order=desc&order_by=created_at"
        
        logger.info(f"Fetching iNaturalist data from: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        observations = []
        
        for i, observation in enumerate(data.get("results", [])):
            try:
                taxon = observation.get("taxon", {})
                
                # Extract location data from observation
                geojson = observation.get("geojson", {})
                coordinates = geojson.get("coordinates", []) if geojson else []
                latitude = coordinates[1] if len(coordinates) >= 2 else None
                longitude = coordinates[0] if len(coordinates) >= 2 else None
                location_string = observation.get("location", "")
                place_guess = observation.get("place_guess", "")
                
                # Extract iNaturalist data
                inaturalist_data = {
                    "category": taxon.get("iconic_taxon_name", ""),
                    "name": taxon.get("preferred_common_name", ""),
                    "inatural_pic": taxon.get("default_photo", {}).get("medium_url", ""),
                    "wikipedia_url": taxon.get("wikipedia_url", "")
                }
                
                # Get Wikipedia data if URL exists
                wikipedia_data = get_wikipedia_data(inaturalist_data["wikipedia_url"])
                
                # Combine all data including location
                combined_data = {
                    "filename": f"inaturalist_{taxon_name.replace(' ', '_')}_{i+1}.jpg",
                    "name": inaturalist_data["name"] or f"{taxon_name} observation {i+1}",
                    "description": wikipedia_data.get("species", f"iNaturalist observation of {taxon_name}"),
                    "facts": f"Category: {inaturalist_data['category']}. " + wikipedia_data.get("summary", "")[:500],
                    "sound_url": "",  # Will be populated later if needed
                    "category": inaturalist_data["category"],
                    "inatural_pic": inaturalist_data["inatural_pic"],
                    "wikipedia_url": inaturalist_data["wikipedia_url"],
                    "original_image": wikipedia_data.get("original_image", ""),
                    "species": wikipedia_data.get("species", ""),
                    "summary": wikipedia_data.get("summary", ""),
                    "latitude": latitude,
                    "longitude": longitude,
                    "location_string": location_string,
                    "place_guess": place_guess
                }
                
                observations.append(combined_data)
                logger.info(f"Processed observation {i+1}: {combined_data['name']}")
                
                # Add delay to be respectful to APIs
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing observation {i+1}: {e}")
                continue
        
        logger.info(f"Successfully fetched {len(observations)} observations")
        return observations
        
    except Exception as e:
        logger.error(f"Error fetching iNaturalist observations: {e}")
        return []

def save_observations_to_database(observations):
    """Save all observations to Snowflake database"""
    success_count = 0
    error_count = 0
    
    for observation in observations:
        try:
            if save_inaturalist_data_to_snowflake(observation):
                success_count += 1
                logger.info(f"Successfully saved: {observation['name']}")
            else:
                error_count += 1
                logger.error(f"Failed to save: {observation['name']}")
        except Exception as e:
            error_count += 1
            logger.error(f"Error saving observation {observation['name']}: {e}")
    
    logger.info(f"Database save complete: {success_count} successful, {error_count} errors")
    return success_count, error_count

def fetch_multiple_species():
    """Fetch data for multiple diverse species with expanded list"""
    species_list = [
        # Mammals
        "Canis lupus",           # Gray Wolf
        "Panthera leo",          # Lion  
        "Ursus americanus",      # American Black Bear
        "Vulpes vulpes",         # Red Fox
        "Elephas maximus",       # Asian Elephant
        "Odocoileus virginianus", # White-tailed Deer
        "Felis catus",           # Domestic Cat
        "Canis familiaris",      # Domestic Dog
        "Rattlesnake",           # Rattlesnake
        "Alligator mississippiensis", # American Alligator
        
        # Birds
        "Aquila chrysaetos",     # Golden Eagle
        "Turdus migratorius",    # American Robin
        "Corvus brachyrhynchos", # American Crow
        "Haliaeetus leucocephalus", # Bald Eagle
        "Strix varia",           # Barred Owl
        "Cardinalis cardinalis", # Northern Cardinal
        "Tachycineta bicolor",   # Tree Swallow
        "Poecile atricapillus",  # Black-capped Chickadee
        "Sialia sialis",         # Eastern Bluebird
        "Picidae",               # Woodpeckers (family)
        
        # Marine Animals
        "Megaptera novaeangliae", # Humpback Whale
        "Tursiops truncatus",    # Bottlenose Dolphin
        "Phoca vitulina",        # Harbor Seal
        "Chelonia mydas",        # Green Sea Turtle
        
        # Amphibians & Reptiles
        "Lithobates clamitans",  # Green Frog
        "Pseudacris crucifer",   # Spring Peeper
        "Thamnophis sirtalis",   # Common Garter Snake
        "Chelydra serpentina",   # Common Snapping Turtle
        
        # Insects & Arthropods
        "Danaus plexippus",      # Monarch Butterfly
        "Bombus",                # Bumblebees (genus)
        "Gryllus",               # Crickets (genus)
        "Cicadidae",             # Cicadas (family)
        
        # Less common but interesting
        "Procyon lotor",         # Raccoon
        "Mephitis mephitis",     # Striped Skunk
        "Sciurus carolinensis",  # Eastern Gray Squirrel
        "Castor canadensis",     # American Beaver
        "Antilocapra americana"  # Pronghorn
    ]
    
    all_observations = []
    
    for i, species in enumerate(species_list):
        logger.info(f"\n--- [{i+1}/{len(species_list)}] Fetching data for {species} ---")
        # Fetch fewer per species but more species overall for diversity
        observations = fetch_inaturalist_observations(species, limit=3)
        all_observations.extend(observations)
        
        # Add delay between species to be respectful to APIs
        time.sleep(1.5)
        
        # Progress update
        if (i + 1) % 10 == 0:
            logger.info(f"Progress: {i+1}/{len(species_list)} species processed, {len(all_observations)} total observations")
    
    logger.info(f"Completed fetching {len(all_observations)} diverse observations from {len(species_list)} species")
    return all_observations

def fetch_diverse_animals_by_category():
    """Fetch diverse animals by major taxonomic categories to ensure variety"""
    
    # Define searches by major groups to ensure diversity
    category_searches = {
        "Birds": [
            {"iconic_taxon": "Aves", "query": "birds", "limit": 15},
            {"place_id": 1, "iconic_taxon": "Aves", "query": "songbirds", "limit": 10}  # North America songbirds
        ],
        "Mammals": [
            {"iconic_taxon": "Mammalia", "query": "mammals", "limit": 15},
            {"iconic_taxon": "Mammalia", "query": "carnivora", "limit": 8}  # Carnivores
        ],
        "Reptiles": [
            {"iconic_taxon": "Reptilia", "query": "reptiles", "limit": 8}
        ],
        "Amphibians": [
            {"iconic_taxon": "Amphibia", "query": "amphibians", "limit": 6}
        ],
        "Fish": [
            {"iconic_taxon": "Actinopterygii", "query": "fish", "limit": 6}
        ],
        "Insects": [
            {"iconic_taxon": "Insecta", "query": "insects", "limit": 6}
        ]
    }
    
    all_observations = []
    
    for category, searches in category_searches.items():
        logger.info(f"\n🔍 Fetching {category}...")
        
        for search_config in searches:
            try:
                # Build URL with category-specific parameters
                params = {
                    "quality_grade": "research",
                    "has_photo": "true",
                    "per_page": search_config["limit"],
                    "order": "desc",
                    "order_by": "created_at",
                    "verifiable": "true"
                }
                
                if "iconic_taxon" in search_config:
                    params["iconic_taxa"] = search_config["iconic_taxon"]
                if "place_id" in search_config:
                    params["place_id"] = search_config["place_id"]
                if "query" in search_config:
                    params["q"] = search_config["query"]
                
                # Make API call
                url = "https://api.inaturalist.org/v1/observations"
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                observations = data.get("results", [])
                
                logger.info(f"Found {len(observations)} {category.lower()} observations")
                
                # Process observations
                for i, observation in enumerate(observations):
                    try:
                        taxon = observation.get("taxon", {})
                        
                        # Skip if no common name
                        common_name = taxon.get("preferred_common_name")
                        if not common_name:
                            continue
                        
                        # Extract location data from observation
                        geojson = observation.get("geojson", {})
                        coordinates = geojson.get("coordinates", []) if geojson else []
                        latitude = coordinates[1] if len(coordinates) >= 2 else None
                        longitude = coordinates[0] if len(coordinates) >= 2 else None
                        location_string = observation.get("location", "")
                        place_guess = observation.get("place_guess", "")
                        
                        # Extract data
                        inaturalist_data = {
                            "category": taxon.get("iconic_taxon_name", category),
                            "name": common_name,
                            "inatural_pic": taxon.get("default_photo", {}).get("medium_url", ""),
                            "wikipedia_url": taxon.get("wikipedia_url", "")
                        }
                        
                        # Get Wikipedia data if URL exists
                        wikipedia_data = get_wikipedia_data(inaturalist_data["wikipedia_url"])
                        
                        # Create unique filename
                        safe_name = common_name.replace(" ", "_").replace("/", "_")
                        filename = f"diverse_{category.lower()}_{safe_name}_{i+1}.jpg"
                        
                        # Combine all data including location
                        combined_data = {
                            "filename": filename,
                            "name": common_name,
                            "description": wikipedia_data.get("species", f"A {inaturalist_data['category'].lower()} species from iNaturalist"),
                            "facts": f"Category: {inaturalist_data['category']}. " + (wikipedia_data.get("summary", "")[:400] if wikipedia_data.get("summary") else f"This {common_name} was observed in the wild and documented on iNaturalist."),
                            "sound_url": "",  # Will be populated by sound system
                            "category": inaturalist_data["category"],
                            "inatural_pic": inaturalist_data["inatural_pic"],
                            "wikipedia_url": inaturalist_data["wikipedia_url"],
                            "original_image": wikipedia_data.get("original_image", ""),
                            "species": wikipedia_data.get("species", ""),
                            "summary": wikipedia_data.get("summary", ""),
                            "latitude": latitude,
                            "longitude": longitude,
                            "location_string": location_string,
                            "place_guess": place_guess
                        }
                        
                        all_observations.append(combined_data)
                        logger.info(f"  Processed: {common_name}")
                        
                    except Exception as e:
                        logger.error(f"Error processing {category} observation {i+1}: {e}")
                        continue
                
                # Small delay between API calls
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error fetching {category} with config {search_config}: {e}")
                continue
    
    logger.info(f"✅ Fetched {len(all_observations)} diverse observations across all categories")
    return all_observations

def main():
    """Main function to fetch and save initial data with diverse species"""
    print("🌿 NatureTrace Enhanced Data Fetcher - Diverse Species")
    print("=" * 60)
    
    try:
        # Test database connection first
        conn = get_snowflake_connection()
        if not conn:
            print("❌ Cannot connect to Snowflake database. Please check your configuration.")
            return
        conn.close()
        print("✅ Database connection successful")
        
        # Ask user which approach to use
        print("\nChoose data fetching approach:")
        print("1. Specific species list (35+ species, 3 observations each)")
        print("2. Diverse categories (Birds, Mammals, etc. with variety)")
        print("3. Both approaches combined")
        
        choice = input("Enter choice (1, 2, or 3): ").strip()
        
        all_observations = []
        
        if choice in ["1", "3"]:
            print("\n📡 Fetching observations from specific species list...")
            species_observations = fetch_multiple_species()
            all_observations.extend(species_observations)
            print(f"✅ Fetched {len(species_observations)} observations from specific species")
        
        if choice in ["2", "3"]:
            print("\n🔍 Fetching diverse observations by category...")
            diverse_observations = fetch_diverse_animals_by_category()
            all_observations.extend(diverse_observations)
            print(f"✅ Fetched {len(diverse_observations)} diverse observations by category")
        
        if not all_observations:
            print("❌ No observations fetched. Please check your internet connection and try again.")
            return
        
        # Remove duplicates based on name
        unique_observations = []
        seen_names = set()
        for obs in all_observations:
            if obs["name"].lower() not in seen_names:
                unique_observations.append(obs)
                seen_names.add(obs["name"].lower())
        
        print(f"\n💾 Saving {len(unique_observations)} unique observations to database...")
        print(f"   (Removed {len(all_observations) - len(unique_observations)} duplicates)")
        
        success_count, error_count = save_observations_to_database(unique_observations)
        
        print(f"\n🎉 Enhanced data fetch complete!")
        print(f"   ✅ Successfully saved: {success_count} unique animal records")
        print(f"   ❌ Errors: {error_count} records")
        print(f"   📊 Total diversity: {len(unique_observations)} different species")
        
        if success_count > 0:
            print(f"\n🚀 Your NatureTrace database now has diverse animal data!")
            print(f"   🔊 Use the sound integration features to add audio")
            print(f"   📱 View the enhanced data in your Streamlit dashboard")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
