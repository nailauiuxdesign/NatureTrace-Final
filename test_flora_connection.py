import snowflake.connector
import logging

# Enable detailed logging
logging.basicConfig(level=logging.INFO)

def test_flora_connection():
    """Test connection with FLORA0122 user"""
    try:
        print("Testing connection with FLORA0122...")
        
        # Connect without role first
        conn = snowflake.connector.connect(
            user="FLORA0122",
            password="NatureTrace.123",
            account="mp23362.canada-central.azure",
            warehouse="COMPUTE_WH",
            autocommit=True
        )
        
        cursor = conn.cursor()
        
        # Check current context and available roles,
        cursor.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_ACCOUNT(), CURRENT_REGION()")
        user, role, account, region = cursor.fetchone()
        print(f"✅ Connected successfully!")
        print(f"   User: {user}")
        print(f"   Role: {role}")
        print(f"   Account: {account}")
        print(f"   Region: {region}")
        
        # Check available roles
        try:
            cursor.execute("SHOW GRANTS TO USER FLORA0122")
            grants = cursor.fetchall()
            print(f"\n✅ Available roles for FLORA0122:")
            for grant in grants:
                if grant[2] == 'ROLE':
                    print(f"   - {grant[3]}")
        except Exception as role_error:
            print(f"⚠ Could not fetch roles: {role_error}")
        
        # Try to switch to ACCOUNTADMIN role
        try:
            cursor.execute("USE ROLE ACCOUNTADMIN")
            print("✅ Successfully switched to ACCOUNTADMIN role")
            
            # Check current role again
            cursor.execute("SELECT CURRENT_ROLE()")
            current_role = cursor.fetchone()[0]
            print(f"   Current role: {current_role}")
            
        except Exception as role_switch_error:
            print(f"⚠ Could not switch to ACCOUNTADMIN: {role_switch_error}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_flora_connection()
