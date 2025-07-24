#!/usr/bin/env python3
"""
Test script to validate all connections before running migration
"""

import yaml
import json
import asyncio
import pyodbc
from databricks import sql
from openai import AzureOpenAI

def load_config():
    """Load configuration file"""
    try:
        with open('config/config.yaml', 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print("❌ Config file not found: config/config.yaml")
        return None
    except yaml.YAMLError as e:
        print(f"❌ Error parsing config file: {e}")
        return None

def test_sql_server_connection(config):
    """Test SQL Server connection"""
    print("\n🔍 Testing SQL Server connection...")
    
    try:
        conn_str = f"""
        DRIVER={{{config['sql_server']['driver']}}};
        SERVER={config['sql_server']['server']};
        DATABASE={config['sql_server']['database']};
        UID={config['sql_server']['username']};
        PWD={config['sql_server']['password']};
        Encrypt={config['sql_server'].get('encrypt', 'no')};
        TrustServerCertificate={config['sql_server'].get('trust_server_certificate', 'yes')};
        Connection Timeout={config['sql_server'].get('connection_timeout', 30)};
        """
        
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        
        # Test table access
        cursor.execute("""
        SELECT COUNT(*) as table_count 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        """)
        table_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"✅ SQL Server connection successful")
        print(f"   Server version: {version[:50]}...")
        print(f"   Available tables: {table_count}")
        return True
        
    except Exception as e:
        print(f"❌ SQL Server connection failed: {str(e)}")
        return False

def test_databricks_connection(config):
    """Test Databricks connection"""
    print("\n🔍 Testing Databricks connection...")
    
    try:
        conn = sql.connect(
            server_hostname=config['databricks']['server_hostname'],
            http_path=config['databricks']['http_path'],
            access_token=config['databricks']['access_token']
        )
        
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT current_timestamp()")
        timestamp = cursor.fetchone()[0]
        
        # Test catalog access
        catalog = config['databricks']['catalog']
        schema = config['databricks']['schema']
        
        cursor.execute(f"SHOW TABLES IN {catalog}.{schema}")
        tables = cursor.fetchall()
        
        conn.close()
        
        print(f"✅ Databricks connection successful")
        print(f"   Current timestamp: {timestamp}")
        print(f"   Target catalog.schema: {catalog}.{schema}")
        print(f"   Existing tables: {len(tables)}")
        return True
        
    except Exception as e:
        print(f"❌ Databricks connection failed: {str(e)}")
        return False

async def test_azure_openai_connection(config):
    """Test Azure OpenAI connection"""
    print("\n🔍 Testing Azure OpenAI connection...")
    
    try:
        client = AzureOpenAI(
            azure_endpoint=config['azure_openai']['endpoint'],
            api_key=config['azure_openai']['api_key'],
            api_version=config['azure_openai']['api_version']
        )
        
        # Test basic completion
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=config['azure_openai']['deployment_name'],
            messages=[{"role": "user", "content": "Hello, this is a test message."}],
            max_tokens=50
        )
        
        response_text = response.choices[0].message.content
        
        print(f"✅ Azure OpenAI connection successful")
        print(f"   Deployment: {config['azure_openai']['deployment_name']}")
        print(f"   Test response: {response_text[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Azure OpenAI connection failed: {str(e)}")
        return False

def test_mapping_file():
    """Test mapping file"""
    print("\n🔍 Testing mapping file...")
    
    try:
        with open('mappings/column_mapping.json', 'r') as f:
            mapping = json.load(f)
        
        tables = mapping.get('tables', {})
        table_count = len(tables)
        
        print(f"✅ Mapping file loaded successfully")
        print(f"   Tables defined: {table_count}")
        
        # Validate mapping structure
        for table_name, table_config in tables.items():
            required_keys = ['source_table', 'target_table', 'columns']
            missing_keys = [key for key in required_keys if key not in table_config]
            
            if missing_keys:
                print(f"⚠️  Table {table_name} missing keys: {missing_keys}")
            else:
                column_count = len(table_config['columns'])
                print(f"   - {table_name}: {column_count} columns mapped")
        
        return True
        
    except FileNotFoundError:
        print("❌ Mapping file not found: mappings/column_mapping.json")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing mapping file: {e}")
        return False

def test_source_tables(config):
    """Test access to source tables defined in mapping"""
    print("\n🔍 Testing source table access...")
    
    try:
        # Load mapping
        with open('mappings/column_mapping.json', 'r') as f:
            mapping = json.load(f)
        
        # Connect to SQL Server
        conn_str = f"""
        DRIVER={{{config['sql_server']['driver']}}};
        SERVER={config['sql_server']['server']};
        DATABASE={config['sql_server']['database']};
        UID={config['sql_server']['username']};
        PWD={config['sql_server']['password']};
        Encrypt={config['sql_server'].get('encrypt', 'no')};
        TrustServerCertificate={config['sql_server'].get('trust_server_certificate', 'yes')};
        Connection Timeout={config['sql_server'].get('connection_timeout', 30)};
        """
        
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        accessible_tables = 0
        total_tables = len(mapping['tables'])
        
        for table_name, table_config in mapping['tables'].items():
            source_table = table_config['source_table']
            
            try:
                # Test table access and get row count
                cursor.execute(f"SELECT COUNT(*) FROM {source_table}")
                row_count = cursor.fetchone()[0]
                
                print(f"   ✅ {source_table}: {row_count} rows")
                accessible_tables += 1
                
            except Exception as e:
                print(f"   ❌ {source_table}: {str(e)}")
        
        conn.close()
        
        print(f"\nSource table summary: {accessible_tables}/{total_tables} tables accessible")
        return accessible_tables == total_tables
        
    except Exception as e:
        print(f"❌ Error testing source tables: {str(e)}")
        return False

async def main():
    """Run all connection tests"""
    print("Data Migration Agent - Connection Tests")
    print("======================================")
    
    # Load configuration
    config = load_config()
    if not config:
        return
    
    print("✅ Configuration file loaded successfully")
    
    # Run all tests
    tests = [
        ("SQL Server", lambda: test_sql_server_connection(config)),
        ("Databricks", lambda: test_databricks_connection(config)),
        ("Azure OpenAI", lambda: test_azure_openai_connection(config)),
        ("Mapping File", test_mapping_file),
        ("Source Tables", lambda: test_source_tables(config))
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {str(e)}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*50}")
    print("Test Summary:")
    print(f"{'='*50}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<15}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! You're ready to run the migration.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix the issues before running migration.")
        print("\nCommon fixes:")
        print("- Check credentials in config/config.yaml")
        print("- Ensure SQL Server allows remote connections")
        print("- Verify Databricks SQL warehouse is running")
        print("- Confirm Azure OpenAI deployment name is correct")

if __name__ == "__main__":
    asyncio.run(main())