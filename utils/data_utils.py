# utils/data_utils.py

import snowflake.connector
import pandas as pd
from datetime import datetime
import streamlit as st
import logging
import requests
import json
import re
import time
from groq import Groq

# Enable detailed logging for Snowflake connections
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_snowflake_connection():
    try:
        # Connect with FLORA0122 using ANIMAL_APP_ROLE
        conn = snowflake.connector.connect(
            user=st.secrets["snowflake_user"],
            password=st.secrets["snowflake_password"],
            account=st.secrets["snowflake_account"],
            warehouse=st.secrets["snowflake_warehouse"],
            role=st.secrets["snowflake_role"],
            autocommit=True
        )
        
        logger.info("Successfully connected to Snowflake")
        
        # Explicitly set the database and schema context
        cursor = conn.cursor()
        cursor.execute(f"USE DATABASE {st.secrets['snowflake_database']}")
        cursor.execute(f"USE SCHEMA {st.secrets['snowflake_schema']}")
        cursor.close()
        
        return conn
    except KeyError as e:
        st.error(f"Missing Snowflake configuration key: {e}. Please check secrets.toml")
        logger.error(f"Missing configuration: {e}")
        return None
    except snowflake.connector.errors.DatabaseError as e:
        st.error(f"Snowflake database error: {e}")
        logger.error(f"Database error: {e}")
        return None
    except Exception as e:
        st.error(f"Snowflake connection failed: {e}")
        logger.error(f"Connection failed: {e}")
        return None


def create_table_if_not_exists():
    """Create the animal_insight_data table if it doesn't exist"""
    conn = get_snowflake_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        # Try to create table with all columns including new location fields
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS animal_insight_data (
                id INTEGER AUTOINCREMENT PRIMARY KEY,
                filename VARCHAR(255) UNIQUE,
                name VARCHAR(255),
                description TEXT,
                facts TEXT,
                sound_url VARCHAR(500),
                sound_source VARCHAR(100),
                sound_updated TIMESTAMP,
                category VARCHAR(255),
                inatural_pic VARCHAR(500),
                wikipedia_url VARCHAR(500),
                original_image VARCHAR(500),
                species TEXT,
                summary TEXT,
                latitude FLOAT,
                longitude FLOAT,
                location_string VARCHAR(500),
                place_guess VARCHAR(500),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
            )
        """)
        cursor.close()
        return True
    except Exception as e:
        # If table creation fails, just log and continue - table might already exist
        print(f"Note: Table creation attempt: {e}")
        return True  # Return True to continue with the app
    finally:
        conn.close()

def save_to_snowflake(filename, name, description, facts, sound_url="", category=None, inatural_pic=None, wikipedia_url=None, original_image=None, species=None, summary=None, fetch_sound=True, fetch_location=True):
    """
    Save animal data to Snowflake (enhanced version with auto-location and sound fetching)
    
    Args:
        fetch_sound: If True, automatically fetches sound for the animal
        fetch_location: If True, automatically fetches location for the animal
    """
    return save_to_snowflake_with_sound(
        filename=filename,
        name=name, 
        description=description,
        facts=facts,
        category=category,
        inatural_pic=inatural_pic,
        wikipedia_url=wikipedia_url,
        original_image=original_image,
        species=species,
        summary=summary,
        fetch_sound=fetch_sound,
        fetch_location=fetch_location
    )

def save_inaturalist_data_to_snowflake(data_record):
    """Save iNaturalist and Wikipedia combined data to Snowflake with location data"""
    conn = get_snowflake_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO animal_insight_data (
                filename, name, description, facts, sound_url, 
                category, inatural_pic, wikipedia_url, original_image, species, summary,
                latitude, longitude, location_string, place_guess
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data_record.get('filename', ''),
            data_record.get('name', ''),
            data_record.get('description', ''),
            data_record.get('facts', ''),
            data_record.get('sound_url', ''),
            data_record.get('category', ''),
            data_record.get('inatural_pic', ''),
            data_record.get('wikipedia_url', ''),
            data_record.get('original_image', ''),
            data_record.get('species', ''),
            data_record.get('summary', ''),
            data_record.get('latitude'),
            data_record.get('longitude'),
            data_record.get('location_string', ''),
            data_record.get('place_guess', '')
        ))
        cursor.close()
        return True
    except Exception as e:
        print(f"Error inserting iNaturalist data into Snowflake: {e}")
        return False
    finally:
        conn.close()

def fetch_dashboard_data():
    conn = get_snowflake_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        # First try to query the table
        df = pd.read_sql("SELECT * FROM animal_insight_data ORDER BY timestamp DESC", conn)
        return df
    except Exception as e:
        # If table doesn't exist, try to create it
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE animal_insight_data (
                    id INTEGER AUTOINCREMENT PRIMARY KEY,
                    filename VARCHAR(255) UNIQUE,
                    name VARCHAR(255),
                    description TEXT,
                    facts TEXT,
                    sound_url VARCHAR(500),
                    category VARCHAR(255),
                    inatural_pic VARCHAR(500),
                    wikipedia_url VARCHAR(500),
                    original_image VARCHAR(500),
                    species TEXT,
                    summary TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
                )
            """)
            cursor.close()
            # Try querying again after creating table
            df = pd.read_sql("SELECT * FROM animal_insight_data ORDER BY timestamp DESC", conn)
            return df
        except Exception as create_error:
            st.error(f"Table doesn't exist and cannot be created. Please contact your Snowflake administrator to create the 'animal_insight_data' table in the ANIMAL_DB.INSIGHTS schema.")
            return pd.DataFrame()
    finally:
        conn.close()

def update_animal_sound_url(animal_id=None, animal_name=None, sound_url=None, source=None):
    """
    Update or fetch and save sound URL for an animal in the database
    
    Args:
        animal_id: Database ID of the animal (optional if animal_name provided)
        animal_name: Name of the animal (optional if animal_id provided)
        sound_url: Direct sound URL to save (optional - will fetch if not provided)
        source: Source of the sound (optional - will be detected if fetching)
    
    Returns:
        dict: {"success": bool, "sound_url": str, "source": str, "message": str}
    """
    conn = get_snowflake_connection()
    if not conn:
        return {"success": False, "sound_url": None, "source": None, "message": "Database connection failed"}
    
    try:
        cursor = conn.cursor()
        
        # Get animal information if not provided
        if animal_id and not animal_name:
            cursor.execute("SELECT name, category FROM animal_insight_data WHERE id = %s", (animal_id,))
            result = cursor.fetchone()
            if result:
                animal_name, animal_type = result
            else:
                return {"success": False, "sound_url": None, "source": None, "message": f"Animal with ID {animal_id} not found"}
        elif animal_name and not animal_id:
            cursor.execute("SELECT id, category FROM animal_insight_data WHERE UPPER(name) = UPPER(%s) LIMIT 1", (animal_name,))
            result = cursor.fetchone()
            if result:
                animal_id, animal_type = result
            else:
                animal_type = "unknown"
        
        # If no sound URL provided, fetch one
        if not sound_url:
            try:
                from utils.sound_utils import sound_fetcher
                logger.info(f"Fetching sound for {animal_name} (type: {animal_type if 'animal_type' in locals() else 'unknown'})")
                
                # Use the enhanced sound fetcher
                fetched_url = sound_fetcher.fetch_sound(
                    animal_name, 
                    max_duration=30, 
                    animal_type=animal_type if 'animal_type' in locals() else "unknown"
                )
                
                if fetched_url:
                    sound_url = fetched_url
                    # Determine source from URL
                    if 'xeno-canto.org' in sound_url:
                        source = 'xeno_canto'
                    elif 'static.inaturalist.org' in sound_url:
                        source = 'inaturalist'
                    elif 'cdn.download.ams.birds.cornell.edu' in sound_url:
                        source = 'macaulay'
                    elif 'huggingface.co' in sound_url:
                        source = 'huggingface'
                    elif 'archive.org' in sound_url:
                        source = 'internet_archive'
                    else:
                        source = 'unknown'
                else:
                    return {"success": False, "sound_url": None, "source": None, "message": f"No sound found for {animal_name}"}
                    
            except Exception as e:
                return {"success": False, "sound_url": None, "source": None, "message": f"Error fetching sound: {str(e)}"}
        
        # Update the database with the sound URL
        if animal_id:
            # Try to update with new columns first, fallback to old structure
            try:
                cursor.execute("""
                    UPDATE animal_insight_data 
                    SET sound_url = %s, sound_source = %s, sound_updated = CURRENT_TIMESTAMP()
                    WHERE id = %s
                """, (sound_url, source, animal_id))
            except:
                # Fallback to basic update if new columns don't exist
                cursor.execute("""
                    UPDATE animal_insight_data 
                    SET sound_url = %s
                    WHERE id = %s
                """, (sound_url, animal_id))
        else:
            # Try to update with new columns first, fallback to old structure
            try:
                cursor.execute("""
                    UPDATE animal_insight_data 
                    SET sound_url = %s, sound_source = %s, sound_updated = CURRENT_TIMESTAMP()
                    WHERE UPPER(name) = UPPER(%s)
                """, (sound_url, source, animal_name))
            except:
                # Fallback to basic update if new columns don't exist
                cursor.execute("""
                    UPDATE animal_insight_data 
                    SET sound_url = %s
                    WHERE UPPER(name) = UPPER(%s)
                """, (sound_url, animal_name))
        
        affected_rows = cursor.rowcount
        cursor.close()
        
        if affected_rows > 0:
            return {
                "success": True, 
                "sound_url": sound_url, 
                "source": source, 
                "message": f"Sound URL updated successfully for {animal_name}"
            }
        else:
            return {
                "success": False, 
                "sound_url": None, 
                "source": None, 
                "message": f"No records updated - animal {animal_name} may not exist"
            }
            
    except Exception as e:
        return {"success": False, "sound_url": None, "source": None, "message": f"Database error: {str(e)}"}
    finally:
        conn.close()

def bulk_update_missing_sounds(limit=None):
    """
    Update sound URLs for all animals in the database that don't have sounds
    
    Args:
        limit: Maximum number of animals to process (None for all)
        
    Returns:
        dict: {"total_processed": int, "successful": int, "failed": int, "results": list}
    """
    conn = get_snowflake_connection()
    if not conn:
        return {"total_processed": 0, "successful": 0, "failed": 0, "results": []}
    
    try:
        cursor = conn.cursor()
        
        # Get animals without sound URLs
        query = """
            SELECT id, name, category 
            FROM animal_insight_data 
            WHERE sound_url IS NULL OR sound_url = '' 
            ORDER BY timestamp DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        animals = cursor.fetchall()
        cursor.close()
        
        results = []
        successful = 0
        failed = 0
        
        for animal_id, name, category in animals:
            logger.info(f"Processing sound for: {name} (ID: {animal_id})")
            
            result = update_animal_sound_url(
                animal_id=animal_id, 
                animal_name=name
            )
            
            results.append({
                "id": animal_id,
                "name": name,
                "success": result["success"],
                "sound_url": result["sound_url"],
                "source": result["source"],
                "message": result["message"]
            })
            
            if result["success"]:
                successful += 1
            else:
                failed += 1
                
        return {
            "total_processed": len(animals),
            "successful": successful,
            "failed": failed,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Bulk sound update error: {str(e)}")
        return {"total_processed": 0, "successful": 0, "failed": 0, "results": []}
    finally:
        conn.close()

def save_to_snowflake_with_sound(filename, name, description, facts, category=None, inatural_pic=None, wikipedia_url=None, original_image=None, species=None, summary=None, fetch_sound=True, fetch_location=True):
    """
    Save animal data to Snowflake and automatically fetch sound and location if requested
    
    Args:
        All the standard save_to_snowflake parameters plus:
        fetch_sound: Boolean to determine if sound should be automatically fetched
        fetch_location: Boolean to determine if location should be automatically fetched
        
    Returns:
        dict: {"success": bool, "animal_id": int, "sound_result": dict, "location_result": dict}
    """
    # Ensure table exists first
    if not create_table_if_not_exists():
        return {"success": False, "animal_id": None, "sound_result": None, "location_result": None}
    
    # Fetch location data first if requested
    location_data = None
    location_result = {"success": False, "source": None}
    
    if fetch_location and name:
        logger.info(f"Fetching location data for {name}...")
        location_data = fetch_location_for_animal(name, category)
        if location_data:
            location_result = {
                "success": True, 
                "source": location_data.get("source", "Unknown"),
                "location": location_data.get("place_guess", "Unknown location")
            }
            logger.info(f"Found location for {name}: {location_data.get('place_guess', 'coordinates only')}")
        else:
            logger.warning(f"No location data found for {name}")
    
    conn = get_snowflake_connection()
    if not conn:
        return {"success": False, "animal_id": None, "sound_result": None, "location_result": location_result}
    
    try:
        cursor = conn.cursor()
        
        # Insert the animal data with location if available
        if location_data:
            cursor.execute("""
                INSERT INTO animal_insight_data (
                    filename, name, description, facts, sound_url, category, 
                    inatural_pic, wikipedia_url, original_image, species, summary,
                    latitude, longitude, location_string, place_guess
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                filename, name, description, facts, "", category, 
                inatural_pic, wikipedia_url, original_image, species, summary,
                location_data.get('latitude'), location_data.get('longitude'),
                location_data.get('location_string', ''), location_data.get('place_guess', '')
            ))
        else:
            # Insert without location data
            cursor.execute("""
                INSERT INTO animal_insight_data (filename, name, description, facts, sound_url, category, inatural_pic, wikipedia_url, original_image, species, summary)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (filename, name, description, facts, "", category, inatural_pic, wikipedia_url, original_image, species, summary))
        
        # Get the inserted animal's ID using Snowflake syntax
        cursor.execute("SELECT id FROM animal_insight_data WHERE filename = %s ORDER BY timestamp DESC LIMIT 1", (filename,))
        result = cursor.fetchone()
        animal_id = result[0] if result else None
        cursor.close()
        
        # Fetch and update sound if requested using enhanced logic
        sound_result = None
        if fetch_sound and name:
            logger.info(f"� Fetching enhanced sound for {name}...")
            sound_result = update_animal_sound_enhanced(
                animal_id=animal_id, 
                animal_name=name,
                sound_url=None,  # Let it fetch automatically
                source=None,     # Let it determine source
                processed=False  # Will be determined by the function
            )
        
        return {
            "success": True,
            "animal_id": animal_id,
            "sound_result": sound_result,
            "location_result": location_result
        }
        
    except Exception as e:
        logger.error(f"Error inserting into Snowflake with enhancements: {e}")
        return {"success": False, "animal_id": None, "sound_result": None, "location_result": location_result}
    finally:
        conn.close()

def get_animal_database_knowledge():
    """
    Fetch all animal data from Snowflake to create a knowledge base for image recognition
    Returns: Dictionary with animal names as keys and their details as values
    """
    conn = get_snowflake_connection()
    if not conn:
        logger.warning("Could not connect to Snowflake for animal knowledge base")
        return {}
    
    try:
        cursor = conn.cursor()
        # Fetch all animal data with image URLs and descriptions
        query = """
            SELECT DISTINCT 
                UPPER(TRIM(name)) as animal_name,
                description,
                inatural_pic,
                original_image,
                species,
                summary,
                category,
                facts
            FROM animal_insight_data 
            WHERE name IS NOT NULL 
            AND TRIM(name) != ''
            ORDER BY animal_name
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        animal_knowledge = {}
        
        for row in results:
            animal_name, description, inatural_pic, original_image, species, summary, category, facts = row
            
            # Create variations of the animal name for better matching
            base_name = animal_name.lower()
            name_variations = [
                base_name,
                base_name.replace(" ", ""),
                base_name.replace("-", " "),
                base_name.replace("_", " "),
            ]
            
            # Also add individual words for partial matching
            words = base_name.split()
            name_variations.extend(words)
            
            animal_data = {
                'name': animal_name,
                'description': description or '',
                'inatural_pic': inatural_pic or '',
                'original_image': original_image or '',
                'species': species or '',
                'summary': summary or '',
                'category': category or 'Unknown',
                'facts': facts or '',
                'name_variations': name_variations
            }
            
            # Store by primary name and all variations
            animal_knowledge[base_name] = animal_data
            for variation in name_variations:
                if variation and len(variation) > 2:  # Skip very short variations
                    animal_knowledge[variation] = animal_data
        
        logger.info(f"Loaded knowledge for {len(set([v['name'] for v in animal_knowledge.values()]))} unique animals from database")
        return animal_knowledge
        
    except Exception as e:
        logger.error(f"Error fetching animal knowledge from database: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()

def match_detected_animal_to_database(detected_animal, confidence, animal_knowledge):
    """
    Match YOLO detected animal to database knowledge for enhanced accuracy
    Args:
        detected_animal: Animal name from YOLO
        confidence: YOLO confidence score
        animal_knowledge: Database knowledge dictionary
    Returns:
        tuple: (matched_animal_data, enhanced_confidence, match_type)
    """
    if not animal_knowledge:
        return None, confidence, "no_database"
    
    detected_lower = detected_animal.lower().strip()
    
    # Direct exact match
    if detected_lower in animal_knowledge:
        match_data = animal_knowledge[detected_lower]
        enhanced_confidence = min(0.95, confidence + 0.15)  # Boost confidence for exact match
        logger.info(f"Exact database match: {detected_animal} -> {match_data['name']}")
        return match_data, enhanced_confidence, "exact_match"
    
    # Partial word matching
    detected_words = detected_lower.split()
    best_match = None
    best_score = 0
    
    for animal_key, animal_data in animal_knowledge.items():
        # Check if any word from detected animal matches any variation
        for detected_word in detected_words:
            if len(detected_word) > 2:  # Skip very short words
                for variation in animal_data['name_variations']:
                    if detected_word in variation or variation in detected_word:
                        # Calculate match score based on word length and position
                        score = len(detected_word) / len(variation) if variation else 0
                        if score > best_score:
                            best_score = score
                            best_match = animal_data
    
    if best_match and best_score > 0.3:  # Minimum match threshold
        enhanced_confidence = min(0.85, confidence + (best_score * 0.2))
        logger.info(f"� Partial database match: {detected_animal} -> {best_match['name']} (score: {best_score:.2f})")
        return best_match, enhanced_confidence, "partial_match"
    
    # Category-based fallback matching
    detected_category = None
    if detected_lower in ['cat', 'dog', 'bird', 'horse', 'cow', 'sheep', 'elephant', 'bear', 'zebra', 'giraffe']:
        # Look for animals in the same YOLO category
        for animal_data in animal_knowledge.values():
            if animal_data.get('category', '').lower() == 'mammal' and detected_lower in ['cat', 'dog', 'horse', 'cow', 'sheep', 'elephant', 'bear', 'zebra', 'giraffe']:
                # Could potentially match - but keep original detection
                pass
    
    return None, confidence, "no_match"

def get_enhanced_animal_description(animal_data, detected_confidence):
    """
    Create enhanced description using database knowledge
    Args:
        animal_data: Matched animal data from database
        detected_confidence: Detection confidence
    Returns:
        tuple: (enhanced_name, enhanced_description, category)
    """
    if not animal_data:
        return None, None, None
    
    name = animal_data['name']
    category = animal_data.get('category', 'Unknown')
    
    # Build comprehensive description from available data
    description_parts = []
    
    if animal_data.get('description'):
        description_parts.append(animal_data['description'])
    
    if animal_data.get('species'):
        description_parts.append(f"Species info: {animal_data['species']}")
    
    if animal_data.get('summary'):
        # Take first 200 characters of summary
        summary_excerpt = animal_data['summary'][:200] + "..." if len(animal_data['summary']) > 200 else animal_data['summary']
        description_parts.append(summary_excerpt)
    
    if animal_data.get('facts'):
        facts_excerpt = animal_data['facts'][:150] + "..." if len(animal_data['facts']) > 150 else animal_data['facts']
        description_parts.append(f"Additional info: {facts_excerpt}")
    
    enhanced_description = " | ".join(description_parts) if description_parts else f"A {category.lower()} species identified using database knowledge."
    enhanced_description += f" (Detected with {detected_confidence:.1%} confidence using enhanced AI analysis)"
    
    return name, enhanced_description, category

def search_inaturalist_for_location(animal_name, category=None):
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
            "per_page": 3,  # Get a few results to find best match
            "order": "desc",
            "order_by": "created_at"
        }
        
        # Try multiple search strategies
        search_queries = [animal_name, animal_name.replace(" ", "+")]
        
        for query in search_queries:
            try:
                params["q"] = query
                
                logger.info(f"Searching iNaturalist for: {query}")
                url = "https://api.inaturalist.org/v1/observations"
                response = requests.get(url, params=params, timeout=20)
                response.raise_for_status()
                
                data = response.json()
                observations = data.get("results", [])
                
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
                                "place_guess": observation.get("place_guess", "") + " (iNaturalist)",
                                "source": "iNaturalist"
                            }
                            
                            logger.info(f"Found iNaturalist location for {animal_name}")
                            return location_data
                
                # Small delay between queries
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error with iNaturalist query '{query}': {e}")
                continue
        
        logger.warning(f"No location data found for {animal_name} in iNaturalist")
        return None
        
    except Exception as e:
        logger.error(f"Error searching iNaturalist for {animal_name}: {e}")
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
                r'occurs in ([^.]+)',
                r'inhabits ([^.]+)'
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
                        logger.info(f"Found Wikipedia location for {animal_name}: {location_text}")
                        return {
                            "latitude": coords['lat'],
                            "longitude": coords['lng'],
                            "location_string": location_text,
                            "place_guess": f"{location_text} (Wikipedia)",
                            "source": "Wikipedia"
                        }
            
        logger.warning(f"No location data found for {animal_name} in Wikipedia")
        return None
        
    except Exception as e:
        logger.error(f"Error searching Wikipedia for {animal_name}: {e}")
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
        # Check if Groq API key is available
        groq_key = st.secrets.get("groq_api_key")
        if not groq_key:
            logger.warning("Groq API key not found in secrets")
            return None
        
        # Initialize Groq client
        client = Groq(api_key=groq_key)
        
        # Create a prompt to get location information
        category_info = f" (a {category})" if category else ""
        prompt = f"""
For the animal "{animal_name}"{category_info}, provide the primary geographic region where this species is typically found.

Respond with ONLY a JSON object in this exact format:
{{
    "region": "specific geographic region name",
    "country": "primary country if applicable",
    "coordinates": {{"lat": latitude_number, "lng": longitude_number}}
}}

If you cannot determine a specific location, respond with: {{"error": "unknown"}}

Examples:
- For "African Elephant": {{"region": "Sub-Saharan Africa", "country": "Kenya", "coordinates": {{"lat": -1.2921, "lng": 36.8219}}}}
- For "Bald Eagle": {{"region": "North America", "country": "United States", "coordinates": {{"lat": 39.8283, "lng": -98.5795}}}}
"""

        # Make the API call
        chat_completion = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": prompt
            }],
            model="llama3-8b-8192",
            temperature=0.1,
            max_tokens=150
        )
        
        response_text = chat_completion.choices[0].message.content.strip()
        
        # Parse the JSON response
        try:
            location_data = json.loads(response_text)
            
            if "error" in location_data:
                logger.warning(f"Groq couldn't determine location for {animal_name}")
                return None
            
            # Extract coordinates
            coords = location_data.get("coordinates", {})
            if coords and "lat" in coords and "lng" in coords:
                region = location_data.get("region", "")
                country = location_data.get("country", "")
                
                place_description = f"{region}"
                if country:
                    place_description += f", {country}"
                place_description += " (AI habitat)"
                
                logger.info(f"Found Groq location for {animal_name}")
                
                return {
                    "latitude": coords["lat"],
                    "longitude": coords["lng"],
                    "location_string": region,
                    "place_guess": place_description,
                    "source": "Groq AI"
                }
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response from Groq for {animal_name}")
            return None
        
        logger.warning(f"No valid coordinates from Groq for {animal_name}")
        return None
        
    except Exception as e:
        logger.error(f"Error using Groq for {animal_name}: {e}")
        return None

def fetch_location_for_animal(animal_name, category=None):
    """
    Fetch location data using multiple sources with fallbacks
    
    Args:
        animal_name: Name of the animal to search for
        category: Optional category filter
    
    Returns:
        dict: Location data or None if not found from any source
    """
    # First try iNaturalist (most reliable for actual sightings)
    logger.info(f"� [1/3] Searching iNaturalist for {animal_name}...")
    inaturalist_result = search_inaturalist_for_location(animal_name, category)
    if inaturalist_result:
        return inaturalist_result
    
    # If iNaturalist fails, try Wikipedia (good for general habitat info)
    logger.info(f"� [2/3] Searching Wikipedia for {animal_name}...")
    wikipedia_result = get_location_from_wikipedia(animal_name)
    if wikipedia_result:
        return wikipedia_result
    
    # If Wikipedia fails, try Groq AI (AI-generated typical habitat)
    logger.info(f"� [3/3] Using Groq AI for {animal_name}...")
    groq_result = get_location_from_groq(animal_name, category)
    if groq_result:
        return groq_result
    
    logger.warning(f"No location data found for {animal_name} from any source")
    return None

def ensure_sound_columns_exist():
    """Ensure that sound_source and sound_updated columns exist in the database"""
    conn = get_snowflake_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if columns exist
        cursor.execute("DESCRIBE TABLE animal_insight_data")
        columns = [row[0] for row in cursor.fetchall()]
        
        # Add missing columns
        if 'SOUND_SOURCE' not in columns:
            logger.info("Adding SOUND_SOURCE column...")
            cursor.execute("ALTER TABLE animal_insight_data ADD COLUMN sound_source VARCHAR(100)")
        
        if 'SOUND_UPDATED' not in columns:
            logger.info("Adding SOUND_UPDATED column...")
            cursor.execute("ALTER TABLE animal_insight_data ADD COLUMN sound_updated TIMESTAMP")
        
        cursor.close()
        logger.info("Sound columns verified/added successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error ensuring sound columns: {e}")
        return False
    finally:
        conn.close()

def update_animal_sound_enhanced(animal_id=None, animal_name=None, sound_url=None, source=None, processed=False):
    """
    Enhanced version of update_animal_sound_url with better source tracking
    
    Args:
        animal_id: Database ID of the animal
        animal_name: Name of the animal
        sound_url: Sound URL to save
        source: Source of the sound (e.g., 'iNaturalist', 'xeno-canto')
        processed: Whether the sound was processed to remove speech
    
    Returns:
        dict: {"success": bool, "sound_url": str, "source": str, "message": str}
    """
    conn = get_snowflake_connection()
    if not conn:
        return {"success": False, "sound_url": None, "source": None, "message": "Database connection failed"}
    
    try:
        # Ensure sound columns exist
        ensure_sound_columns_exist()
        
        cursor = conn.cursor()
        
        # Get animal information if not provided
        if animal_id and not animal_name:
            cursor.execute("SELECT name, category FROM animal_insight_data WHERE id = %s", (animal_id,))
            result = cursor.fetchone()
            if result:
                animal_name, animal_type = result
            else:
                return {"success": False, "sound_url": None, "source": None, "message": f"Animal with ID {animal_id} not found"}
        elif animal_name and not animal_id:
            cursor.execute("SELECT id, category FROM animal_insight_data WHERE UPPER(name) = UPPER(%s) LIMIT 1", (animal_name,))
            result = cursor.fetchone()
            if result:
                animal_id, animal_type = result
            else:
                animal_type = "unknown"
        
        # If no sound URL provided, fetch one using enhanced logic
        if not sound_url:
            try:
                from utils.sound_utils import fetch_clean_animal_sound
                logger.info(f"Fetching enhanced sound for {animal_name} (type: {animal_type if 'animal_type' in locals() else 'unknown'})")
                
                # Use the enhanced sound fetcher with speech removal
                result = fetch_clean_animal_sound(
                    animal_name, 
                    animal_type if 'animal_type' in locals() else "unknown"
                )
                
                if result.get('success'):
                    sound_url = result.get('processed_url') or result.get('original_url')
                    source = result.get('source', 'Unknown')
                    if result.get('speech_removed'):
                        source += " (processed)"
                        processed = True
                else:
                    return {"success": False, "sound_url": None, "source": None, "message": f"No sound found for {animal_name}"}
                    
            except Exception as e:
                return {"success": False, "sound_url": None, "source": None, "message": f"Error fetching sound: {str(e)}"}
        
        # Enhance source name if processed
        enhanced_source = source
        if processed and " (processed)" not in source:
            enhanced_source += " (processed)"
        
        # Update the database with enhanced sound data
        if animal_id:
            cursor.execute("""
                UPDATE animal_insight_data 
                SET sound_url = %s, sound_source = %s, sound_updated = CURRENT_TIMESTAMP()
                WHERE id = %s
            """, (sound_url, enhanced_source, animal_id))
        else:
            cursor.execute("""
                UPDATE animal_insight_data 
                SET sound_url = %s, sound_source = %s, sound_updated = CURRENT_TIMESTAMP()
                WHERE UPPER(name) = UPPER(%s)
            """, (sound_url, enhanced_source, animal_name))
        
        affected_rows = cursor.rowcount
        cursor.close()
        
        if affected_rows > 0:
            return {
                "success": True, 
                "sound_url": sound_url, 
                "source": enhanced_source, 
                "message": f"Enhanced sound data updated for {animal_name}",
                "processed": processed
            }
        else:
            return {
                "success": False, 
                "sound_url": None, 
                "source": None, 
                "message": f"No records updated - animal {animal_name} may not exist"
            }
            
    except Exception as e:
        return {"success": False, "sound_url": None, "source": None, "message": f"Database error: {str(e)}"}
    finally:
        conn.close()
