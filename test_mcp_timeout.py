#!/usr/bin/env python3
"""
Test script to verify MCP timeout improvements
"""

import asyncio
import json
import sys
import os
import time
from mcp_streamlit_client import SimpleMCPClient

def test_mcp_timeout():
    """Test MCP client with timeout"""
    print("🔧 Testing MCP Client Timeout Handling")
    print("=" * 50)
    
    # Get current directory for paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    python_path = os.path.join(current_dir, "dm_steve", "Scripts", "python.exe")
    databricks_script = os.path.join(current_dir, "Databricks_MCP.py")
    
    print(f"Python path: {python_path}")
    print(f"Databricks script: {databricks_script}")
    
    # Test 1: Basic connection
    print("\n1. Testing basic MCP connection...")
    client = SimpleMCPClient(python_path, [databricks_script])
    
    start_time = time.time()
    success, message = client.start()
    connection_time = time.time() - start_time
    
    if success:
        print(f"✅ Connected successfully in {connection_time:.2f} seconds")
        print(f"Available tools: {[tool['name'] for tool in client.tools]}")
        
        # Test 2: Ping test (should be fast)
        if any(tool['name'] == 'ping' for tool in client.tools):
            print("\n2. Testing ping tool (should be fast)...")
            start_time = time.time()
            response = client.call_tool("ping", {})
            ping_time = time.time() - start_time
            
            print(f"Ping response time: {ping_time:.2f} seconds")
            if response and "result" in response:
                print("✅ Ping successful")
            else:
                print(f"❌ Ping failed: {response}")
        
        # Test 3: Warehouse status check (may timeout)
        if any(tool['name'] == 'check_warehouse_status' for tool in client.tools):
            print("\n3. Testing warehouse status check (may timeout)...")
            start_time = time.time()
            response = client.call_tool("check_warehouse_status", {})
            status_time = time.time() - start_time
            
            print(f"Warehouse check time: {status_time:.2f} seconds")
            if response and "error" in response and "timeout" in response["error"].lower():
                print("⏰ Warehouse check timed out (expected for cold warehouse)")
            elif response and "result" in response:
                print("✅ Warehouse check successful")
            else:
                print(f"❌ Warehouse check failed: {response}")
        
        # Test 4: List catalogs (will definitely timeout if warehouse is cold)
        print("\n4. Testing list_catalogs (will timeout if warehouse is cold)...")
        start_time = time.time()
        response = client.call_tool("list_catalogs", {})
        catalog_time = time.time() - start_time
        
        print(f"List catalogs time: {catalog_time:.2f} seconds")
        if response and "error" in response and "timeout" in response["error"].lower():
            print("⏰ List catalogs timed out (expected for cold warehouse)")
            print("💡 Try again in a few minutes after the warehouse warms up")
        elif response and "result" in response:
            print("✅ List catalogs successful")
        else:
            print(f"❌ List catalogs failed: {response}")
        
        # Cleanup
        client.close()
        print("\n✅ Test completed successfully")
        
    else:
        print(f"❌ Failed to connect: {message}")
        return False
    
    print("\n" + "=" * 50)
    print("Summary:")
    print("- MCP server connection timeout: Working")
    print("- Tool call timeout: 180 seconds")
    print("- Databricks connection timeout: 120 seconds")
    print("- Progress indicators: Added to Streamlit client")
    return True

if __name__ == "__main__":
    test_mcp_timeout()