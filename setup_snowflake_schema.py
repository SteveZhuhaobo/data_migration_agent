#!/usr/bin/env python3
"""
Setup Snowflake schema and permissions for migration
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

def setup_database_and_schema(sf_conn):
    """Setup database and schema with proper permissions"""
    cursor = sf_conn.cursor()
    
    try:
        # Create database if it doesn't exist
        print("🏗️  Creating database steve_mcp...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS steve_mcp")
        
        # Use the database
        cursor.execute("USE DATABASE steve_mcp")
        
        # Create schema if it doesn't exist
        print("🏗️  Creating schema data_migration...")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS data_migration")
        
        # Grant permissions to current user
        print("🔐 Granting permissions...")
        cursor.execute("GRANT ALL ON DATABASE steve_mcp TO ROLE sysadmin")
        cursor.execute("GRANT ALL ON SCHEMA steve_mcp.data_migration TO ROLE sysadmin")
        cursor.execute("GRANT ALL ON FUTURE TABLES IN SCHEMA steve_mcp.data_migration TO ROLE sysadmin")
        
        print("✅ Database and schema setup completed successfully")
        
        # Test by creating a simple table
        print("🧪 Testing table creation...")
        cursor.execute("USE SCHEMA steve_mcp.data_migration")
        cursor.execute("CREATE OR REPLACE TABLE test_table (id INTEGER, name VARCHAR(50))")
        cursor.execute("DROP TABLE test_table")
        print("✅ Table creation test successful")
        
    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        raise
    finally:
        cursor.close()

def main():
    """Setup Snowflake environment"""
    print("=== SNOWFLAKE SCHEMA SETUP ===")
    
    try:
        # Load configuration
        config = load_config()
        
        # Connect to Snowflake
        print("🔌 Connecting to Snowflake...")
        sf_conn = get_snowflake_connection(config)
        
        # Setup database and schema
        setup_database_and_schema(sf_conn)
        
        # Close connection
        sf_conn.close()
        
        print("\n🎉 SNOWFLAKE SETUP COMPLETED!")
        print("✅ Database: steve_mcp")
        print("✅ Schema: data_migration")
        print("✅ Permissions granted")
        print("\n🚀 Ready to run migration!")
        
    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()