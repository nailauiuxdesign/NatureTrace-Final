# utils/data_utils.py

import snowflake.connector
import pandas as pd
from datetime import datetime
import streamlit as st
import logging

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
        # Try to create table with all columns including new ones
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

def save_to_snowflake(filename, name, description, facts, sound_url="", category=None, inatural_pic=None, wikipedia_url=None, original_image=None, species=None, summary=None, fetch_sound=True):
    """
    Save animal data to Snowflake (legacy function - now calls enhanced version)
    
    Args:
        fetch_sound: If True, automatically fetches sound for the animal
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
        fetch_sound=fetch_sound
    )

def save_inaturalist_data_to_snowflake(data_record):
    """Save iNaturalist and Wikipedia combined data to Snowflake"""
    conn = get_snowflake_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO animal_insight_data (
                filename, name, description, facts, sound_url, 
                category, inatural_pic, wikipedia_url, original_image, species, summary
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            data_record.get('summary', '')
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
            cursor.execute("""
                UPDATE animal_insight_data 
                SET sound_url = %s, sound_source = %s, sound_updated = CURRENT_TIMESTAMP()
                WHERE id = %s
            """, (sound_url, source, animal_id))
        else:
            cursor.execute("""
                UPDATE animal_insight_data 
                SET sound_url = %s, sound_source = %s, sound_updated = CURRENT_TIMESTAMP()
                WHERE UPPER(name) = UPPER(%s)
            """, (sound_url, source, animal_name))
        
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

def save_to_snowflake_with_sound(filename, name, description, facts, category=None, inatural_pic=None, wikipedia_url=None, original_image=None, species=None, summary=None, fetch_sound=True):
    """
    Save animal data to Snowflake and automatically fetch sound if requested
    
    Args:
        All the standard save_to_snowflake parameters plus:
        fetch_sound: Boolean to determine if sound should be automatically fetched
        
    Returns:
        dict: {"success": bool, "animal_id": int, "sound_result": dict}
    """
    # Ensure table exists first
    if not create_table_if_not_exists():
        return {"success": False, "animal_id": None, "sound_result": None}
    
    conn = get_snowflake_connection()
    if not conn:
        return {"success": False, "animal_id": None, "sound_result": None}
    
    try:
        cursor = conn.cursor()
        
        # Insert the animal data first (without sound_url initially)
        cursor.execute("""
            INSERT INTO animal_insight_data (filename, name, description, facts, sound_url, category, inatural_pic, wikipedia_url, original_image, species, summary)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (filename, name, description, facts, "", category, inatural_pic, wikipedia_url, original_image, species, summary))
        
        # Get the inserted animal's ID using Snowflake syntax
        cursor.execute("SELECT id FROM animal_insight_data WHERE filename = %s ORDER BY timestamp DESC LIMIT 1", (filename,))
        result = cursor.fetchone()
        animal_id = result[0] if result else None
        cursor.close()
        
        # Fetch and update sound if requested
        sound_result = None
        if fetch_sound and name:
            sound_result = update_animal_sound_url(animal_id=animal_id, animal_name=name)
        
        return {
            "success": True,
            "animal_id": animal_id,
            "sound_result": sound_result
        }
        
    except Exception as e:
        logger.error(f"Error inserting into Snowflake with sound: {e}")
        return {"success": False, "animal_id": None, "sound_result": None}
    finally:
        conn.close()
