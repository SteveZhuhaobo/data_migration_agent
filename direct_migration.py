#!/usr/bin/env python3
"""
Direct SQL Server to Snowflake Migration
Uses direct connections with the correct account format
"""

import snowflake.connector
import pyodbc
import yaml
import json
from datetime import datetime
from typing import List, Dict, Any

def load_config():
    """Load configuration"""
    with open("config/config.yaml", 'r') as f:
        return yaml.safe_load(f)

def get_sql_server_connection(config):
    """Create SQL Server connection"""
    sql_config = config['sql_server']
    
    if sql_config['use_windows_auth']:
        conn_str = f"DRIVER={{{sql_config['driver']}}};SERVER={sql_config['server']};DATABASE={sql_config['database']};Trusted_Connection=yes;Encrypt={sql_config['encrypt']};TrustServerCertificate={sql_config['trust_server_certificate']}"
    else:
        conn_str = f"DRIVER={{{sql_config['driver']}}};SERVER={sql_config['server']};DATABASE={sql_config['database']};UID={sql_config['username']};PWD={sql_config['password']};Encrypt={sql_config['encrypt']};TrustServerCertificate={sql_config['trust_server_certificate']}"
    
    return pyodbc.connect(conn_str)

def get_snowflake_connection(config):
    """Create Snowflake connection with correct account format"""
    sf_config = config['snowflake']
    
    return snowflake.connector.connect(
        account="MZLGTMY-ZL90213",  # Use the working format
        user=sf_config['user'],
        password=sf_config['password'],
        database=sf_config['database'],
        schema=sf_config['schema'],
        warehouse=sf_config['warehouse'],
        role=sf_config.get('role', 'accountadmin')
    )

def extract_customers_data(sql_conn):
    """Extract customers data from SQL Server"""
    cursor = sql_conn.cursor()
    cursor.execute("SELECT * FROM customers")
    
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()
    
    data = []
    for row in rows:
        row_dict = {}
        for i, value in enumerate(row):
            row_dict[columns[i]] = value
        data.append(row_dict)
    
    cursor.close()
    return data

def extract_orders_data(sql_conn):
    """Extract orders data from SQL Server"""
    cursor = sql_conn.cursor()
    cursor.execute("""
        SELECT OrderID, CustomerID, 
               CONVERT(varchar, OrderDate, 120) as OrderDate,
               CONVERT(varchar, RequiredDate, 120) as RequiredDate,
               CONVERT(varchar, ShippedDate, 120) as ShippedDate,
               ShipVia, CAST(Freight as float) as Freight,
               ShipName, ShipAddress, ShipCity, ShipRegion, 
               ShipPostalCode, ShipCountry, OrderStatus,
               CONVERT(varchar, CreatedDate, 120) as CreatedDate,
               CONVERT(varchar, ModifiedDate, 120) as ModifiedDate
        FROM orders
    """)
    
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()
    
    data = []
    for row in rows:
        row_dict = {}
        for i, value in enumerate(row):
            row_dict[columns[i]] = value
        data.append(row_dict)
    
    cursor.close()
    return data

def create_customers_table(sf_conn):
    """Create customers table in Snowflake"""
    cursor = sf_conn.cursor()
    
    create_sql = """
    CREATE OR REPLACE TABLE steve_mcp.data_migration.customers (
        CustomerID VARCHAR(50) NOT NULL,
        CompanyName VARCHAR(255) NOT NULL,
        ContactName VARCHAR(100) NULL,
        ContactTitle VARCHAR(50) NULL,
        Address VARCHAR(255) NULL,
        City VARCHAR(50) NULL,
        Region VARCHAR(50) NULL,
        PostalCode VARCHAR(20) NULL,
        Country VARCHAR(50) NULL,
        Phone VARCHAR(30) NULL,
        Fax VARCHAR(30) NULL,
        Email VARCHAR(100) NULL,
        IsActive BOOLEAN NULL,
        is_migrated INTEGER NOT NULL,
        migrated_at TIMESTAMP_NTZ NOT NULL
    )
    """
    
    cursor.execute(create_sql)
    cursor.close()
    print("✅ Customers table created successfully")

def create_orders_table(sf_conn):
    """Create orders table in Snowflake"""
    cursor = sf_conn.cursor()
    
    create_sql = """
    CREATE OR REPLACE TABLE steve_mcp.data_migration.orders (
        OrderID INTEGER NOT NULL,
        CustomerID VARCHAR(50) NOT NULL,
        OrderDate TIMESTAMP_NTZ NOT NULL,
        RequiredDate TIMESTAMP_NTZ NULL,
        ShippedDate TIMESTAMP_NTZ NULL,
        ShipVia INTEGER NULL,
        Freight NUMBER(10,2) NULL,
        ShipName VARCHAR(100) NULL,
        ShipAddress VARCHAR(255) NULL,
        ShipCity VARCHAR(50) NULL,
        ShipRegion VARCHAR(50) NULL,
        ShipPostalCode VARCHAR(20) NULL,
        ShipCountry VARCHAR(50) NULL,
        OrderStatus VARCHAR(20) NULL,
        CreatedDate TIMESTAMP_NTZ NULL,
        ModifiedDate TIMESTAMP_NTZ NULL,
        is_migrated INTEGER NOT NULL,
        migrated_at TIMESTAMP_NTZ NOT NULL
    )
    """
    
    cursor.execute(create_sql)
    cursor.close()
    print("✅ Orders table created successfully")

def load_customers_data(sf_conn, customers_data):
    """Load customers data into Snowflake"""
    cursor = sf_conn.cursor()
    current_time = datetime.now().isoformat()
    
    for customer in customers_data:
        insert_sql = """
        INSERT INTO steve_mcp.data_migration.customers (
            CustomerID, CompanyName, ContactName, ContactTitle, Address, City, Region,
            PostalCode, Country, Phone, Fax, Email, IsActive, is_migrated, migrated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(insert_sql, (
            customer['CustomerID'],
            customer['CompanyName'],
            customer['ContactName'],
            customer['ContactTitle'],
            customer['Address'],
            customer['City'],
            customer['Region'],
            customer['PostalCode'],
            customer['Country'],
            customer['Phone'],
            customer['Fax'],
            customer['Email'],
            customer['IsActive'],
            1,  # is_migrated
            current_time  # migrated_at
        ))
    
    cursor.close()
    print(f"✅ Loaded {len(customers_data)} customer records")

def load_orders_data(sf_conn, orders_data):
    """Load orders data into Snowflake"""
    cursor = sf_conn.cursor()
    current_time = datetime.now().isoformat()
    
    for order in orders_data:
        insert_sql = """
        INSERT INTO steve_mcp.data_migration.orders (
            OrderID, CustomerID, OrderDate, RequiredDate, ShippedDate, ShipVia, Freight,
            ShipName, ShipAddress, ShipCity, ShipRegion, ShipPostalCode, ShipCountry,
            OrderStatus, CreatedDate, ModifiedDate, is_migrated, migrated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(insert_sql, (
            order['OrderID'],
            order['CustomerID'],
            order['OrderDate'],
            order['RequiredDate'],
            order['ShippedDate'],
            order['ShipVia'],
            order['Freight'],
            order['ShipName'],
            order['ShipAddress'],
            order['ShipCity'],
            order['ShipRegion'],
            order['ShipPostalCode'],
            order['ShipCountry'],
            order['OrderStatus'],
            order['CreatedDate'],
            order['ModifiedDate'],
            1,  # is_migrated
            current_time  # migrated_at
        ))
    
    cursor.close()
    print(f"✅ Loaded {len(orders_data)} order records")

def validate_migration(sf_conn):
    """Validate the migration results"""
    cursor = sf_conn.cursor()
    
    # Check customers count
    cursor.execute("SELECT COUNT(*) FROM steve_mcp.data_migration.customers")
    customers_count = cursor.fetchone()[0]
    
    # Check orders count
    cursor.execute("SELECT COUNT(*) FROM steve_mcp.data_migration.orders")
    orders_count = cursor.fetchone()[0]
    
    # Check metadata columns
    cursor.execute("SELECT COUNT(*) FROM steve_mcp.data_migration.customers WHERE is_migrated = 1")
    migrated_customers = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM steve_mcp.data_migration.orders WHERE is_migrated = 1")
    migrated_orders = cursor.fetchone()[0]
    
    cursor.close()
    
    print(f"\n📊 MIGRATION VALIDATION:")
    print(f"Customers migrated: {customers_count}")
    print(f"Orders migrated: {orders_count}")
    print(f"Customers with metadata: {migrated_customers}")
    print(f"Orders with metadata: {migrated_orders}")
    
    return {
        "customers_count": customers_count,
        "orders_count": orders_count,
        "migrated_customers": migrated_customers,
        "migrated_orders": migrated_orders
    }

def main():
    """Execute the complete migration"""
    print("=== DIRECT SQL SERVER TO SNOWFLAKE MIGRATION ===")
    
    try:
        # Load configuration
        config = load_config()
        
        # Connect to SQL Server
        print("🔌 Connecting to SQL Server...")
        sql_conn = get_sql_server_connection(config)
        
        # Connect to Snowflake
        print("🔌 Connecting to Snowflake...")
        sf_conn = get_snowflake_connection(config)
        
        # Extract data from SQL Server
        print("📤 Extracting customers data...")
        customers_data = extract_customers_data(sql_conn)
        
        print("📤 Extracting orders data...")
        orders_data = extract_orders_data(sql_conn)
        
        # Create tables in Snowflake
        print("🏗️  Creating customers table...")
        create_customers_table(sf_conn)
        
        print("🏗️  Creating orders table...")
        create_orders_table(sf_conn)
        
        # Load data into Snowflake
        print("📥 Loading customers data...")
        load_customers_data(sf_conn, customers_data)
        
        print("📥 Loading orders data...")
        load_orders_data(sf_conn, orders_data)
        
        # Validate migration
        print("✅ Validating migration...")
        validation_results = validate_migration(sf_conn)
        
        # Close connections
        sql_conn.close()
        sf_conn.close()
        
        print("\n🎉 MIGRATION COMPLETED SUCCESSFULLY!")
        print(f"✅ {validation_results['customers_count']} customers migrated")
        print(f"✅ {validation_results['orders_count']} orders migrated")
        print("✅ All records include migration metadata (is_migrated=1, migrated_at=timestamp)")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()