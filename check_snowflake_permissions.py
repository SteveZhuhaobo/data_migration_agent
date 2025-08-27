#!/usr/bin/env python3
"""
Check Snowflake permissions and available resources
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
        role=sf_config.get('role', 'sysadmin')
    )

def check_permissions(sf_conn):
    """Check what databases and schemas are available"""
    cursor = sf_conn.cursor()
    
    try:
        # Check current user and role
        print("👤 Current User Information:")
        cursor.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_ACCOUNT()")
        user_info = cursor.fetchone()
        print(f"   User: {user_info[0]}")
        print(f"   Role: {user_info[1]}")
        print(f"   Account: {user_info[2]}")
        
        # Check available databases
        print("\n📚 Available Databases:")
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        for db in databases:
            print(f"   - {db[1]}")  # Database name is in column 1
        
        # Check available schemas in each database
        print("\n📁 Available Schemas:")
        for db in databases:
            db_name = db[1]
            try:
                cursor.execute(f"SHOW SCHEMAS IN DATABASE {db_name}")
                schemas = cursor.fetchall()
                print(f"   Database: {db_name}")
                for schema in schemas:
                    print(f"     - {schema[1]}")  # Schema name is in column 1
            except Exception as e:
                print(f"     - Cannot access schemas in {db_name}: {str(e)}")
        
        # Check available warehouses
        print("\n🏭 Available Warehouses:")
        cursor.execute("SHOW WAREHOUSES")
        warehouses = cursor.fetchall()
        for wh in warehouses:
            print(f"   - {wh[0]} (State: {wh[1]})")  # Name and state
        
        # Check current warehouse
        cursor.execute("SELECT CURRENT_WAREHOUSE()")
        current_wh = cursor.fetchone()
        print(f"\n🔧 Current Warehouse: {current_wh[0]}")
        
    except Exception as e:
        print(f"❌ Error checking permissions: {str(e)}")
        raise
    finally:
        cursor.close()

def test_table_creation(sf_conn):
    """Test table creation in different schemas"""
    cursor = sf_conn.cursor()
    
    print("\n🧪 Testing Table Creation Permissions:")
    
    # Try different database/schema combinations
    test_locations = [
        ("SNOWFLAKE_SAMPLE_DATA", "TPCH_SF1"),
        ("UTIL_DB", "PUBLIC"),
        ("DEMO_DB", "PUBLIC"),
        ("PUBLIC", "PUBLIC")
    ]
    
    for db, schema in test_locations:
        try:
            cursor.execute(f"USE DATABASE {db}")
            cursor.execute(f"USE SCHEMA {schema}")
            cursor.execute("CREATE OR REPLACE TABLE migration_test (id INTEGER, name VARCHAR(50))")
            cursor.execute("DROP TABLE migration_test")
            print(f"   ✅ Can create tables in {db}.{schema}")
            return db, schema
        except Exception as e:
            print(f"   ❌ Cannot create tables in {db}.{schema}: {str(e)}")
    
    cursor.close()
    return None, None

def main():
    """Check Snowflake permissions and resources"""
    print("=== SNOWFLAKE PERMISSIONS CHECK ===")
    
    try:
        # Load configuration
        config = load_config()
        
        # Connect to Snowflake
        print("🔌 Connecting to Snowflake...")
        sf_conn = get_snowflake_connection(config)
        
        # Check permissions
        check_permissions(sf_conn)
        
        # Test table creation
        working_db, working_schema = test_table_creation(sf_conn)
        
        # Close connection
        sf_conn.close()
        
        if working_db and working_schema:
            print(f"\n🎉 FOUND WORKING LOCATION!")
            print(f"✅ Database: {working_db}")
            print(f"✅ Schema: {working_schema}")
            print(f"\nUpdate your migration script to use:")
            print(f"   Database: {working_db}")
            print(f"   Schema: {working_schema}")
        else:
            print(f"\n❌ NO WORKING LOCATION FOUND")
            print("You may need to:")
            print("1. Contact your Snowflake administrator")
            print("2. Request permissions to create tables")
            print("3. Use a different role with more privileges")
        
    except Exception as e:
        print(f"❌ Check failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()