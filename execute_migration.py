#!/usr/bin/env python3
"""
Execute SQL Server to Snowflake Migration
This script performs the actual migration using the available MCP tools
"""

import json
from datetime import datetime

def create_customers_table_sql():
    """Generate CREATE TABLE SQL for customers"""
    return """CREATE OR REPLACE TABLE steve_mcp.data_migration.customers (
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
)"""

def create_orders_table_sql():
    """Generate CREATE TABLE SQL for orders"""
    return """CREATE OR REPLACE TABLE steve_mcp.data_migration.orders (
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
)"""

def transform_customers_data(customers_data):
    """Transform customers data and add metadata"""
    transformed = []
    current_time = datetime.now().isoformat()
    
    for customer in customers_data:
        transformed_customer = {
            "CustomerID": customer["CustomerID"],
            "CompanyName": customer["CompanyName"],
            "ContactName": customer["ContactName"],
            "ContactTitle": customer["ContactTitle"],
            "Address": customer["Address"],
            "City": customer["City"],
            "Region": customer["Region"],
            "PostalCode": customer["PostalCode"],
            "Country": customer["Country"],
            "Phone": customer["Phone"],
            "Fax": customer["Fax"],
            "Email": customer["Email"],
            "IsActive": customer["IsActive"],
            "is_migrated": 1,
            "migrated_at": current_time
        }
        transformed.append(transformed_customer)
    
    return transformed

def transform_orders_data(orders_data):
    """Transform orders data and add metadata"""
    transformed = []
    current_time = datetime.now().isoformat()
    
    for order in orders_data:
        transformed_order = {
            "OrderID": order["OrderID"],
            "CustomerID": order["CustomerID"],
            "OrderDate": order["OrderDate"],
            "RequiredDate": order["RequiredDate"],
            "ShippedDate": order["ShippedDate"],
            "ShipVia": order["ShipVia"],
            "Freight": order["Freight"],
            "ShipName": order["ShipName"],
            "ShipAddress": order["ShipAddress"],
            "ShipCity": order["ShipCity"],
            "ShipRegion": order["ShipRegion"],
            "ShipPostalCode": order["ShipPostalCode"],
            "ShipCountry": order["ShipCountry"],
            "OrderStatus": order["OrderStatus"],
            "CreatedDate": order["CreatedDate"],
            "ModifiedDate": order["ModifiedDate"],
            "is_migrated": 1,
            "migrated_at": current_time
        }
        transformed.append(transformed_order)
    
    return transformed

# Sample data from our previous queries
customers_data = [
    {
        "CustomerID": "AAAAA",
        "CompanyName": "Blondel père et fils",
        "ContactName": "Frédérique Citeaux",
        "ContactTitle": "Marketing Manager",
        "Address": None,
        "City": "Strasbourg",
        "Region": None,
        "PostalCode": None,
        "Country": "France",
        "Phone": "88.60.15.31",
        "Fax": None,
        "Email": "frederique@blonp.com",
        "IsActive": True
    },
    {
        "CustomerID": "ALFKI",
        "CompanyName": "Alfreds Futterkiste",
        "ContactName": "Maria Anders",
        "ContactTitle": "Sales Representative",
        "Address": None,
        "City": "Berlin",
        "Region": None,
        "PostalCode": None,
        "Country": "Germany",
        "Phone": "030-0074321",
        "Fax": None,
        "Email": "maria@alfreds.com",
        "IsActive": True
    }
    # Add more customers as needed
]

orders_data = [
    {
        "OrderID": 1,
        "CustomerID": "ALFKI",
        "OrderDate": "2024-01-15 00:00:00",
        "RequiredDate": "2024-01-25 00:00:00",
        "ShippedDate": None,
        "ShipVia": None,
        "Freight": 0.0,
        "ShipName": "Alfreds Futterkiste",
        "ShipAddress": None,
        "ShipCity": "Berlin",
        "ShipRegion": None,
        "ShipPostalCode": None,
        "ShipCountry": "Germany",
        "OrderStatus": "Shipped",
        "CreatedDate": "2025-07-24 10:48:51",
        "ModifiedDate": "2025-07-24 10:48:51"
    }
    # Add more orders as needed
]

if __name__ == "__main__":
    print("=== SQL Server to Snowflake Migration ===")
    print("1. Creating customers table SQL:")
    print(create_customers_table_sql())
    print("\n2. Creating orders table SQL:")
    print(create_orders_table_sql())
    print("\n3. Sample transformed customers data:")
    transformed_customers = transform_customers_data(customers_data[:2])
    print(json.dumps(transformed_customers, indent=2))
    print("\n4. Sample transformed orders data:")
    transformed_orders = transform_orders_data(orders_data[:1])
    print(json.dumps(transformed_orders, indent=2))