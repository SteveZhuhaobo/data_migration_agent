#!/usr/bin/env python3
"""
Test startup without MCP stdio for debugging
"""

import asyncio
import sys
import os

# Add the server directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from env_validator import validate_environment
from server import load_config, get_connection, list_tools

async def test_startup():
    """Test server startup components individually"""
    print("🧪 SQL Server MCP Server Component Test")
    print("=" * 50)
    
    try:
        # Test 1: Environment validation
        print("1️⃣ Testing environment validation...")
        if not validate_environment():
            print("❌ Environment validation failed")
            return False
        print("✅ Environment validation passed")
        
        # Test 2: Configuration loading
        print("\n2️⃣ Testing configuration loading...")
        load_config()
        print("✅ Configuration loaded successfully")
        
        # Test 3: Database connection
        print("\n3️⃣ Testing database connection...")
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DB_NAME(), USER_NAME(), @@VERSION")
            result = cursor.fetchone()
            conn.close()
            print(f"✅ Database connection successful")
            print(f"   Database: {result[0]}")
            print(f"   User: {result[1]}")
            print(f"   Version: {result[2][:50]}...")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
        
        # Test 4: Tool listing
        print("\n4️⃣ Testing tool listing...")
        tools = await list_tools()
        print(f"✅ Tool listing successful: {len(tools)} tools available")
        for tool in tools:
            print(f"   - {tool.name}")
        
        print("\n🎉 All startup components working correctly!")
        print("The issue is likely with the MCP stdio server initialization.")
        print("This suggests the server is waiting for MCP client input.")
        
        return True
        
    except Exception as e:
        print(f"❌ Component test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_startup())
    sys.exit(0 if success else 1)