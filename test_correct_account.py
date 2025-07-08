import snowflake.connector
import logging

# 启用详细日志
logging.basicConfig(level=logging.INFO)

def test_correct_account():
    """Test Snowflake connection with correct account format"""
    try:
        print("Testing Snowflake connection with correct account format...")
        
        conn = snowflake.connector.connect(
            user="FLORA0122",
            password="NatureTrace.123",
            account="MQGEBKP-MP23362",
            role="NATURETRACE_ROLE",
            warehouse="COMPUTE_WH",
            database="ANIMAL_DB",
            schema="INSIGHTS",
            autocommit=True
        )
        
        cursor = conn.cursor()
        
        # Test basic connection
        cursor.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_ACCOUNT(), CURRENT_REGION()")
        user, role, db, schema, account, region = cursor.fetchone()
        print(f"✅ Connected successfully!")
        print(f"   User: {user}")
        print(f"   Role: {role}")
        print(f"   Database: {db}")
        print(f"   Schema: {schema}")
        print(f"   Account: {account}")
        print(f"   Region: {region}")
        
        # Test table access
        try:
            cursor.execute("SELECT COUNT(*) FROM animal_insight_data")
            count = cursor.fetchone()[0]
            print(f"✅ Table 'animal_insight_data' exists with {count} rows")
            
            # Show sample data if any exists
            if count > 0:
                cursor.execute("SELECT filename, name, timestamp FROM animal_insight_data LIMIT 3")
                rows = cursor.fetchall()
                print(f"✅ Sample data:")
                for row in rows:
                    print(f"   - {row[0]}: {row[1]} ({row[2]})")
            
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
                    VALUES ('test_connection.jpg', 'Test Lion', 'A test animal for connection verification', 'Lions are the king of the jungle', 'https://example.com/lion.mp3')
                """)
                print("✅ Test data inserted successfully")
                
                # Verify the insert
                cursor.execute("SELECT COUNT(*) FROM animal_insight_data")
                count = cursor.fetchone()[0]
                print(f"✅ Table now has {count} rows")
                
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
    test_correct_account()
