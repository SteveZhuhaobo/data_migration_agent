import asyncio
import sys
import argparse
import traceback
from agent.migration_agent import DataMigrationAgent

# mcp_client/client.py - Debug version to find correct imports

import asyncio
import json
from contextlib import asynccontextmanager
from typing import Dict, List, Any, Optional

# Debug: Try to find the correct MCP imports
def debug_mcp_imports():
    """Debug function to find available MCP imports"""
    import_attempts = [
        # Attempt 1: Standard MCP client
        ("from mcp.client.stdio import stdio_client", "from mcp.types import StdioServerParameters"),
        ("from mcp.client.stdio import stdio_client", None),
        
        # Attempt 2: Alternative MCP client structure
        ("from mcp import stdio_client", None),
        ("from mcp.stdio import stdio_client", None),
        ("from mcp.client import stdio_client", None),
        
        # Attempt 3: Different package structure
        ("from mcp_client.stdio import stdio_client", None),
        ("from mcp_server.client import stdio_client", None),
        
        # Attempt 4: Check if it's a different package name entirely
        ("from mcp_python.client.stdio import stdio_client", None),
        ("from python_mcp.client.stdio import stdio_client", None),
    ]
    
    successful_imports = []
    
    for client_import, params_import in import_attempts:
        try:
            exec(client_import)
            print(f"✓ SUCCESS: {client_import}")
            successful_imports.append(client_import)
            
            if params_import:
                try:
                    exec(params_import)
                    print(f"✓ SUCCESS: {params_import}")
                    successful_imports.append(params_import)
                except ImportError as e:
                    print(f"✗ FAILED: {params_import} - {e}")
            
        except ImportError as e:
            print(f"✗ FAILED: {client_import} - {e}")
    
    return successful_imports

# Run the debug function
print("=== DEBUGGING MCP IMPORTS ===")
successful_imports = debug_mcp_imports()

if not successful_imports:
    print("\n❌ NO MCP IMPORTS FOUND!")
    print("Please install MCP library with: pip install mcp")
    stdio_client = None
    StdioServerParameters = None
    MCP_AVAILABLE = False
else:
    print(f"\n✅ Found {len(successful_imports)} working imports")
    MCP_AVAILABLE = True
    
    # Try to actually import based on successful attempts
    stdio_client = None
    StdioServerParameters = None
    
    # Try the most common patterns first
    try:
        from mcp.client.stdio import stdio_client
        print("✓ Successfully imported stdio_client from mcp.client.stdio")
    except ImportError:
        try:
            from mcp import stdio_client
            print("✓ Successfully imported stdio_client from mcp")
        except ImportError:
            print("✗ Could not import stdio_client")
    
    try:
        from mcp.types import StdioServerParameters
        print("✓ Successfully imported StdioServerParameters from mcp.types")
    except ImportError:
        try:
            from mcp.client.stdio import StdioServerParameters
            print("✓ Successfully imported StdioServerParameters from mcp.client.stdio")
        except ImportError:
            print("✗ Could not import StdioServerParameters, will create custom class")
            
            # Create a simple replacement
            class StdioServerParameters:
                def __init__(self, command: str, args: List[str] = None):
                    self.command = command
                    self.args = args or []
                    print(f"Created custom StdioServerParameters: command={command}, args={args}")

# Also check what MCP-related packages are installed
print("\n=== CHECKING INSTALLED PACKAGES ===")
try:
    import pkg_resources
    installed_packages = [pkg.project_name for pkg in pkg_resources.working_set]
    mcp_packages = [pkg for pkg in installed_packages if 'mcp' in pkg.lower()]
    if mcp_packages:
        print(f"Found MCP-related packages: {mcp_packages}")
    else:
        print("No MCP-related packages found")
except ImportError:
    print("Could not check installed packages")

class DataMigrationClient:
    def __init__(self):
        self.session = None
        self.session_context = None
        print(f"DataMigrationClient initialized. MCP available: {MCP_AVAILABLE}")
    
    async def connect(self, command: List[str]):
        """Connect to MCP server with multiple fallback approaches"""
        print(f"Attempting to connect with command: {command}")
        
        if not MCP_AVAILABLE or stdio_client is None:
            raise ImportError(f"MCP not available. stdio_client: {stdio_client}, MCP_AVAILABLE: {MCP_AVAILABLE}")
        
        connection_attempts = []
        
        try:
            # Attempt 1: With StdioServerParameters
            if StdioServerParameters is not None:
                try:
                    print("Attempt 1: Using StdioServerParameters")
                    server_params = StdioServerParameters(
                        command=command[0],
                        args=command[1:] if len(command) > 1 else []
                    )
                    self.session_context = stdio_client(server_params)
                    print("✓ Created session context with StdioServerParameters")
                except Exception as e:
                    print(f"✗ Attempt 1 failed: {e}")
                    connection_attempts.append(f"StdioServerParameters: {e}")
            
            # Attempt 2: Direct command list
            if self.session_context is None:
                try:
                    print("Attempt 2: Using command list directly")
                    self.session_context = stdio_client(command)
                    print("✓ Created session context with command list")
                except Exception as e:
                    print(f"✗ Attempt 2 failed: {e}")
                    connection_attempts.append(f"Direct command list: {e}")
            
            # Attempt 3: Command as single string
            if self.session_context is None:
                try:
                    print("Attempt 3: Using command string")
                    command_str = " ".join(command)
                    self.session_context = stdio_client(command_str)
                    print("✓ Created session context with command string")
                except Exception as e:
                    print(f"✗ Attempt 3 failed: {e}")
                    connection_attempts.append(f"Command string: {e}")
            
            if self.session_context is None:
                raise Exception(f"All connection attempts failed: {connection_attempts}")
            
            # Enter the context manager
            print("Entering session context...")
            self.session = await self.session_context.__aenter__()
            print("✓ Entered session context")
            
            # Initialize the session
            print("Initializing session...")
            await self.session.initialize()
            print("✓ Session initialized successfully")
            
            print("Successfully connected to MCP server")
            
        except Exception as e:
            print(f"Error connecting to MCP server: {e}")
            print(f"All attempts: {connection_attempts}")
            raise
    
    async def close(self):
        """Close the MCP connection"""
        try:
            if self.session_context:
                print("Closing MCP connection...")
                await self.session_context.__aexit__(None, None, None)
                self.session_context = None
                self.session = None
                print("MCP connection closed")
        except Exception as e:
            print(f"Error closing MCP connection: {e}")
    
    # Mock methods for testing
    async def get_mapping(self, table_name: str) -> Optional[Dict]:
        if not self.session:
            return {"error": "Not connected to MCP server"}
        try:
            result = await self.session.call_tool("get_mapping", {"table_name": table_name})
            return {"status": "success", "result": str(result)}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_sql_schema(self, table_name: str) -> Optional[Dict]:
        if not self.session:
            return {"error": "Not connected to MCP server"}
        try:
            result = await self.session.call_tool("get_sql_schema", {"table_name": table_name})
            return {"status": "success", "result": str(result)}
        except Exception as e:
            return {"error": str(e)}
    
    async def extract_data(self, table_name: str, limit: int = 1000) -> Optional[List[Dict]]:
        if not self.session:
            return [{"error": "Not connected to MCP server"}]
        try:
            result = await self.session.call_tool("extract_data", {"table_name": table_name, "limit": limit})
            return [{"status": "success", "result": str(result)}]
        except Exception as e:
            return [{"error": str(e)}]
    
    async def create_databricks_table(self, table_name: str, schema: Dict) -> Optional[Dict]:
        if not self.session:
            return {"error": "Not connected to MCP server"}
        try:
            result = await self.session.call_tool("create_databricks_table", {"table_name": table_name, "schema": schema})
            return {"status": "success", "result": str(result)}
        except Exception as e:
            return {"error": str(e)}
    
    async def load_data(self, table_name: str, data: List[Dict]) -> Optional[Dict]:
        if not self.session:
            return {"error": "Not connected to MCP server"}
        try:
            result = await self.session.call_tool("load_data", {"table_name": table_name, "data": data})
            return {"status": "success", "result": str(result)}
        except Exception as e:
            return {"error": str(e)}