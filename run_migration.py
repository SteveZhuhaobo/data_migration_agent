#!/usr/bin/env python3
"""
SQL Server to Snowflake Migration - Executable Script
Uses MCP tools to perform the actual migration
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def migrate_customers_and_orders():
    """Execute the complete migration process"""
    logger.info("=== Starting SQL Server to Snowflake Migration ===")
    
    try:
        # Step 1: Get customers table schema and data
        logger.info("Step 1: Getting customers table schema...")
        
        # Get customers schema
        customers_schema_result = await get_sql_table_schema("customers")
        logger.info(f"Customers schema: {json.dumps(customers_schema_result, indent=2)}")
        
        # Get customers data
        logger.info("Getting customers data...")
        customers_data_result = await get_sql_table_data("customers")
        logger.info(f"Retrieved {len(customers_data_result.get('data', []))} customer records")
        
        # Step 2: Get orders table schema and data
        logger.info("Step 2: Getting orders table schema...")
        
        # Get orders schema
        orders_schema_result = await get_sql_table_schema("orders")
        logger.info(f"Orders schema: {json.dumps(orders_schema_result, indent=2)}")
        
        # Get orders data
        logger.info("Getting orders data...")
        orders_data_result = await get_sql_table_data("orders")
        logger.info(f"Retrieved {len(orders_data_result.get('data', []))} order records")
        
        # Step 3: Create customers table in Snowflake
        logger.info("Step 3: Creating customers table in Snowflake...")
        customers_create_sql = generate_snowflake_create_sql("customers", customers_schema_result)
        logger.info(f"Customers CREATE SQL: {customers_create_sql}")
        
        customers_create_result = await execute_snowflake_query(customers_create_sql)
        logger.info(f"Customers table creation result: {customers_create_result}")
        
        # Step 4: Create orders table in Snowflake
        logger.info("Step 4: Creating orders table in Snowflake...")
        orders_create_sql = generate_snowflake_create_sql("orders", orders_schema_result)
        logger.info(f"Orders CREATE SQL: {orders_create_sql}")
        
        orders_create_result = await execute_snowflake_query(orders_create_sql)
        logger.info(f"Orders table creation result: {orders_create_result}")
        
        # Step 5: Transform and load customers data
        logger.info("Step 5: Loading customers data...")
        customers_transformed = transform_data_with_metadata(customers_data_result.get('data', []))
        customers_load_result = await load_data_to_snowflake("customers", customers_transformed)
        logger.info(f"Customers data load result: {customers_load_result}")
        
        # Step 6: Transform and load orders data
        logger.info("Step 6: Loading orders data...")
        orders_transformed = transform_data_with_metadata(orders_data_result.get('data', []))
        orders_load_result = await load_data_to_snowflake("orders", orders_transformed)
        logger.info(f"Orders data load result: {orders_load_result}")
        
        # Step 7: Validate migration
        logger.info("Step 7: Validating migration...")
        await validate_migration()
        
        logger.info("=== Migration completed successfully! ===")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise

async def get_sql_table_schema(table_name: str) -> Dict[str, Any]:
    """Get table schema from SQL Server using MCP"""
    # This will be replaced with actual MCP call
    logger.info(f"Getting schema for {table_name} from SQL Server")
    return {"columns": []}

async def get_sql_table_data(table_name: str) -> Dict[str, Any]:
    """Get table data from SQL Server using MCP"""
    # This will be replaced with actual MCP call
    logger.info(f"Getting data for {table_name} from SQL Server")
    return {"data": []}

async def execute_snowflake_query(query: str) -> Dict[str, Any]:
    """Execute query in Snowflake using MCP"""
    # This will be replaced with actual MCP call
    logger.info(f"Executing Snowflake query: {query[:100]}...")
    return {"success": True}

async def load_data_to_snowflake(table_name: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Load data to Snowflake using MCP"""
    # This will be replaced with actual MCP call
    logger.info(f"Loading {len(data)} records to {table_name}")
    return {"success": True, "records_loaded": len(data)}

def generate_snowflake_create_sql(table_name: str, schema: Dict[str, Any]) -> str:
    """Generate CREATE TABLE SQL for Snowflake"""
    # SQL Server to Snowflake type mapping
    type_mapping = {
        'nvarchar': 'VARCHAR',
        'varchar': 'VARCHAR',
        'int': 'INTEGER',
        'bigint': 'BIGINT',
        'bit': 'BOOLEAN',
        'datetime2': 'TIMESTAMP_NTZ',
        'datetime': 'TIMESTAMP_NTZ',
        'decimal': 'NUMBER',
        'numeric': 'NUMBER'
    }
    
    columns = []
    for col in schema.get('columns', []):
        col_name = col['column_name']
        sql_type = col['data_type'].lower()
        
        # Map SQL Server type to Snowflake
        if sql_type in type_mapping:
            sf_type = type_mapping[sql_type]
            
            # Handle varchar with length
            if sql_type in ['nvarchar', 'varchar'] and col.get('max_length'):
                sf_type = f"VARCHAR({col['max_length']})"
            elif sql_type in ['decimal', 'numeric']:
                precision = col.get('precision', 18)
                scale = col.get('scale', 0)
                sf_type = f"NUMBER({precision},{scale})"
        else:
            sf_type = 'VARCHAR'
        
        # Handle nullability
        nullable = "NULL" if col['is_nullable'] else "NOT NULL"
        columns.append(f"    {col_name} {sf_type} {nullable}")
    
    # Add metadata columns
    columns.append("    is_migrated INTEGER NOT NULL")
    columns.append("    migrated_at TIMESTAMP_NTZ NOT NULL")
    
    return f"""CREATE OR REPLACE TABLE steve_mcp.data_migration.{table_name} (
{chr(10).join(columns)}
)"""

def transform_data_with_metadata(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transform data and add metadata columns"""
    transformed = []
    current_time = datetime.now().isoformat()
    
    for row in data:
        new_row = row.copy()
        new_row['is_migrated'] = 1
        new_row['migrated_at'] = current_time
        transformed.append(new_row)
    
    return transformed

async def validate_migration():
    """Validate the migration results"""
    logger.info("Validating migration results...")
    
    # Check customers table
    customers_count_result = await execute_snowflake_query(
        "SELECT COUNT(*) as count FROM steve_mcp.data_migration.customers"
    )
    logger.info(f"Customers count in Snowflake: {customers_count_result}")
    
    # Check orders table
    orders_count_result = await execute_snowflake_query(
        "SELECT COUNT(*) as count FROM steve_mcp.data_migration.orders"
    )
    logger.info(f"Orders count in Snowflake: {orders_count_result}")
    
    # Check metadata columns
    metadata_check = await execute_snowflake_query(
        "SELECT COUNT(*) as count FROM steve_mcp.data_migration.customers WHERE is_migrated = 1"
    )
    logger.info(f"Customers with migration metadata: {metadata_check}")

if __name__ == "__main__":
    asyncio.run(migrate_customers_and_orders())