import snowflake.connector
import pandas as pd

def test_table_access():
    """Test different ways to access the table"""
    try:
        conn = snowflake.connector.connect(
            user="ANIMAL_USER",
            password="NatureTrace.123", 
            account="mqgebkp-rw64676",
            warehouse="COMPUTE_WH",
            database="ANIMAL_DB",
            schema="INSIGHTS"
        )
        
        cursor = conn.cursor()
        
        print("Testing table access...")
        
        # Test 1: Show current database and schema
        cursor.execute("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA()")
        result = cursor.fetchone()
        print(f"Current database: {result[0]}, Current schema: {result[1]}")
        
        # Test 2: Show all tables in current schema
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"Tables in current schema: {[table[1] for table in tables]}")
        
        # Test 3: Try different table name variations
        table_variations = [
            "animal_insight_data",
            "ANIMAL_INSIGHT_DATA", 
            "ANIMAL_DB.INSIGHTS.animal_insight_data",
            "ANIMAL_DB.INSIGHTS.ANIMAL_INSIGHT_DATA"
        ]
        
        for table_name in table_variations:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"✓ Table '{table_name}' exists with {count} rows")
                
                # Try to fetch data
                df = pd.read_sql(f"SELECT * FROM {table_name} LIMIT 5", conn)
                print(f"✓ Successfully queried {table_name}")
                break
                
            except Exception as e:
                print(f"✗ Failed to access '{table_name}': {e}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    test_table_access()
