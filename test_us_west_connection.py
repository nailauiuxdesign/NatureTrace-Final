import snowflake.connector
import logging

# 启用详细日志
logging.basicConfig(level=logging.INFO)

def test_us_west_connection():
    """Test Snowflake connection with US West 2 region"""
    try:
        print("Testing Snowflake connection with US West 2 region...")
        
        conn = snowflake.connector.connect(
            user="FLORA0122",
            password="NatureTrace.123",
            account="MP23362.us-west-2",
            role="NATURETRACE_ROLE",
            warehouse="COMPUTE_WH",
            database="ANIMAL_DB",
            schema="INSIGHTS",
            autocommit=True
        )
        
        cursor = conn.cursor()
        
        # Test basic connection
        cursor.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE(), CURRENT_SCHEMA()")
        user, role, db, schema = cursor.fetchone()
        print(f"✅ Connected successfully!")
        print(f"   User: {user}")
        print(f"   Role: {role}")
        print(f"   Database: {db}")
        print(f"   Schema: {schema}")
        
        # Test table access
        try:
            cursor.execute("SELECT COUNT(*) FROM animal_insight_data")
            count = cursor.fetchone()[0]
            print(f"✅ Table 'animal_insight_data' exists with {count} rows")
            
            # Test a simple query
            cursor.execute("SELECT * FROM animal_insight_data LIMIT 3")
            rows = cursor.fetchall()
            print(f"✅ Successfully queried table, sample data: {len(rows)} rows")
            
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
                print("✅ Table created successfully")
                
                # Test insert
                cursor.execute("""
                    INSERT INTO animal_insight_data (filename, name, description, facts, sound_url)
                    VALUES ('test.jpg', 'Test Animal', 'Test description', 'Test fact', 'test_url')
                """)
                print("✅ Test data inserted successfully")
                
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
    test_us_west_connection()
