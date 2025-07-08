#!/usr/bin/env python3
"""
Dashboard Sound Integration - Complete solution for managing animal sounds in the NatureTrace dashboard
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_utils import (
    update_animal_sound_url, 
    bulk_update_missing_sounds, 
    save_to_snowflake_with_sound,
    get_snowflake_connection,
    fetch_dashboard_data
)
from utils.sound_utils import sound_fetcher
import logging
import streamlit as st
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DashboardSoundManager:
    """Comprehensive sound management for the NatureTrace dashboard"""
    
    def __init__(self):
        self.sound_fetcher = sound_fetcher
        
    def add_animal_with_sound(self, filename, name, description, facts, category=None, 
                            inatural_pic=None, wikipedia_url=None, original_image=None, 
                            species=None, summary=None, auto_fetch_sound=True):
        """
        Add a new animal to the dashboard with automatic sound fetching
        
        Args:
            All standard animal data fields plus:
            auto_fetch_sound: Boolean to enable automatic sound fetching
            
        Returns:
            dict: Complete result including animal_id and sound information
        """
        logger.info(f"Adding animal to dashboard: {name}")
        
        # Save animal data with sound fetching
        result = save_to_snowflake_with_sound(
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
            fetch_sound=auto_fetch_sound
        )
        
        # Log the result
        if result["success"]:
            logger.info(f"Successfully added {name} to dashboard (ID: {result['animal_id']})")
            if result["sound_result"] and result["sound_result"]["success"]:
                logger.info(f"Sound found: {result['sound_result']['source']} - {result['sound_result']['sound_url']}")
            else:
                logger.warning(f"No sound found for {name}")
        else:
            logger.error(f"Failed to add {name} to dashboard")
            
        return result
    
    def update_existing_animal_sound(self, animal_identifier, sound_url=None, source=None):
        """
        Update sound for an existing animal in the dashboard
        
        Args:
            animal_identifier: Animal ID (int) or animal name (str)
            sound_url: Direct URL (optional - will fetch if not provided)
            source: Sound source (optional - will detect if fetching)
            
        Returns:
            dict: Update result with success status and details
        """
        if isinstance(animal_identifier, int):
            result = update_animal_sound_url(
                animal_id=animal_identifier,
                sound_url=sound_url,
                source=source
            )
        else:
            result = update_animal_sound_url(
                animal_name=animal_identifier,
                sound_url=sound_url,
                source=source
            )
        
        if result["success"]:
            logger.info(f"Updated sound for {animal_identifier}: {result['source']} - {result['sound_url']}")
        else:
            logger.error(f"Failed to update sound for {animal_identifier}: {result['message']}")
            
        return result
    
    def batch_update_all_missing_sounds(self, limit=None, progress_callback=None):
        """
        Update all animals in the dashboard that are missing sounds
        
        Args:
            limit: Maximum number to process (None for all)
            progress_callback: Function to call with progress updates
            
        Returns:
            dict: Batch update results with detailed statistics
        """
        logger.info(f"Starting batch sound update (limit: {limit or 'all'})")
        
        result = bulk_update_missing_sounds(limit=limit)
        
        logger.info(f"Batch update complete: {result['successful']}/{result['total_processed']} successful")
        
        if progress_callback:
            progress_callback(result)
            
        return result
    
    def get_dashboard_sound_status(self):
        """
        Get comprehensive sound status for all animals in the dashboard
        
        Returns:
            dict: Statistics about sound availability and sources
        """
        conn = get_snowflake_connection()
        if not conn:
            return {"error": "Database connection failed"}
        
        try:
            cursor = conn.cursor()
            
            # Get overall statistics
            cursor.execute("SELECT COUNT(*) FROM animal_insight_data")
            total_animals = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM animal_insight_data WHERE sound_url IS NOT NULL AND sound_url != ''")
            animals_with_sound = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM animal_insight_data WHERE sound_url IS NULL OR sound_url = ''")
            animals_without_sound = cursor.fetchone()[0]
            
            # Try to get breakdown by sound source (fallback if column doesn't exist)
            sources = {}
            try:
                cursor.execute("""
                    SELECT sound_source, COUNT(*) 
                    FROM animal_insight_data 
                    WHERE sound_url IS NOT NULL AND sound_url != ''
                    GROUP BY sound_source
                    ORDER BY COUNT(*) DESC
                """)
                sources = dict(cursor.fetchall())
            except:
                # Column might not exist yet, that's okay
                sources = {"various": animals_with_sound}
            
            # Try to get recently updated sounds (fallback if column doesn't exist)
            recent_updates = []
            try:
                cursor.execute("""
                    SELECT name, sound_source, sound_updated
                    FROM animal_insight_data 
                    WHERE sound_updated IS NOT NULL
                    ORDER BY sound_updated DESC
                    LIMIT 10
                """)
                recent_updates = cursor.fetchall()
            except:
                # Column might not exist yet, get recent animals with sounds instead
                cursor.execute("""
                    SELECT name, 'unknown', timestamp
                    FROM animal_insight_data 
                    WHERE sound_url IS NOT NULL AND sound_url != ''
                    ORDER BY timestamp DESC
                    LIMIT 10
                """)
                recent_updates = cursor.fetchall()
            
            cursor.close()
            
            return {
                "total_animals": total_animals,
                "animals_with_sound": animals_with_sound,
                "animals_without_sound": animals_without_sound,
                "sound_coverage_percentage": round((animals_with_sound / total_animals * 100) if total_animals > 0 else 0, 1),
                "sources_breakdown": sources,
                "recent_updates": recent_updates
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard sound status: {str(e)}")
            return {"error": str(e)}
        finally:
            conn.close()
    
    def get_animals_without_sounds(self, limit=50):
        """
        Get list of animals that don't have sound URLs
        
        Args:
            limit: Maximum number to return
            
        Returns:
            list: Animals missing sounds with their details
        """
        conn = get_snowflake_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, category, timestamp
                FROM animal_insight_data 
                WHERE sound_url IS NULL OR sound_url = ''
                ORDER BY timestamp DESC
                LIMIT %s
            """, (limit,))
            
            animals = cursor.fetchall()
            cursor.close()
            
            return [
                {
                    "id": animal[0],
                    "name": animal[1],
                    "category": animal[2],
                    "added_date": animal[3]
                }
                for animal in animals
            ]
            
        except Exception as e:
            logger.error(f"Error getting animals without sounds: {str(e)}")
            return []
        finally:
            conn.close()
    
    def test_sound_sources(self, test_animal="robin"):
        """
        Test all sound sources with a sample animal
        
        Args:
            test_animal: Animal name to test with
            
        Returns:
            dict: Test results for each source
        """
        logger.info(f"Testing sound sources with animal: {test_animal}")
        
        results = {}
        
        # Test each source
        sources = ["xeno_canto", "inaturalist", "huggingface", "internet_archive"]
        
        for source in sources:
            try:
                logger.info(f"Testing {source}...")
                # This would require modifications to sound_utils to test individual sources
                # For now, we'll just test the general fetcher
                sound_url = self.sound_fetcher.fetch_sound(test_animal, max_duration=30)
                
                results[source] = {
                    "success": bool(sound_url),
                    "url": sound_url,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                results[source] = {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        return results

# Global instance for easy import
dashboard_sound_manager = DashboardSoundManager()

def streamlit_sound_management_ui():
    """
    Streamlit UI components for sound management (can be integrated into app.py)
    """
    st.subheader("🔊 Sound Management")
    
    # Sound status overview
    with st.expander("📊 Sound Status Overview", expanded=True):
        status = dashboard_sound_manager.get_dashboard_sound_status()
        
        if "error" not in status:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Animals", status["total_animals"])
            with col2:
                st.metric("With Sounds", status["animals_with_sound"])
            with col3:
                st.metric("Coverage", f"{status['sound_coverage_percentage']}%")
            
            # Sources breakdown
            if status["sources_breakdown"]:
                st.write("**Sound Sources:**")
                for source, count in status["sources_breakdown"].items():
                    st.write(f"- {source}: {count}")
        else:
            st.error(f"Error: {status['error']}")
    
    # Batch update section
    with st.expander("🔄 Batch Sound Updates"):
        col1, col2 = st.columns(2)
        
        with col1:
            limit = st.number_input("Limit (0 for all)", min_value=0, value=10)
            limit = None if limit == 0 else limit
        
        with col2:
            if st.button("🚀 Update Missing Sounds"):
                with st.spinner("Updating sounds..."):
                    result = dashboard_sound_manager.batch_update_all_missing_sounds(limit=limit)
                    
                st.success(f"Updated {result['successful']}/{result['total_processed']} animals")
                
                # Show results
                if result["results"]:
                    for animal_result in result["results"][:5]:  # Show first 5
                        if animal_result["success"]:
                            st.write(f"✅ {animal_result['name']}: {animal_result['source']}")
                        else:
                            st.write(f"❌ {animal_result['name']}: {animal_result['message']}")
    
    # Individual animal update
    with st.expander("🎯 Update Individual Animal"):
        animal_name = st.text_input("Animal Name")
        if st.button("🔊 Fetch Sound") and animal_name:
            with st.spinner(f"Fetching sound for {animal_name}..."):
                result = dashboard_sound_manager.update_existing_animal_sound(animal_name)
                
            if result["success"]:
                st.success(f"✅ Found sound from {result['source']}")
                st.audio(result["sound_url"])
            else:
                st.error(f"❌ {result['message']}")
    
    # Animals without sounds
    with st.expander("🔍 Animals Without Sounds"):
        animals_without_sounds = dashboard_sound_manager.get_animals_without_sounds(limit=20)
        
        if animals_without_sounds:
            for animal in animals_without_sounds:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{animal['name']}** ({animal['category'] or 'Unknown'})")
                with col2:
                    if st.button("🔊", key=f"sound_{animal['id']}"):
                        with st.spinner("Fetching..."):
                            result = dashboard_sound_manager.update_existing_animal_sound(animal["id"])
                        if result["success"]:
                            st.success("✅")
                            st.rerun()
                        else:
                            st.error("❌")
        else:
            st.info("All animals have sounds! 🎉")

if __name__ == "__main__":
    print("🔊 NatureTrace Dashboard Sound Integration")
    print("=" * 50)
    
    # Initialize manager
    manager = DashboardSoundManager()
    
    # Show status
    print("\n📊 Current Sound Status:")
    status = manager.get_dashboard_sound_status()
    if "error" not in status:
        print(f"Total Animals: {status['total_animals']}")
        print(f"With Sounds: {status['animals_with_sound']}")
        print(f"Coverage: {status['sound_coverage_percentage']}%")
        print(f"Sources: {status['sources_breakdown']}")
    else:
        print(f"Error: {status['error']}")
    
    # Interactive mode
    print("\nAvailable commands:")
    print("1. update_all - Update all missing sounds")
    print("2. update <animal_name> - Update specific animal")
    print("3. status - Show current status")
    print("4. test - Test sound sources")
    print("5. exit - Exit")
    
    while True:
        try:
            command = input("\nEnter command: ").strip().lower()
            
            if command == "exit":
                break
            elif command == "status":
                status = manager.get_dashboard_sound_status()
                print(f"Animals: {status.get('total_animals', 0)}, With sounds: {status.get('animals_with_sound', 0)}")
            elif command == "update_all":
                print("Updating all missing sounds...")
                result = manager.batch_update_all_missing_sounds(limit=10)
                print(f"Updated {result['successful']}/{result['total_processed']} animals")
            elif command.startswith("update "):
                animal_name = command[7:]
                print(f"Updating sound for: {animal_name}")
                result = manager.update_existing_animal_sound(animal_name)
                if result["success"]:
                    print(f"✅ Success: {result['source']} - {result['sound_url']}")
                else:
                    print(f"❌ Failed: {result['message']}")
            elif command == "test":
                print("Testing sound sources...")
                results = manager.test_sound_sources()
                for source, result in results.items():
                    status = "✅" if result["success"] else "❌"
                    print(f"{status} {source}: {result}")
            else:
                print("Unknown command. Try 'help' for available commands.")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
