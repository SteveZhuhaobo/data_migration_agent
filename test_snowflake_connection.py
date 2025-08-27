#!/usr/bin/env python3
"""
Test Snowflake connection with different account formats
"""

import snowflake.connector
import yaml
import os

def test_connection_formats():
    """Test different account identifier formats"""
    
    # Load config
    config_path = os.path.join("config", "config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    snowflake_config = config['snowflake']
    
    # Different account formats to try
    account_formats = [
        "MZLGTMY-ZL90213.snowflakecomputing.com",  # Current format
        "MZLGTMY-ZL90213",  # Without .snowflakecomputing.com
        "mzlgtmy-zl90213",  # Lowercase
        "mzlgtmy-zl90213.snowflakecomputing.com",  # Lowercase with domain
    ]
    
    for account_format in account_formats:
        print(f"\n🔍 Testing account format: {account_format}")
        
        try:
            conn = snowflake.connector.connect(
                account=account_format,
                user=snowflake_config['user'],
                password=snowflake_config['password'],
                database=snowflake_config['database'],
                schema=snowflake_config['schema'],
                warehouse=snowflake_config['warehouse'],
                role=snowflake_config.get('role', 'sysadmin')
            )
            
            # Test the connection
            cursor = conn.cursor()
            cursor.execute("SELECT CURRENT_VERSION(), CURRENT_USER(), CURRENT_ACCOUNT()")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            print(f"✅ SUCCESS with account format: {account_format}")
            print(f"   Version: {result[0]}")
            print(f"   User: {result[1]}")
            print(f"   Account: {result[2]}")
            return account_format
            
        except Exception as e:
            print(f"❌ FAILED with account format: {account_format}")
            print(f"   Error: {str(e)}")
    
    return None

if __name__ == "__main__":
    print("=== Testing Snowflake Connection Formats ===")
    
    try:
        working_format = test_connection_formats()
        
        if working_format:
            print(f"\n🎉 Found working account format: {working_format}")
            print("\nUpdate your config/config.yaml with this format:")
            print(f"snowflake:")
            print(f"  account: \"{working_format}\"")
        else:
            print("\n❌ No working account format found")
            print("Please check:")
            print("1. Your Snowflake account identifier")
            print("2. Username and password")
            print("3. Network connectivity")
            print("4. Firewall settings")
            
    except Exception as e:
        print(f"Error running tests: {str(e)}")