import snowflake.connector
import sys

def setup_snowflake_database():
    """Set up the Snowflake database, schema, and table"""
    try:
        # Connect to Snowflake
        conn = snowflake.connector.connect(
            user="ANIMAL_USER",
            password="NatureTrace.123", 
            account="mqgebkp-rw64676",
            warehouse="COMPUTE_WH"
        )
        
        cursor = conn.cursor()
        
        print("Setting up Snowflake database and schema...")
        
        # Create database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS ANIMAL_DB")
        print("✓ Database ANIMAL_DB created/verified")
        
        # Use the database
        cursor.execute("USE DATABASE ANIMAL_DB")
        
        # Create schema if it doesn't exist
        cursor.execute("CREATE SCHEMA IF NOT EXISTS INSIGHTS")
        print("✓ Schema INSIGHTS created/verified")
        
        # Use the schema
        cursor.execute("USE SCHEMA INSIGHTS")
        
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS animal_insight_data (
                id INTEGER AUTOINCREMENT PRIMARY KEY,
                filename VARCHAR(255) UNIQUE,
                name VARCHAR(255),
                description TEXT,
                facts TEXT,
                sound_url VARCHAR(500),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
            )
        """)
        print("✓ Table animal_insight_data created/verified")
        
        # Verify the setup
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"✓ Tables in ANIMAL_DB.INSIGHTS: {[table[1] for table in tables]}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Snowflake setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up Snowflake: {e}")
        return False

if __name__ == "__main__":
    success = setup_snowflake_database()
    sys.exit(0 if success else 1)
