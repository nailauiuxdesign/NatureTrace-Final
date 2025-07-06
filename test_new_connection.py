import snowflake.connector
import pandas as pd

def test_new_connection():
    """Test the new Snowflake connection with updated credentials"""
    try:
        print("Testing new Snowflake connection...")
        
        conn = snowflake.connector.connect(
            user="FLORA0122",
            password="NatureTrace.123",
            account="MP23362.canadacentral.azure",
            warehouse="COMPUTE_WH",
            database="ANIMAL_DB",
            schema="INSIGHTS",
            role="NATURETRACE_ROLE",
            autocommit=True
        )
        
        cursor = conn.cursor()
        
        # Test connection
        cursor.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE(), CURRENT_SCHEMA()")
        result = cursor.fetchone()
        print(f"✓ Connected as user: {result[0]}")
        print(f"✓ Using role: {result[1]}")
        print(f"✓ Current database: {result[2]}")
        print(f"✓ Current schema: {result[3]}")
        
        # Check if table exists
        try:
            cursor.execute("SELECT COUNT(*) FROM animal_insight_data")
            count = cursor.fetchone()[0]
            print(f"✓ Table 'animal_insight_data' exists with {count} rows")
            
            # Test querying the table
            cursor.execute("SELECT * FROM animal_insight_data LIMIT 5")
            rows = cursor.fetchall()
            print(f"✓ Successfully queried table, got {len(rows)} rows")
            
        except Exception as table_error:
            print(f"⚠ Table issue: {table_error}")
            
            # Try to create the table
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
                print("✓ Table created successfully")
            except Exception as create_error:
                print(f"✗ Failed to create table: {create_error}")
        
        cursor.close()
        conn.close()
        print("\n🎉 Connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_new_connection()
