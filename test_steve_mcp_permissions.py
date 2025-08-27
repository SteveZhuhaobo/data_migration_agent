#!/usr/bin/env python3
"""
Test permissions specifically in STEVE_MCP.DATA_MIGRATION
"""

import snowflake.connector
import yaml

def load_config():
    """Load configuration"""
    with open("config/config.yaml", 'r') as f:
        return yaml.safe_load(f)

def get_snowflake_connection(config):
    """Create Snowflake connection with correct account format"""
    sf_config = config['snowflake']
    
    return snowflake.connector.connect(
        account="MZLGTMY-ZL90213",  # Use the working format
        user=sf_config['user'],
        password=sf_config['password'],
        warehouse=sf_config['warehouse'],
        role=sf_config.get('role', 'accountadmin')
    )

def test_steve_mcp_permissions(sf_conn):
    """Test permissions in STEVE_MCP.DATA_MIGRATION"""
    cursor = sf_conn.cursor()
    
    try:
        print("🧪 Testing STEVE_MCP.DATA_MIGRATION permissions...")
        
        # Use the correct database and schema
        cursor.execute("USE DATABASE STEVE_MCP")
        cursor.execute("USE SCHEMA DATA_MIGRATION")
        
        # Test table creation
        cursor.execute("CREATE OR REPLACE TABLE migration_test (id INTEGER, name VARCHAR(50))")
        print("✅ Table creation successful!")
        
        # Test data insertion
        cursor.execute("INSERT INTO migration_test VALUES (1, 'test')")
        print("✅ Data insertion successful!")
        
        # Test data selection
        cursor.execute("SELECT * FROM migration_test")
        result = cursor.fetchone()
        print(f"✅ Data selection successful: {result}")
        
        # Clean up
        cursor.execute("DROP TABLE migration_test")
        print("✅ Table cleanup successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Permission test failed: {str(e)}")
        return False
    finally:
        cursor.close()

def main():
    """Test STEVE_MCP permissions"""
    print("=== TESTING STEVE_MCP.DATA_MIGRATION PERMISSIONS ===")
    
    try:
        # Load configuration
        config = load_config()
        
        # Connect to Snowflake
        print("🔌 Connecting to Snowflake...")
        sf_conn = get_snowflake_connection(config)
        
        # Test permissions
        success = test_steve_mcp_permissions(sf_conn)
        
        # Close connection
        sf_conn.close()
        
        if success:
            print("\n🎉 PERMISSIONS TEST SUCCESSFUL!")
            print("✅ You can create tables in STEVE_MCP.DATA_MIGRATION")
            print("🚀 Ready to run the migration!")
        else:
            print("\n❌ PERMISSIONS TEST FAILED")
            print("Contact your Snowflake administrator for access")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()