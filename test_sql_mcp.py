#!/usr/bin/env python3
"""
Simple test for SQL Server MCP
"""

import sys
import os
import time
from mcp_streamlit_client import SimpleMCPClient

def test_sql_mcp():
    """Test SQL Server MCP with simple operations"""
    print("🔧 Testing SQL Server MCP")
    print("=" * 40)
    
    # Get current directory for paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    python_path = os.path.join(current_dir, "dm_steve", "Scripts", "python.exe")
    sql_script = os.path.join(current_dir, "SQL_MCP.py")
    
    print(f"Python path: {python_path}")
    print(f"SQL script: {sql_script}")
    
    # Test connection
    print("\n1. Testing SQL MCP connection...")
    client = SimpleMCPClient(python_path, [sql_script])
    
    start_time = time.time()
    success, message = client.start()
    connection_time = time.time() - start_time
    
    if success:
        print(f"✅ Connected in {connection_time:.2f} seconds")
        print(f"Available tools: {[tool['name'] for tool in client.tools]}")
        
        # Test connection first
        if any(tool['name'] == 'test_connection' for tool in client.tools):
            print("\n2. Testing connection...")
            start_time = time.time()
            response = client.call_tool("test_connection", {})
            test_time = time.time() - start_time
            
            print(f"Connection test time: {test_time:.2f} seconds")
            if response and "result" in response:
                print("✅ Connection test successful")
                print(f"Response: {response}")
            else:
                print(f"❌ Connection test failed: {response}")
        
        # Test list tables (should be fast)
        if any(tool['name'] == 'list_tables' for tool in client.tools):
            print("\n3. Testing list_tables...")
            start_time = time.time()
            response = client.call_tool("list_tables", {})
            list_time = time.time() - start_time
            
            print(f"List tables time: {list_time:.2f} seconds")
            if response and "result" in response:
                print("✅ List tables successful")
                print(f"Response: {response}")
            else:
                print(f"❌ List tables failed: {response}")
        
        client.close()
        print("\n✅ SQL MCP test completed")
        return True
        
    else:
        print(f"❌ Failed to connect: {message}")
        return False

if __name__ == "__main__":
    test_sql_mcp()