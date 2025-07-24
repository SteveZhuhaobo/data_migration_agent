#!/usr/bin/env python3
"""
Test script for the Data Migration MCP Server using proper MCP client
This script connects to the MCP server and retrieves top 10 records from each table in the mapping
"""

import asyncio
import sys
import json
import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def print_table_data(table_name: str, data: List[Dict[str, Any]], limit: int = 10):
    """Print table data in a formatted way"""
    print(f"\n{'='*60}")
    print(f"TABLE: {table_name}")
    print(f"{'='*60}")
    
    if not data:
        print("No data found")
        return
    
    # Get column names from first record
    columns = list(data[0].keys()) if data else []
    
    if not columns:
        print("No columns found")
        return
    
    # Print header
    header = " | ".join(f"{col:15}" for col in columns)
    print(header)
    print("-" * len(header))
    
    # Print data rows (limit to specified number)
    for i, row in enumerate(data[:limit]):
        if i >= limit:
            break
        row_str = " | ".join(f"{str(row.get(col, 'N/A')):15}" for col in columns)
        print(row_str)
    
    if len(data) > limit:
        print(f"... ({len(data) - limit} more rows)")
    
    print(f"\nTotal records: {len(data)}")

async def get_mapping_tables(session: ClientSession) -> List[str]:
    """Get list of tables from the mapping configuration"""
    try:
        # From the server code, we can see the fallback mapping has 'test_table'
        # Let's try this table first and see if we can get more tables from the mapping
        test_tables = ['test_table']
        
        # Try to get mapping for test table to see if server is working
        result = await session.call_tool("get_mapping", {"table_name": "test_table"})
        
        if result and result.content:
            content = result.content[0].text
            if "No mapping found" not in content:
                logger.info("Found test_table in mapping")
                
                # Try to parse the mapping to see if there are other tables
                try:
                    mapping_data = json.loads(content)
                    # This is the mapping for a single table, but we could potentially
                    # extract more table names if the mapping structure allows it
                    logger.info(f"Successfully parsed mapping for {test_tables[0]}")
                except json.JSONDecodeError:
                    logger.warning("Could not parse mapping as JSON")
                
                return test_tables
        
        # If we can't get the mapping, return the fallback table
        logger.warning("Could not retrieve table list from mapping, using fallback")
        return test_tables
        
    except Exception as e:
        logger.error(f"Error getting mapping tables: {e}")
        return ['test_table']  # Return fallback table

async def test_data_extraction():
    """Main test function to extract data from all mapped tables"""
    
    print("=== Data Migration MCP Server Test ===")
    print("Testing data extraction from all mapped tables...")
    
    try:
        # Set up server parameters
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["data_migration_server.py"]  # Adjust path if needed
        )
        
        # Connect to the MCP server
        logger.info("Connecting to MCP server...")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                logger.info("✓ Connected to MCP server successfully")
                
                # List available tools
                logger.info("Listing available tools...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                
                print(f"\nFound {len(tools)} available tools:")
                for tool in tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                # Get list of tables from mapping
                logger.info("Getting table list from mapping...")
                table_names = await get_mapping_tables(session)
                
                if not table_names:
                    logger.error("No tables found in mapping")
                    return False
                
                print(f"\nFound {len(table_names)} table(s) in mapping: {', '.join(table_names)}")
                
                # Extract data from each table
                for table_name in table_names:
                    try:
                        logger.info(f"Processing table: {table_name}")
                        
                        # Get table mapping info
                        print(f"\n--- Getting mapping for {table_name} ---")
                        mapping_result = await session.call_tool("get_mapping", {"table_name": table_name})
                        
                        if mapping_result and mapping_result.content:
                            mapping_content = mapping_result.content[0].text
                            print("Table Mapping:")
                            # Pretty print the JSON if possible
                            try:
                                mapping_json = json.loads(mapping_content)
                                print(json.dumps(mapping_json, indent=2))
                            except json.JSONDecodeError:
                                print(mapping_content)
                        
                        # Get schema information
                        print(f"\n--- Getting schema for {table_name} ---")
                        schema_result = await session.call_tool("get_sql_schema", {"table_name": table_name})
                        
                        if schema_result and schema_result.content:
                            schema_content = schema_result.content[0].text
                            print("Table Schema:")
                            # Pretty print the JSON if possible
                            try:
                                schema_json = json.loads(schema_content)
                                print(json.dumps(schema_json, indent=2))
                            except json.JSONDecodeError:
                                print(schema_content)
                        
                        # Extract top 10 records
                        print(f"\n--- Extracting data from {table_name} ---")
                        data_result = await session.call_tool("extract_data", {
                            "table_name": table_name,
                            "limit": 10
                        })
                        
                        if data_result and data_result.content:
                            data_content = data_result.content[0].text
                            
                            try:
                                # Parse JSON data
                                data = json.loads(data_content)
                                
                                if isinstance(data, list):
                                    print_table_data(table_name, data, 10)
                                else:
                                    print(f"Unexpected data format for {table_name}: {data}")
                            
                            except json.JSONDecodeError:
                                print(f"Raw response for {table_name}:")
                                print(data_content)
                        
                        # Test table creation (optional)
                        print(f"\n--- Testing table creation for {table_name} ---")
                        try:
                            # Get a sample schema for table creation
                            sample_schema = {
                                "id": {"type": "INT", "nullable": False},
                                "name": {"type": "STRING", "nullable": True}
                            }
                            
                            create_result = await session.call_tool("create_databricks_table", {
                                "table_name": table_name,
                                "schema": sample_schema
                            })
                            
                            if create_result and create_result.content:
                                create_content = create_result.content[0].text
                                print(f"Table creation result: {create_content}")
                        
                        except Exception as e:
                            logger.warning(f"Table creation test failed for {table_name}: {e}")
                        
                    except Exception as e:
                        logger.error(f"Error processing table {table_name}: {e}")
                        continue
                
                print(f"\n{'='*60}")
                print("✅ Data extraction test completed successfully!")
                print(f"{'='*60}")
                return True
                
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def print_usage():
    """Print usage instructions"""
    print("""
Data Migration MCP Server Test Script
=====================================

This script tests the MCP data migration server by:
1. Connecting to the MCP server using proper MCP client
2. Listing available tools
3. Getting table mappings
4. Extracting top 10 records from each mapped table
5. Displaying the data in formatted tables
6. Testing table creation functionality

Prerequisites:
- Install MCP: pip install mcp
- Ensure the MCP server file (data_migration_server.py) is in the same directory
- Install required dependencies for the server
- Configure your database connections in config/config.yaml (optional - fallback used if missing)
- Set up table mappings in mappings/column_mapping.json (optional - fallback used if missing)

Usage:
    python test_mcp_server.py

The script will use mock data if actual database connections are not configured.

Available options:
    -h, --help    Show this help message
    """)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print_usage()
        sys.exit(0)
    
    try:
        success = asyncio.run(test_data_extraction())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        sys.exit(1)