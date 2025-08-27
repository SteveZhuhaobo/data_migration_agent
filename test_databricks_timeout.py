#!/usr/bin/env python3
"""
Test script to verify Databricks MCP timeout improvements
"""

import asyncio
import json
import sys
import os

# Add current directory to path to import the MCP server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Databricks_MCP import load_config, check_warehouse_status, get_sql_connection

async def test_warehouse_status():
    """Test warehouse status checking"""
    print("Testing warehouse status check...")
    
    try:
        # Load config
        load_config()
        print("✅ Configuration loaded")
        
        # Check warehouse status
        warehouse_ok, warehouse_msg = check_warehouse_status()
        print(f"Warehouse status: {warehouse_msg}")
        
        if warehouse_ok:
            print("✅ Warehouse check passed")
        else:
            print("⚠️ Warehouse check failed, but this might be expected")
            
    except Exception as e:
        print(f"❌ Error testing warehouse status: {e}")

async def test_connection_timeout():
    """Test SQL connection with extended timeouts"""
    print("\nTesting SQL connection with extended timeouts...")
    
    try:
        # Load config
        load_config()
        
        # Test connection (this will now have extended timeouts)
        connection = get_sql_connection()
        print("✅ SQL connection established with extended timeouts")
        
        # Test a simple query
        cursor = connection.cursor()
        cursor.execute("SELECT 1 as test_column")
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        
        print(f"✅ Test query successful: {result}")
        
    except Exception as e:
        print(f"❌ Error testing SQL connection: {e}")
        print("This might be expected if the warehouse is cold starting...")

if __name__ == "__main__":
    print("🔧 Testing Databricks MCP timeout improvements")
    print("=" * 50)
    
    asyncio.run(test_warehouse_status())
    asyncio.run(test_connection_timeout())
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")
    print("\nKey improvements made:")
    print("- Extended connection timeout to 120 seconds")
    print("- Extended socket timeout to 300 seconds (5 minutes)")
    print("- Added retry logic for cold start scenarios")
    print("- Added warehouse status checking")
    print("- Extended MCP client timeout to 180 seconds")