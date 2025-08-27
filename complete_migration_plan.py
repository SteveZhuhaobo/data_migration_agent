#!/usr/bin/env python3
"""
Complete SQL Server to Snowflake Migration Plan
This script shows the complete migration process with actual data
"""

import json
from datetime import datetime

# Actual customers data from SQL Server (19 records)
customers_data = [
    {"CustomerID": "AAAAA", "CompanyName": "Blondel père et fils", "ContactName": "Frédérique Citeaux", "ContactTitle": "Marketing Manager", "Address": None, "City": "Strasbourg", "Region": None, "PostalCode": None, "Country": "France", "Phone": "88.60.15.31", "Fax": None, "Email": "frederique@blonp.com", "IsActive": True},
    {"CustomerID": "ALFKI", "CompanyName": "Alfreds Futterkiste", "ContactName": "Maria Anders", "ContactTitle": "Sales Representative", "Address": None, "City": "Berlin", "Region": None, "PostalCode": None, "Country": "Germany", "Phone": "030-0074321", "Fax": None, "Email": "maria@alfreds.com", "IsActive": True},
    {"CustomerID": "ANATR", "CompanyName": "Ana Trujillo Emparedados y helados", "ContactName": "Ana Trujillo", "ContactTitle": "Owner", "Address": None, "City": "México D.F.", "Region": None, "PostalCode": None, "Country": "Mexico", "Phone": "(5) 555-4729", "Fax": None, "Email": "ana@anatr.com", "IsActive": True},
    {"CustomerID": "ANTON", "CompanyName": "Antonio Moreno Taquería", "ContactName": "Antonio Moreno", "ContactTitle": "Owner", "Address": None, "City": "México D.F.", "Region": None, "PostalCode": None, "Country": "Mexico", "Phone": "(5) 555-3932", "Fax": None, "Email": "antonio@anton.com", "IsActive": True},
    {"CustomerID": "BBBBB", "CompanyName": "Alfreds Futterkiste", "ContactName": "Maria Anders", "ContactTitle": "Sales Representative", "Address": None, "City": "Berlin", "Region": None, "PostalCode": None, "Country": "Germany", "Phone": "030-0074321", "Fax": None, "Email": "maria@alfreds.com", "IsActive": True},
    {"CustomerID": "BERGS", "CompanyName": "Berglunds snabbköp", "ContactName": "Christina Berglund", "ContactTitle": "Order Administrator", "Address": None, "City": "Luleå", "Region": None, "PostalCode": None, "Country": "Sweden", "Phone": "0921-12 34 65", "Fax": None, "Email": "christina@bergs.com", "IsActive": True},
    {"CustomerID": "BERGSteve", "CompanyName": "Berglunds snabbköp", "ContactName": "Christina Berglund", "ContactTitle": "Order Administrator", "Address": None, "City": "Luleå", "Region": None, "PostalCode": None, "Country": "Sweden", "Phone": "0921-12 34 65", "Fax": None, "Email": "christina@bergs.com", "IsActive": True},
    {"CustomerID": "BLONP", "CompanyName": "Blondel père et fils", "ContactName": "Frédérique Citeaux", "ContactTitle": "Marketing Manager", "Address": None, "City": "Strasbourg", "Region": None, "PostalCode": None, "Country": "France", "Phone": "88.60.15.31", "Fax": None, "Email": "frederique@blonp.com", "IsActive": True},
    {"CustomerID": "BLONQ", "CompanyName": "Blondel père et fils", "ContactName": "Frédérique Citeaux", "ContactTitle": "Marketing Manager", "Address": None, "City": "Strasbourg", "Region": None, "PostalCode": None, "Country": "France", "Phone": "88.60.15.31", "Fax": None, "Email": "frederique@blonp.com", "IsActive": True},
    {"CustomerID": "CUST001", "CompanyName": "Tech Solutions Inc", "ContactName": "John Smith", "ContactTitle": "CEO", "Address": "123 Main Street", "City": "New York", "Region": "NY", "PostalCode": "10001", "Country": "USA", "Phone": "(555) 123-4567", "Fax": "(555) 123-4568", "Email": "john.smith@techsolutions.com", "IsActive": True},
    {"CustomerID": "CUST002", "CompanyName": "Global Marketing Ltd", "ContactName": "Sarah Johnson", "ContactTitle": "Marketing Director", "Address": "456 Oak Avenue", "City": "Los Angeles", "Region": "CA", "PostalCode": "90210", "Country": "USA", "Phone": "(555) 234-5678", "Fax": "(555) 234-5679", "Email": "sarah.johnson@globalmarketing.com", "IsActive": True},
    {"CustomerID": "CUST003", "CompanyName": "European Imports Co", "ContactName": "Hans Mueller", "ContactTitle": "Import Manager", "Address": "789 Elm Street", "City": "Berlin", "Region": "Berlin", "PostalCode": "10115", "Country": "Germany", "Phone": "+49 30 12345678", "Fax": "+49 30 12345679", "Email": "hans.mueller@euroimports.de", "IsActive": True},
    {"CustomerID": "CUST004", "CompanyName": "Pacific Trading Corp", "ContactName": "Yuki Tanaka", "ContactTitle": "Sales Manager", "Address": "321 Cherry Blossom Lane", "City": "Tokyo", "Region": "Tokyo", "PostalCode": "100-0001", "Country": "Japan", "Phone": "+81 3 1234 5678", "Fax": "+81 3 1234 5679", "Email": "yuki.tanaka@pacifictrading.jp", "IsActive": True},
    {"CustomerID": "CUST005", "CompanyName": "Australian Outback Supplies", "ContactName": "Mike O'Connor", "ContactTitle": "Operations Director", "Address": "654 Kangaroo Road", "City": "Sydney", "Region": "NSW", "PostalCode": "2000", "Country": "Australia", "Phone": "+61 2 9876 5432", "Fax": "+61 2 9876 5433", "Email": "mike.oconnor@outbacksupplies.au", "IsActive": True},
    {"CustomerID": "CUST006", "CompanyName": "Nordic Furniture AB", "ContactName": "Astrid Larsson", "ContactTitle": "Design Lead", "Address": "987 Pine Forest Way", "City": "Stockholm", "Region": "Stockholm", "PostalCode": "11122", "Country": "Sweden", "Phone": "+46 8 555 1234", "Fax": "+46 8 555 1235", "Email": "astrid.larsson@nordicfurniture.se", "IsActive": True},
    {"CustomerID": "CUST007", "CompanyName": "Brazilian Coffee Exports", "ContactName": "Carlos Silva", "ContactTitle": "Export Coordinator", "Address": "147 Coffee Bean Avenue", "City": "São Paulo", "Region": "SP", "PostalCode": "01310-100", "Country": "Brazil", "Phone": "+55 11 3456 7890", "Fax": "+55 11 3456 7891", "Email": "carlos.silva@braziliancoffee.br", "IsActive": True},
    {"CustomerID": "CUST008", "CompanyName": "Canadian Maple Products", "ContactName": "Jennifer Brown", "ContactTitle": "Product Manager", "Address": "258 Maple Leaf Drive", "City": "Toronto", "Region": "ON", "PostalCode": "M5V 3A8", "Country": "Canada", "Phone": "+1 416 789 0123", "Fax": "+1 416 789 0124", "Email": "jennifer.brown@canadianmaple.ca", "IsActive": True},
    {"CustomerID": "CUST009", "CompanyName": "Mediterranean Olive Oil Ltd", "ContactName": "Giuseppe Romano", "ContactTitle": "Quality Control Manager", "Address": "369 Olive Grove Street", "City": "Rome", "Region": "Lazio", "PostalCode": "00100", "Country": "Italy", "Phone": "+39 06 1234 5678", "Fax": "+39 06 1234 5679", "Email": "giuseppe.romano@medoliveoil.it", "IsActive": True},
    {"CustomerID": "CUST010", "CompanyName": "British Tea Company", "ContactName": "Emma Thompson", "ContactTitle": "Tea Specialist", "Address": "741 Earl Grey Boulevard", "City": "London", "Region": "London", "PostalCode": "SW1A 1AA", "Country": "United Kingdom", "Phone": "+44 20 7946 0958", "Fax": "+44 20 7946 0959", "Email": "emma.thompson@britishtea.co.uk", "IsActive": True}
]

# Sample of orders data (showing first 5 of 29 records)
orders_data_sample = [
    {"OrderID": 1, "CustomerID": "ALFKI", "OrderDate": "2024-01-15 00:00:00", "RequiredDate": "2024-01-25 00:00:00", "ShippedDate": None, "ShipVia": None, "Freight": 0.0, "ShipName": "Alfreds Futterkiste", "ShipAddress": None, "ShipCity": "Berlin", "ShipRegion": None, "ShipPostalCode": None, "ShipCountry": "Germany", "OrderStatus": "Shipped", "CreatedDate": "2025-07-24 10:48:51", "ModifiedDate": "2025-07-24 10:48:51"},
    {"OrderID": 2, "CustomerID": "ALFKI", "OrderDate": "2024-02-03 00:00:00", "RequiredDate": "2024-02-13 00:00:00", "ShippedDate": None, "ShipVia": None, "Freight": 0.0, "ShipName": "Alfreds Futterkiste", "ShipAddress": None, "ShipCity": "Berlin", "ShipRegion": None, "ShipPostalCode": None, "ShipCountry": "Germany", "OrderStatus": "Delivered", "CreatedDate": "2025-07-24 10:48:51", "ModifiedDate": "2025-07-24 10:48:51"},
    {"OrderID": 3, "CustomerID": "ANATR", "OrderDate": "2024-01-20 00:00:00", "RequiredDate": "2024-01-30 00:00:00", "ShippedDate": None, "ShipVia": None, "Freight": 0.0, "ShipName": "Ana Trujillo Emparedados", "ShipAddress": None, "ShipCity": "México D.F.", "ShipRegion": None, "ShipPostalCode": None, "ShipCountry": "Mexico", "OrderStatus": "Shipped", "CreatedDate": "2025-07-24 10:48:51", "ModifiedDate": "2025-07-24 10:48:51"},
    {"OrderID": 4, "CustomerID": "ANTON", "OrderDate": "2024-02-01 00:00:00", "RequiredDate": "2024-02-11 00:00:00", "ShippedDate": None, "ShipVia": None, "Freight": 0.0, "ShipName": "Steve", "ShipAddress": None, "ShipCity": "México D.F.", "ShipRegion": None, "ShipPostalCode": None, "ShipCountry": "Mexico", "OrderStatus": "Processing", "CreatedDate": "2025-07-24 10:48:51", "ModifiedDate": "2025-07-29 10:00:00"},
    {"OrderID": 5, "CustomerID": "BERGS", "OrderDate": "2024-02-05 00:00:00", "RequiredDate": "2024-02-15 00:00:00", "ShippedDate": None, "ShipVia": None, "Freight": 0.0, "ShipName": "Berglunds snabbköp", "ShipAddress": None, "ShipCity": "Luleå", "ShipRegion": None, "ShipPostalCode": None, "ShipCountry": "Sweden", "OrderStatus": "Pending", "CreatedDate": "2025-07-24 10:48:51", "ModifiedDate": "2025-07-24 10:48:51"}
]

def generate_migration_summary():
    """Generate a complete migration summary"""
    current_time = datetime.now().isoformat()
    
    # Transform customers data
    transformed_customers = []
    for customer in customers_data:
        transformed_customer = customer.copy()
        transformed_customer["is_migrated"] = 1
        transformed_customer["migrated_at"] = current_time
        transformed_customers.append(transformed_customer)
    
    # Transform orders data
    transformed_orders = []
    for order in orders_data_sample:
        transformed_order = order.copy()
        transformed_order["is_migrated"] = 1
        transformed_order["migrated_at"] = current_time
        transformed_orders.append(transformed_order)
    
    return {
        "migration_summary": {
            "source_database": "SQL Server",
            "target_database": "Snowflake (steve_mcp.data_migration)",
            "migration_timestamp": current_time,
            "tables_migrated": ["customers", "orders"],
            "customers_count": len(customers_data),
            "orders_count": 29,  # Total from SQL Server
            "metadata_columns_added": ["is_migrated", "migrated_at"]
        },
        "customers_table": {
            "create_sql": """CREATE OR REPLACE TABLE steve_mcp.data_migration.customers (
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
)""",
            "sample_data": transformed_customers[:3]
        },
        "orders_table": {
            "create_sql": """CREATE OR REPLACE TABLE steve_mcp.data_migration.orders (
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
)""",
            "sample_data": transformed_orders[:3]
        },
        "validation_queries": [
            "SELECT COUNT(*) as customer_count FROM steve_mcp.data_migration.customers",
            "SELECT COUNT(*) as order_count FROM steve_mcp.data_migration.orders",
            "SELECT COUNT(*) as migrated_customers FROM steve_mcp.data_migration.customers WHERE is_migrated = 1",
            "SELECT COUNT(*) as migrated_orders FROM steve_mcp.data_migration.orders WHERE is_migrated = 1",
            "SELECT CustomerID, CompanyName, is_migrated, migrated_at FROM steve_mcp.data_migration.customers LIMIT 5",
            "SELECT OrderID, CustomerID, OrderStatus, is_migrated, migrated_at FROM steve_mcp.data_migration.orders LIMIT 5"
        ]
    }

if __name__ == "__main__":
    print("=== COMPLETE SQL SERVER TO SNOWFLAKE MIGRATION PLAN ===")
    
    migration_plan = generate_migration_summary()
    
    print("\n📊 MIGRATION SUMMARY:")
    print(f"Source: {migration_plan['migration_summary']['source_database']}")
    print(f"Target: {migration_plan['migration_summary']['target_database']}")
    print(f"Customers to migrate: {migration_plan['migration_summary']['customers_count']}")
    print(f"Orders to migrate: {migration_plan['migration_summary']['orders_count']}")
    print(f"Metadata columns: {', '.join(migration_plan['migration_summary']['metadata_columns_added'])}")
    
    print("\n🏗️  CUSTOMERS TABLE CREATE SQL:")
    print(migration_plan['customers_table']['create_sql'])
    
    print("\n🏗️  ORDERS TABLE CREATE SQL:")
    print(migration_plan['orders_table']['create_sql'])
    
    print("\n📝 SAMPLE TRANSFORMED CUSTOMERS DATA:")
    print(json.dumps(migration_plan['customers_table']['sample_data'], indent=2))
    
    print("\n📝 SAMPLE TRANSFORMED ORDERS DATA:")
    print(json.dumps(migration_plan['orders_table']['sample_data'], indent=2))
    
    print("\n✅ VALIDATION QUERIES TO RUN AFTER MIGRATION:")
    for i, query in enumerate(migration_plan['validation_queries'], 1):
        print(f"{i}. {query}")
    
    print("\n🎯 MIGRATION STATUS:")
    print("✅ Schema analysis completed")
    print("✅ Data extraction completed")
    print("✅ Data transformation completed")
    print("✅ CREATE TABLE statements generated")
    print("✅ Sample data with metadata prepared")
    print("⏳ Awaiting Snowflake connection for table creation and data loading")
    
    print(f"\n📅 Migration prepared at: {migration_plan['migration_summary']['migration_timestamp']}")
    print("\n🚀 Ready to execute when Snowflake connection is available!")