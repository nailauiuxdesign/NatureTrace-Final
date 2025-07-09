#!/usr/bin/env python3
"""
Script to update existing database records with location data from iNaturalist API
"""

import requests
import time
import logging
import json
import re
from utils.data_utils import get_snowflake_connection, fetch_dashboard_data
import pandas as pd
from groq import Groq
import streamlit as st

# Enable detailed logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def search_inaturalist_for_location(animal_name, category=None):
    """
    Search iNaturalist for location data for a specific animal
    
    Args:
        animal_name: Name of the animal to search for
        category: Optional category filter
    
    Returns:
        dict: Location data or None if not found
    """
    try:
        # Build search parameters
        params = {
            "quality_grade": "research",
            "has_photo": "true",
            "per_page": 5,  # Get a few results to find best match
            "order": "desc",
            "order_by": "created_at"
        }
        
        # Try multiple search strategies
        search_queries = [
            animal_name,  # Exact name
            animal_name.replace(" ", "+"),  # Space to plus
            f'"{animal_name}"'  # Quoted exact match
        ]
        
        if category:
            # Add category-based searches
            iconic_taxa_map = {
                'Bird': 'Aves',
                'Mammal': 'Mammalia', 
                'Reptile': 'Reptilia',
                'Amphibian': 'Amphibia',
                'Fish': 'Actinopterygii',
                'Insect': 'Insecta'
            }
            if category in iconic_taxa_map:
                search_queries.append(f"{animal_name}+{iconic_taxa_map[category]}")
        
        for query in search_queries:
            try:
                params["q"] = query
                
                logger.info(f"Searching iNaturalist for: {query}")
                url = "https://api.inaturalist.org/v1/observations"
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                observations = data.get("results", [])
                
                logger.info(f"Found {len(observations)} observations for query: {query}")
                
                # Look for observations with location data
                for observation in observations:
                    taxon = observation.get("taxon", {})
                    common_name = taxon.get("preferred_common_name", "")
                    
                    # Check if this matches our animal (case-insensitive)
                    if (common_name.lower() == animal_name.lower() or 
                        animal_name.lower() in common_name.lower()):
                        
                        # Extract location data
                        geojson = observation.get("geojson", {})
                        coordinates = geojson.get("coordinates", []) if geojson else []
                        
                        if len(coordinates) >= 2:
                            location_data = {
                                "latitude": coordinates[1],
                                "longitude": coordinates[0],
                                "location_string": observation.get("location", ""),
                                "place_guess": observation.get("place_guess", ""),
                                "observation_id": observation.get("id"),
                                "matched_name": common_name
                            }
                            
                            logger.info(f"✅ Found location for {animal_name}: {location_data['place_guess']}")
                            return location_data
                
                # Small delay between queries
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error with query '{query}': {e}")
                continue
        
        logger.warning(f"❌ No location data found for {animal_name} in iNaturalist")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error searching for {animal_name}: {e}")
        return None

def get_location_from_wikipedia(animal_name):
    """
    Try to extract location information from Wikipedia
    
    Args:
        animal_name: Name of the animal
    
    Returns:
        dict: Location data or None if not found
    """
    try:
        # Search for Wikipedia page
        search_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + animal_name.replace(" ", "_")
        
        headers = {
            'User-Agent': 'NatureTrace/1.0 (flora.jiang1990@gmail.com)'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            extract = data.get('extract', '')
            
            # Look for geographic mentions in the text
            geographic_patterns = [
                r'found in ([^.]+)',
                r'native to ([^.]+)',
                r'distributed in ([^.]+)',
                r'ranges from ([^.]+)',
                r'occurs in ([^.]+)',
                r'inhabits ([^.]+)',
                r'lives in ([^.]+)'
            ]
            
            for pattern in geographic_patterns:
                match = re.search(pattern, extract, re.IGNORECASE)
                if match:
                    location_text = match.group(1)
                    # Clean up the location text
                    location_text = re.sub(r'[,;].*', '', location_text).strip()
                    
                    # Try to get coordinates for this location using a geocoding service
                    coords = geocode_location(location_text)
                    if coords:
                        logger.info(f"✅ Found Wikipedia location for {animal_name}: {location_text}")
                        return {
                            "latitude": coords['lat'],
                            "longitude": coords['lng'],
                            "location_string": location_text,
                            "place_guess": f"{location_text} (from Wikipedia)"
                        }
            
        logger.warning(f"❌ No location data found for {animal_name} in Wikipedia")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error searching Wikipedia for {animal_name}: {e}")
        return None

def geocode_location(location_text):
    """
    Convert location text to coordinates using a free geocoding service
    
    Args:
        location_text: Text description of location
    
    Returns:
        dict: Coordinates or None if not found
    """
    try:
        # Use Nominatim (OpenStreetMap) free geocoding service
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': location_text,
            'format': 'json',
            'limit': 1
        }
        
        headers = {
            'User-Agent': 'NatureTrace/1.0 (flora.jiang1990@gmail.com)'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                result = data[0]
                return {
                    'lat': float(result['lat']),
                    'lng': float(result['lon'])
                }
        
        return None
        
    except Exception as e:
        logger.error(f"Error geocoding {location_text}: {e}")
        return None

def get_location_from_groq(animal_name, category=None):
    """
    Use Groq AI to get typical habitat/location information for an animal
    
    Args:
        animal_name: Name of the animal
        category: Optional category of the animal
    
    Returns:
        dict: Location data or None if not found
    """
    try:
        # Initialize Groq client
        client = Groq(api_key=st.secrets.get("groq_api_key"))
        
        # Create a prompt to get location information
        category_info = f" (a {category})" if category else ""
        prompt = f"""
For the animal "{animal_name}"{category_info}, provide the primary geographic region where this species is typically found.

Respond with ONLY a JSON object in this exact format:
{{
    "region": "specific geographic region name",
    "country": "primary country if applicable",
    "continent": "continent name",
    "coordinates": {{"lat": latitude_number, "lng": longitude_number}}
}}

If you cannot determine a specific location, respond with: {{"error": "unknown"}}

Examples:
- For "African Elephant": {{"region": "Sub-Saharan Africa", "country": "Kenya", "continent": "Africa", "coordinates": {{"lat": -1.2921, "lng": 36.8219}}}}
- For "Bald Eagle": {{"region": "North America", "country": "United States", "continent": "North America", "coordinates": {{"lat": 39.8283, "lng": -98.5795}}}}
"""

        # Make the API call
        chat_completion = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": prompt
            }],
            model="llama3-8b-8192",
            temperature=0.1,
            max_tokens=200
        )
        
        response_text = chat_completion.choices[0].message.content.strip()
        
        # Parse the JSON response
        try:
            location_data = json.loads(response_text)
            
            if "error" in location_data:
                logger.warning(f"❌ Groq couldn't determine location for {animal_name}")
                return None
            
            # Extract coordinates
            coords = location_data.get("coordinates", {})
            if coords and "lat" in coords and "lng" in coords:
                region = location_data.get("region", "")
                country = location_data.get("country", "")
                continent = location_data.get("continent", "")
                
                place_description = f"{region}"
                if country:
                    place_description += f", {country}"
                if continent:
                    place_description += f", {continent}"
                place_description += " (typical habitat from AI)"
                
                logger.info(f"✅ Found Groq location for {animal_name}: {place_description}")
                
                return {
                    "latitude": coords["lat"],
                    "longitude": coords["lng"],
                    "location_string": region,
                    "place_guess": place_description
                }
            
        except json.JSONDecodeError:
            logger.error(f"❌ Invalid JSON response from Groq for {animal_name}: {response_text}")
            return None
        
        logger.warning(f"❌ No valid coordinates from Groq for {animal_name}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error using Groq for {animal_name}: {e}")
        return None

def search_inaturalist_for_location(animal_name, category=None):
    """
    Search iNaturalist for location data for a specific animal with multiple fallbacks
    
    Args:
        animal_name: Name of the animal to search for
        category: Optional category filter
    
    Returns:
        dict: Location data or None if not found
    """
    # First try iNaturalist
    logger.info(f"🔍 Searching iNaturalist for {animal_name}...")
    inaturalist_result = search_inaturalist_api(animal_name, category)
    if inaturalist_result:
        return inaturalist_result
    
    # If iNaturalist fails, try Wikipedia
    logger.info(f"🔍 Searching Wikipedia for {animal_name}...")
    wikipedia_result = get_location_from_wikipedia(animal_name)
    if wikipedia_result:
        return wikipedia_result
    
    # If Wikipedia fails, try Groq AI
    logger.info(f"🔍 Using Groq AI for {animal_name}...")
    groq_result = get_location_from_groq(animal_name, category)
    if groq_result:
        return groq_result
    
    logger.warning(f"❌ No location data found for {animal_name} from any source")
    return None

def search_inaturalist_api(animal_name, category=None):
    """
    Search iNaturalist API for location data for a specific animal
    
    Args:
        animal_name: Name of the animal to search for
        category: Optional category filter
    
    Returns:
        dict: Location data or None if not found
    """
    try:
        # Build search parameters
        params = {
            "quality_grade": "research",
            "has_photo": "true",
            "per_page": 5,  # Get a few results to find best match
            "order": "desc",
            "order_by": "created_at"
        }
        
        # Try multiple search strategies
        search_queries = [
            animal_name,  # Exact name
            animal_name.replace(" ", "+"),  # Space to plus
            f'"{animal_name}"'  # Quoted exact match
        ]
        
        if category:
            # Add category-based searches
            iconic_taxa_map = {
                'Bird': 'Aves',
                'Mammal': 'Mammalia', 
                'Reptile': 'Reptilia',
                'Amphibian': 'Amphibia',
                'Fish': 'Actinopterygii',
                'Insect': 'Insecta'
            }
            if category in iconic_taxa_map:
                search_queries.append(f"{animal_name}+{iconic_taxa_map[category]}")
        
        for query in search_queries:
            try:
                params["q"] = query
                
                logger.info(f"Searching iNaturalist for: {query}")
                url = "https://api.inaturalist.org/v1/observations"
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                observations = data.get("results", [])
                
                logger.info(f"Found {len(observations)} observations for query: {query}")
                
                # Look for observations with location data
                for observation in observations:
                    taxon = observation.get("taxon", {})
                    common_name = taxon.get("preferred_common_name", "")
                    
                    # Check if this matches our animal (case-insensitive)
                    if (common_name.lower() == animal_name.lower() or 
                        animal_name.lower() in common_name.lower()):
                        
                        # Extract location data
                        geojson = observation.get("geojson", {})
                        coordinates = geojson.get("coordinates", []) if geojson else []
                        
                        if len(coordinates) >= 2:
                            location_data = {
                                "latitude": coordinates[1],
                                "longitude": coordinates[0],
                                "location_string": observation.get("location", ""),
                                "place_guess": observation.get("place_guess", ""),
                                "observation_id": observation.get("id"),
                                "matched_name": common_name
                            }
                            
                            logger.info(f"✅ Found iNaturalist location for {animal_name}: {location_data['place_guess']}")
                            return location_data
                
                # Small delay between queries
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error with query '{query}': {e}")
                continue
        
        logger.warning(f"❌ No location data found for {animal_name} in iNaturalist")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error searching iNaturalist for {animal_name}: {e}")
        return None

def update_animal_location_in_db(animal_id, location_data):
    """
    Update an animal record with location data
    
    Args:
        animal_id: Database ID of the animal
        location_data: Dict containing latitude, longitude, location_string, place_guess
    
    Returns:
        bool: Success status
    """
    conn = get_snowflake_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE animal_insight_data 
            SET 
                latitude = %s,
                longitude = %s,
                location_string = %s,
                place_guess = %s
            WHERE id = %s
        """, (
            location_data.get('latitude'),
            location_data.get('longitude'),
            location_data.get('location_string', ''),
            location_data.get('place_guess', ''),
            animal_id
        ))
        
        cursor.close()
        logger.info(f"✅ Updated location for animal ID {animal_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating animal ID {animal_id}: {e}")
        return False
    finally:
        conn.close()
    """
    Update an animal record with location data
    
    Args:
        animal_id: Database ID of the animal
        location_data: Dict containing latitude, longitude, location_string, place_guess
    
    Returns:
        bool: Success status
    """
    conn = get_snowflake_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE animal_insight_data 
            SET 
                latitude = %s,
                longitude = %s,
                location_string = %s,
                place_guess = %s
            WHERE id = %s
        """, (
            location_data.get('latitude'),
            location_data.get('longitude'),
            location_data.get('location_string', ''),
            location_data.get('place_guess', ''),
            animal_id
        ))
        
        cursor.close()
        logger.info(f"✅ Updated location for animal ID {animal_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating animal ID {animal_id}: {e}")
        return False
    finally:
        conn.close()

def update_existing_animals_with_location():
    """
    Main function to update all existing animals with location data
    """
    print("Starting location update for existing animals...")
    print("=" * 60)
    
    # Fetch existing data
    df = fetch_dashboard_data()
    
    if df.empty:
        print("❌ No animals found in database")
        return
    
    # Check which animals need location updates
    lat_col = 'LATITUDE' if 'LATITUDE' in df.columns else 'latitude'
    lng_col = 'LONGITUDE' if 'LONGITUDE' in df.columns else 'longitude'
    
    if lat_col not in df.columns or lng_col not in df.columns:
        print("❌ Location columns not found. Please run add_location_columns.py first")
        return
    
    # Find animals without location data
    animals_without_location = df[df[lat_col].isna() | df[lng_col].isna()]
    animals_with_location = df[df[lat_col].notna() & df[lng_col].notna()]
    
    print(f"📊 Database Status:")
    print(f"   Total animals: {len(df)}")
    print(f"   With location: {len(animals_with_location)}")
    print(f"   Without location: {len(animals_without_location)}")
    print(f"   Need updates: {len(animals_without_location)}")
    
    if len(animals_without_location) == 0:
        print("🎉 All animals already have location data!")
        return
    
    # Ask user for confirmation
    response = input(f"\n🔄 Update location data for {len(animals_without_location)} animals? (y/n): ")
    if response.lower() != 'y':
        print("❌ Update cancelled")
        return
    
    print(f"\n🚀 Starting location updates...")
    
    # Process each animal
    success_count = 0
    error_count = 0
    not_found_count = 0
    
    name_col = 'NAME' if 'NAME' in df.columns else 'name'
    category_col = 'CATEGORY' if 'CATEGORY' in df.columns else 'category'
    id_col = 'ID' if 'ID' in df.columns else 'id'
    
    for idx, (_, animal) in enumerate(animals_without_location.iterrows()):
        animal_name = animal.get(name_col, 'Unknown')
        animal_category = animal.get(category_col, '')
        animal_id = animal.get(id_col)
        
        print(f"\n[{idx+1}/{len(animals_without_location)}] Processing: {animal_name}")
        
        # Search for location data
        location_data = search_inaturalist_for_location(animal_name, animal_category)
        
        if location_data:
            # Update database
            if update_animal_location_in_db(animal_id, location_data):
                success_count += 1
                place = location_data.get('place_guess', 'Unknown location')
                print(f"   ✅ Updated with location: {place}")
            else:
                error_count += 1
                print(f"   ❌ Database update failed")
        else:
            not_found_count += 1
            print(f"   ⚠️  No location data found")
        
        # Progress update every 10 animals
        if (idx + 1) % 10 == 0:
            print(f"\n📈 Progress: {idx+1}/{len(animals_without_location)} processed")
            print(f"   ✅ Success: {success_count}, ❌ Errors: {error_count}, ⚠️  Not found: {not_found_count}")
        
        # Rate limiting - be respectful to iNaturalist API
        time.sleep(1.5)
    
    # Final summary
    print(f"\n🎉 Location update completed!")
    print(f"=" * 60)
    print(f"📊 Final Results:")
    print(f"   ✅ Successfully updated: {success_count}")
    print(f"   ❌ Database errors: {error_count}")
    print(f"   ⚠️  No location found: {not_found_count}")
    print(f"   📍 Total processed: {len(animals_without_location)}")
    
    if success_count > 0:
        print(f"\n🗺️  Your animals now have enhanced location data!")
        print(f"   • GPS coordinates for precise mapping")
        print(f"   • Place names for context") 
        print(f"   • Enhanced map visualizations")
        print(f"\n💡 Refresh your dashboard to see the new GPS-based maps!")

def verify_location_updates():
    """
    Verify the location updates were successful
    """
    print("\n🔍 Verifying location updates...")
    
    df = fetch_dashboard_data()
    if df.empty:
        print("❌ No data found")
        return
    
    lat_col = 'LATITUDE' if 'LATITUDE' in df.columns else 'latitude'
    lng_col = 'LONGITUDE' if 'LONGITUDE' in df.columns else 'longitude'
    
    if lat_col in df.columns and lng_col in df.columns:
        animals_with_location = df[df[lat_col].notna() & df[lng_col].notna()]
        animals_without_location = df[df[lat_col].isna() | df[lng_col].isna()]
        
        print(f"📊 Updated Database Status:")
        print(f"   Total animals: {len(df)}")
        print(f"   With location: {len(animals_with_location)} ({len(animals_with_location)/len(df)*100:.1f}%)")
        print(f"   Without location: {len(animals_without_location)} ({len(animals_without_location)/len(df)*100:.1f}%)")
        
        if len(animals_with_location) > 0:
            print(f"\n🌍 Sample locations:")
            for _, animal in animals_with_location.head(3).iterrows():
                name = animal.get('NAME', animal.get('name', 'Unknown'))
                lat = animal.get(lat_col)
                lng = animal.get(lng_col)
                place = animal.get('PLACE_GUESS', animal.get('place_guess', ''))
                print(f"   📍 {name}: {lat:.4f}, {lng:.4f} ({place})")
    else:
        print("❌ Location columns not found")

def main():
    """Main execution function"""
    try:
        # Step 1: Update locations
        update_existing_animals_with_location()
        
        # Step 2: Verify updates
        verify_location_updates()
        
        print(f"\nNext Steps:")
        print(f"   1. Refresh your NatureTrace dashboard")
        print(f"   2. View the enhanced GPS-based maps")
        print(f"   3. Explore individual animal location profiles")
        
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Update cancelled by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
