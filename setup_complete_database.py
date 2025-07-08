import snowflake.connector
import logging

# Enable detailed logging
logging.basicConfig(level=logging.INFO)

def setup_complete_database():
    """Set up complete database structure with ACCOUNTADMIN privileges"""
    try:
        print("Setting up complete Snowflake database structure...")
        
        # Connect with ACCOUNTADMIN role
        conn = snowflake.connector.connect(
            user="FLORA0122",
            password="NatureTrace.123",
            account="mp23362.canada-central.azure",
            warehouse="COMPUTE_WH",
            role="ACCOUNTADMIN",
            autocommit=True
        )
        
        cursor = conn.cursor()
        
        # Check current context
        cursor.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_ACCOUNT(), CURRENT_REGION()")
        user, role, account, region = cursor.fetchone()
        print(f"✅ Connected successfully!")
        print(f"   User: {user}")
        print(f"   Role: {role}")
        print(f"   Account: {account}")
        print(f"   Region: {region}")
        
        # Create database if it doesn't exist
        try:
            cursor.execute("CREATE DATABASE IF NOT EXISTS ANIMAL_DB")
            print("✅ Database 'ANIMAL_DB' created/verified")
        except Exception as db_error:
            print(f"⚠ Database creation issue: {db_error}")
        
        # Use the database
        cursor.execute("USE DATABASE ANIMAL_DB")
        print("✅ Using database ANIMAL_DB")
        
        # Create schema if it doesn't exist
        try:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS INSIGHTS")
            print("✅ Schema 'INSIGHTS' created/verified")
        except Exception as schema_error:
            print(f"⚠ Schema creation issue: {schema_error}")
        
        # Use the schema
        cursor.execute("USE SCHEMA INSIGHTS")
        print("✅ Using schema INSIGHTS")
        
        # Create the table
        try:
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
            print("✅ Table 'animal_insight_data' created successfully")
        except Exception as table_error:
            print(f"⚠ Table creation issue: {table_error}")
        
        # Verify table structure
        cursor.execute("DESCRIBE TABLE animal_insight_data")
        columns = cursor.fetchall()
        print("✅ Table structure verified:")
        for col in columns:
            print(f"   - {col[0]}: {col[1]}")
        
        # Test insert
        try:
            cursor.execute("""
                INSERT INTO animal_insight_data (filename, name, description, facts, sound_url)
                VALUES ('setup_test.jpg', 'Setup Test Lion', 'Database setup verification', 'Successfully created complete database structure', 'https://example.com/setup_lion.mp3')
                ON CONFLICT(filename) DO NOTHING
            """)
            print("✅ Test data inserted successfully")
        except Exception as insert_error:
            print(f"⚠ Insert test issue: {insert_error}")
        
        # Verify the data
        cursor.execute("SELECT COUNT(*) FROM animal_insight_data")
        count = cursor.fetchone()[0]
        print(f"✅ Table now has {count} rows")
        
        # Show sample data
        cursor.execute("SELECT filename, name, timestamp FROM animal_insight_data LIMIT 3")
        rows = cursor.fetchall()
        print("✅ Sample data:")
        for row in rows:
            print(f"   - {row[0]}: {row[1]} ({row[2]})")
        
        cursor.close()
        conn.close()
        print("\n🎉 Complete database setup completed successfully!")
        print("🚀 NatureTrace application is now ready to use!")
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    setup_complete_database()
