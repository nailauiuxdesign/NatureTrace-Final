import streamlit as st
import snowflake.connector
import sys
import os

# Add the current directory to Python path
sys.path.append(os.getcwd())

print("Testing Snowflake configuration...")

# Try to load secrets
try:
    # Check if secrets.toml exists and is readable
    secrets_path = ".streamlit/secrets.toml"
    if os.path.exists(secrets_path):
        print(f"✓ Found secrets.toml at {secrets_path}")
        
        # Try to read the file content
        with open(secrets_path, 'r') as f:
            content = f.read()
            print("✓ secrets.toml is readable")
            
            # Check if all required Snowflake keys are present
            required_keys = [
                "snowflake_account",
                "snowflake_user", 
                "snowflake_password",
                "snowflake_warehouse",
                "snowflake_database",
                "snowflake_schema"
            ]
            
            for key in required_keys:
                if key in content:
                    print(f"✓ Found {key}")
                else:
                    print(f"✗ Missing {key}")
    else:
        print(f"✗ secrets.toml not found at {secrets_path}")
        
except Exception as e:
    print(f"✗ Error reading secrets.toml: {e}")

# Try to connect to Snowflake directly
try:
    print("\nTesting direct Snowflake connection...")
    conn = snowflake.connector.connect(
        user="ANIMAL_USER",
        password="NatureTrace.123", 
        account="mqgebkp-rw64676",
        warehouse="COMPUTE_WH",
        database="ANIMAL_DB",
        schema="INSIGHTS"
    )
    print("✓ Direct Snowflake connection successful!")
    conn.close()
except Exception as e:
    print(f"✗ Direct Snowflake connection failed: {e}")

# Try using streamlit secrets
try:
    print("\nTesting Streamlit secrets access...")
    # This will only work if running in streamlit context
    from utils.data_utils import get_snowflake_connection
    conn = get_snowflake_connection()
    if conn:
        print("✓ Streamlit secrets connection successful!")
        conn.close()
    else:
        print("✗ Streamlit secrets connection failed")
except Exception as e:
    print(f"✗ Error with Streamlit secrets: {e}")
