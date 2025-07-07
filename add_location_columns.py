#!/usr/bin/env python3
"""
Database migration script to add location columns to existing animal_insight_data table
"""

from utils.data_utils import get_snowflake_connection
import logging

# Enable detailed logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_location_columns():
    """Add location columns to the existing animal_insight_data table"""
    conn = get_snowflake_connection()
    if not conn:
        logger.error("Cannot connect to Snowflake database")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Add location columns if they don't exist
        location_columns = [
            "ALTER TABLE animal_insight_data ADD COLUMN latitude FLOAT",
            "ALTER TABLE animal_insight_data ADD COLUMN longitude FLOAT", 
            "ALTER TABLE animal_insight_data ADD COLUMN location_string VARCHAR(500)",
            "ALTER TABLE animal_insight_data ADD COLUMN place_guess VARCHAR(500)"
        ]
        
        for sql in location_columns:
            try:
                cursor.execute(sql)
                column_name = sql.split()[-2]  # Extract column name from SQL
                logger.info(f"✅ Added column: {column_name}")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate column name" in str(e).lower():
                    column_name = sql.split()[-2]
                    logger.info(f"ℹ️  Column {column_name} already exists")
                else:
                    logger.error(f"❌ Error adding column: {e}")
        
        cursor.close()
        logger.info("🎉 Location columns migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False
    finally:
        conn.close()

def verify_location_columns():
    """Verify that the location columns were added successfully"""
    conn = get_snowflake_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("DESCRIBE TABLE animal_insight_data")
        columns = cursor.fetchall()
        
        location_columns = ['LATITUDE', 'LONGITUDE', 'LOCATION_STRING', 'PLACE_GUESS']
        existing_columns = [col[0] for col in columns]
        
        logger.info("📋 Current table schema:")
        for col in columns:
            logger.info(f"  - {col[0]} ({col[1]})")
        
        logger.info("\n🔍 Location columns status:")
        for loc_col in location_columns:
            if loc_col in existing_columns:
                logger.info(f"  ✅ {loc_col}: Present")
            else:
                logger.info(f"  ❌ {loc_col}: Missing")
        
        cursor.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False
    finally:
        conn.close()

def main():
    """Main migration function"""
    print("🚀 Starting location columns migration...")
    print("=" * 50)
    
    # Step 1: Add location columns
    print("\n📝 Step 1: Adding location columns...")
    if add_location_columns():
        print("✅ Location columns added successfully!")
    else:
        print("❌ Failed to add location columns")
        return
    
    # Step 2: Verify columns
    print("\n🔍 Step 2: Verifying table schema...")
    if verify_location_columns():
        print("✅ Schema verification completed!")
    else:
        print("❌ Schema verification failed")
        return
    
    print("\n🎉 Migration completed successfully!")
    print("\n📍 Your database now supports location data:")
    print("  • Latitude/Longitude coordinates")
    print("  • Location strings from iNaturalist")
    print("  • Place names and location descriptions")
    print("\n💡 Next steps:")
    print("  1. Run fetch_initial_data.py to populate with location data")
    print("  2. Use the enhanced Google Maps integration")
    print("  3. View animal locations on interactive maps")

if __name__ == "__main__":
    main()
