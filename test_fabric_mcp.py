#!/usr/bin/env python3
"""
Test script for Microsoft Fabric MCP Server
"""

import asyncio
import json
import sys
import os

# Add the current directory to the path so we can import the MCP server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Fabric_MCP import (
    load_config, 
    validate_connection, 
    test_authentication,
    ping_tool,
    test_connection_tool
)

async def test_basic_functionality():
    """Test basic MCP server functionality"""
    print("Testing Microsoft Fabric MCP Server...")
    print("=" * 50)
    
    try:
        # Test 1: Configuration loading
        print("1. Testing configuration loading...")
        try:
            load_config()
            print("   ✓ Configuration loaded successfully")
        except Exception as e:
            print(f"   ✗ Configuration loading failed: {e}")
            print("   Note: Make sure you have a config/config.yaml file with proper Fabric settings")
            return
        
        # Test 2: Configuration validation
        print("2. Testing configuration validation...")
        try:
            validate_connection()
            print("   ✓ Configuration validation passed")
        except Exception as e:
            print(f"   ✗ Configuration validation failed: {e}")
            return
        
        # Test 3: Ping tool
        print("3. Testing ping tool...")
        try:
            ping_result = await ping_tool()
            ping_data = json.loads(ping_result)
            if ping_data.get('success'):
                print("   ✓ Ping tool working")
            else:
                print(f"   ✗ Ping tool failed: {ping_data.get('error')}")
        except Exception as e:
            print(f"   ✗ Ping tool error: {e}")
        
        # Test 4: Connection test (includes authentication)
        print("4. Testing connection and authentication...")
        try:
            connection_result = await test_connection_tool()
            connection_data = json.loads(connection_result)
            if connection_data.get('success'):
                print("   ✓ Connection and authentication successful")
                print(f"   Tenant ID: {connection_data.get('tenant_id')}")
                print(f"   Client ID: {connection_data.get('client_id')}")
                print(f"   Workspace ID: {connection_data.get('workspace_id')}")
            else:
                print(f"   ✗ Connection test failed: {connection_data.get('error')}")
                print("   Note: Make sure your Azure credentials are correct and you have proper permissions")
        except Exception as e:
            print(f"   ✗ Connection test error: {e}")
        
        print("\n" + "=" * 50)
        print("Basic functionality test completed!")
        print("\nNext steps:")
        print("1. Configure your config/config.yaml file with proper Fabric credentials")
        print("2. Test the MCP server with a real MCP client")
        print("3. Try the various tools like list_workspaces, list_lakehouses, etc.")
        
    except Exception as e:
        print(f"Unexpected error during testing: {e}")

if __name__ == "__main__":
    asyncio.run(test_basic_functionality())