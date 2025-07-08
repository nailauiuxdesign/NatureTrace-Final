#!/usr/bin/env python3
"""
Enhanced Sound Database Update Script
Updates SOUND_URL, SOUND_SOURCE, and SOUND_UPDATED fields for all animals in the database
Prioritizes iNaturalist sources and applies current enhanced sound logic
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import logging
from datetime import datetime
from utils.data_utils import get_snowflake_connection, fetch_dashboard_data
from utils.sound_utils import fetch_clean_animal_sound, test_multiple_sound_sources, prioritize_inaturalist_for_mammals

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_sound_source_and_timestamp(animal_id, animal_name, sound_url, sound_source):
    """Update sound URL, source, and timestamp in database"""
    conn = get_snowflake_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # First check if columns exist, add them if they don't
        try:
            cursor.execute("""
                ALTER TABLE animal_insight_data 
                ADD COLUMN sound_source VARCHAR(100),
                ADD COLUMN sound_updated TIMESTAMP
            """)
            logger.info("Added sound_source and sound_updated columns")
        except Exception as e:
            # Columns might already exist
            logger.debug(f"Columns may already exist: {e}")
        
        # Update the record with enhanced data
        cursor.execute("""
            UPDATE animal_insight_data 
            SET sound_url = %s, 
                sound_source = %s, 
                sound_updated = CURRENT_TIMESTAMP()
            WHERE id = %s
        """, (sound_url, sound_source, animal_id))
        
        affected_rows = cursor.rowcount
        cursor.close()
        
        if affected_rows > 0:
            logger.info(f"Updated sound data for {animal_name} (ID: {animal_id})")
            return True
        else:
            logger.warning(f"No rows updated for {animal_name} (ID: {animal_id})")
            return False
            
    except Exception as e:
        logger.error(f"Database error updating {animal_name}: {e}")
        return False
    finally:
        conn.close()

def enhance_sound_database(update_existing=False, prioritize_inaturalist=True, limit=None):
    """
    Enhance sound database with current logic
    
    Args:
        update_existing: If True, update animals that already have sounds
        prioritize_inaturalist: If True, prioritize iNaturalist sources for mammals
        limit: Maximum number of animals to process (None for all)
    """
    logger.info("🎵 Starting Enhanced Sound Database Update...")
    
    # Fetch current data
    df = fetch_dashboard_data()
    if df.empty:
        logger.error("No data found in database")
        return
    
    logger.info(f"Found {len(df)} animals in database")
    
    # Filter animals that need sound updates
    if update_existing:
        # Update all animals
        animals_to_update = df
        logger.info("Updating ALL animals (including those with existing sounds)")
    else:
        # Only update animals without sounds
        animals_to_update = df[df['SOUND_URL'].isna() | (df['SOUND_URL'] == '')]
        logger.info(f"Updating {len(animals_to_update)} animals without sounds")
    
    if limit:
        animals_to_update = animals_to_update.head(limit)
        logger.info(f"Limited to {limit} animals for this run")
    
    # Statistics tracking
    stats = {
        'total_processed': 0,
        'successful_updates': 0,
        'failed_updates': 0,
        'inatural_sources': 0,
        'other_sources': 0,
        'no_sound_found': 0,
        'speech_removed': 0
    }
    
    logger.info(f"Processing {len(animals_to_update)} animals...")
    
    for idx, (_, animal) in enumerate(animals_to_update.iterrows()):
        animal_id = animal.get('ID')
        animal_name = animal.get('NAME', 'Unknown')
        animal_category = animal.get('CATEGORY', 'Unknown')
        
        stats['total_processed'] += 1
        
        logger.info(f"\n[{idx+1}/{len(animals_to_update)}] Processing: {animal_name} ({animal_category})")
        
        try:
            # Special handling for mammals to prioritize iNaturalist
            if prioritize_inaturalist and ('mammal' in animal_category.lower() or 
                any(mammal_word in animal_name.lower() for mammal_word in 
                    ["bear", "wolf", "lion", "tiger", "elephant", "whale", "dolphin", 
                     "cat", "dog", "horse", "bobcat", "lynx", "fox", "deer", "elk"])):
                
                logger.info(f"  🦁 Mammal detected - prioritizing iNaturalist")
                # First try iNaturalist specifically
                inaturalist_url = prioritize_inaturalist_for_mammals(animal_name, animal_category)
                
                if inaturalist_url:
                    logger.info(f"  ✅ Found iNaturalist sound: {inaturalist_url}")
                    success = update_sound_source_and_timestamp(
                        animal_id, animal_name, inaturalist_url, "iNaturalist"
                    )
                    if success:
                        stats['successful_updates'] += 1
                        stats['inatural_sources'] += 1
                    else:
                        stats['failed_updates'] += 1
                    continue
            
            # Use enhanced sound fetching for all other cases
            logger.info(f"  🔍 Using enhanced sound fetching...")
            result = fetch_clean_animal_sound(animal_name, animal_category)
            
            if result.get('success'):
                sound_url = result.get('processed_url') or result.get('original_url')
                source = result.get('source', 'Unknown')
                speech_removed = result.get('speech_removed', False)
                
                logger.info(f"  ✅ Found sound from {source}: {sound_url}")
                if speech_removed:
                    logger.info(f"  🧹 Speech was removed from recording")
                    stats['speech_removed'] += 1
                
                # Enhance source name for database
                enhanced_source = source
                if speech_removed:
                    enhanced_source += " (processed)"
                
                success = update_sound_source_and_timestamp(
                    animal_id, animal_name, sound_url, enhanced_source
                )
                
                if success:
                    stats['successful_updates'] += 1
                    if 'inaturalist' in source.lower():
                        stats['inatural_sources'] += 1
                    else:
                        stats['other_sources'] += 1
                else:
                    stats['failed_updates'] += 1
            else:
                logger.warning(f"  ❌ No sound found for {animal_name}: {result.get('message', 'Unknown error')}")
                stats['no_sound_found'] += 1
                
        except Exception as e:
            logger.error(f"  💥 Error processing {animal_name}: {e}")
            stats['failed_updates'] += 1
        
        # Progress update every 10 animals
        if (idx + 1) % 10 == 0:
            logger.info(f"\n📊 Progress Update - Processed {idx+1}/{len(animals_to_update)}")
            logger.info(f"   ✅ Successful: {stats['successful_updates']}")
            logger.info(f"   ❌ Failed: {stats['failed_updates']}")
            logger.info(f"   🔬 iNaturalist: {stats['inatural_sources']}")
            logger.info(f"   📚 Other sources: {stats['other_sources']}")
    
    # Final statistics
    logger.info(f"\n🎯 Enhanced Sound Database Update Complete!")
    logger.info(f"📊 Final Statistics:")
    logger.info(f"   Total Processed: {stats['total_processed']}")
    logger.info(f"   ✅ Successful Updates: {stats['successful_updates']}")
    logger.info(f"   ❌ Failed Updates: {stats['failed_updates']}")
    logger.info(f"   ⭕ No Sound Found: {stats['no_sound_found']}")
    logger.info(f"   🔬 iNaturalist Sources: {stats['inatural_sources']}")
    logger.info(f"   📚 Other Sources: {stats['other_sources']}")
    logger.info(f"   🧹 Speech Removed: {stats['speech_removed']}")
    
    success_rate = (stats['successful_updates'] / stats['total_processed'] * 100) if stats['total_processed'] > 0 else 0
    logger.info(f"   📈 Success Rate: {success_rate:.1f}%")
    
    return stats

def update_blank_sounds_only():
    """Update only animals with blank sound fields"""
    logger.info("🎵 Updating only animals with blank sound data...")
    return enhance_sound_database(
        update_existing=False, 
        prioritize_inaturalist=True,
        limit=None
    )

def update_all_sounds():
    """Update all animals with enhanced sound logic"""
    logger.info("🎵 Updating ALL animals with enhanced sound logic...")
    return enhance_sound_database(
        update_existing=True, 
        prioritize_inaturalist=True,
        limit=None
    )

def test_sound_updates(limit=5):
    """Test sound updates on a small subset"""
    logger.info(f"🧪 Testing sound updates on {limit} animals...")
    return enhance_sound_database(
        update_existing=False, 
        prioritize_inaturalist=True,
        limit=limit
    )

def verify_sound_updates():
    """Verify the sound updates by checking database"""
    logger.info("🔍 Verifying sound updates...")
    
    df = fetch_dashboard_data()
    if df.empty:
        logger.error("No data found")
        return
    
    # Check sound coverage
    total_animals = len(df)
    animals_with_sounds = len(df[df['SOUND_URL'].notna() & (df['SOUND_URL'] != '')])
    animals_with_sources = len(df[df['SOUND_SOURCE'].notna() & (df['SOUND_SOURCE'] != '')]) if 'SOUND_SOURCE' in df.columns else 0
    
    logger.info(f"📊 Sound Data Coverage:")
    logger.info(f"   Total Animals: {total_animals}")
    logger.info(f"   Animals with Sound URLs: {animals_with_sounds} ({animals_with_sounds/total_animals*100:.1f}%)")
    logger.info(f"   Animals with Sound Sources: {animals_with_sources} ({animals_with_sources/total_animals*100:.1f}%)")
    
    # Show source breakdown
    if 'SOUND_SOURCE' in df.columns:
        source_counts = df[df['SOUND_SOURCE'].notna()]['SOUND_SOURCE'].value_counts()
        logger.info(f"📈 Source Breakdown:")
        for source, count in source_counts.items():
            logger.info(f"   {source}: {count} animals")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Sound Database Update")
    parser.add_argument("--mode", choices=["blank", "all", "test", "verify"], 
                       default="blank", help="Update mode")
    parser.add_argument("--limit", type=int, help="Limit number of animals to process")
    
    args = parser.parse_args()
    
    if args.mode == "blank":
        update_blank_sounds_only()
    elif args.mode == "all":
        update_all_sounds()
    elif args.mode == "test":
        test_sound_updates(args.limit or 5)
    elif args.mode == "verify":
        verify_sound_updates()
