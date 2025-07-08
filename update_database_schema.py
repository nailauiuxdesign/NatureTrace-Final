import snowflake.connector
import logging
import os

# Enable detailed logging
logging.basicConfig(level=logging.INFO)

def update_database_schema():
    """Update the database schema to include new columns for iNaturalist and Wikipedia data"""
    try:
        print("Updating Snowflake database schema for iNaturalist and Wikipedia data...")
        
        # Connect using the correct credentials
        conn = snowflake.connector.connect(
            user="FLORA0122",
            password="Animal@Trace123!",
            account="mp23362.canada-central.azure",
            warehouse="COMPUTE_WH",
            role="ANIMAL_APP_ROLE",
            autocommit=True
        )
        
        cursor = conn.cursor()
        
        # Use the database and schema
        cursor.execute("USE DATABASE ANIMAL_DB")
        cursor.execute("USE SCHEMA INSIGHTS")
        print("✅ Connected to ANIMAL_DB.INSIGHTS")
        
        # Check current table structure
        cursor.execute("DESCRIBE TABLE animal_insight_data")
        existing_columns = [row[0].lower() for row in cursor.fetchall()]
        print(f"✅ Current columns: {existing_columns}")
        
        # Define new columns to add
        new_columns = [
            ("category", "VARCHAR(255)", "iconic_taxon_name from iNaturalist"),
            ("inatural_pic", "VARCHAR(500)", "image URL from iNaturalist"),
            ("wikipedia_url", "VARCHAR(500)", "Wikipedia URL"),
            ("original_image", "VARCHAR(500)", "original image from Wikipedia"),
            ("species", "TEXT", "species description from Wikipedia"),
            ("summary", "TEXT", "summary from Wikipedia")
        ]
        
        # Add new columns if they don't exist
        for col_name, col_type, description in new_columns:
            if col_name.lower() not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE animal_insight_data ADD COLUMN {col_name} {col_type}")
                    print(f"✅ Added column '{col_name}' ({description})")
                except Exception as e:
                    print(f"⚠ Issue adding column '{col_name}': {e}")
            else:
                print(f"✅ Column '{col_name}' already exists")
        
        # Verify updated table structure
        cursor.execute("DESCRIBE TABLE animal_insight_data")
        updated_columns = cursor.fetchall()
        print("\n✅ Updated table structure:")
        for col in updated_columns:
            print(f"   - {col[0]}: {col[1]}")
        
        cursor.close()
        conn.close()
        print("\n🎉 Database schema update completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Schema update failed: {e}")
        return False

if __name__ == "__main__":
    update_database_schema()
