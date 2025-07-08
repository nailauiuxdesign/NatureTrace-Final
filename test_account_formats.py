import snowflake.connector
import logging

# 启用详细日志
logging.basicConfig(level=logging.INFO)

def test_different_account_formats():
    """Test different account identifier formats"""
    
    account_formats = [
        "MP23362.canadacentral",
        "MP23362",
        "mp23362.canadacentral.azure",
        "mp23362.canada-central.azure",
        "MP23362.canada-central.azure"
    ]
    
    for account in account_formats:
        print(f"\n=== Testing account format: {account} ===")
        try:
            conn = snowflake.connector.connect(
                user="FLORA0122",
                password="NatureTrace.123",
                account=account,
                role="NATURETRACE_ROLE",
                warehouse="COMPUTE_WH",
                login_timeout=10  # Shorter timeout for testing
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT CURRENT_ACCOUNT(), CURRENT_REGION()")
            account_info, region_info = cursor.fetchone()
            print(f"✅ SUCCESS! Account: {account_info}, Region: {region_info}")
            
            cursor.close()
            conn.close()
            return account  # Return the working format
            
        except Exception as e:
            print(f"❌ Failed with {account}: {str(e)[:100]}...")
    
    print("\n❌ None of the account formats worked")
    return None

if __name__ == "__main__":
    working_format = test_different_account_formats()
    if working_format:
        print(f"\n🎉 Use this account format: {working_format}")
