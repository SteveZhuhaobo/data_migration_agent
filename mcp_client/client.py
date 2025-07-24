# mcp_client/client.py - V2 Only (Recommended approach)

import asyncio
import json
from typing import Dict, List, Any, Optional

# Import the correct MCP components
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class DataMigrationClient:
    """MCP Client using proper async context management (recommended approach)"""
    
    def __init__(self):
        self.server_params = None
        print("DataMigrationClient initialized")
    
    def set_server_params(self, command: List[str]):
        """Set server parameters for connection"""
        # Use the current Python executable to ensure same environment
        if command[0] == "python":
            import sys
            command[0] = sys.executable
            print(f"Using current Python executable: {sys.executable}")
        
        self.server_params = StdioServerParameters(
            command=command[0],
            args=command[1:] if len(command) > 1 else []
        )
        print(f"Server parameters set for command: {command}")
    
    async def test_server_availability(self) -> bool:
        """Test if the MCP server is available and responding"""
        if not self.server_params:
            print("✗ Server parameters not set")
            return False

# Test function
async def test_client():
    """Test function to verify the MCP client works"""
    client = DataMigrationClient()
    
    try:
        # Set server parameters (V2 style)
        client.set_server_params(["python", "mcp_server/server.py"])
        
        # Test server availability first  
        print("Testing server availability...")
        is_available = await client.test_server_availability()
        
        if not is_available:
            print("✗ Server is not available. Please check:")
            print("  1. Server file exists: mcp_server/server.py")
            print("  2. Python environment has required dependencies")
            print("  3. Server script runs without errors")
            return
        
        print("✓ Server is available")
        
        # Test a simple tool call
        print("Testing get_mapping...")
        mapping = await client.get_mapping("test_table")
        print(f"Mapping result: {mapping}")
        
        print("✓ Client test successful!")
        
    except Exception as e:
        print(f"✗ Client test failed: {e}")
        import traceback
        traceback.print_exc()

# Alternative simplified test function
async def test_client_simple():
    """Simplified test that works with V2 client"""
    client = DataMigrationClient()
    
    try:
        # Set server parameters
        client.set_server_params(["python", "mcp_server/server.py"])
        print("✓ Server parameters set")
        
        # Test get_mapping directly
        print("Testing get_mapping tool...")
        mapping = await client.get_mapping("test_table")
        print(f"Mapping result: {mapping}")
        
        # Test get_sql_schema
        print("Testing get_sql_schema tool...")
        schema = await client.get_sql_schema("test_table")
        print(f"Schema result: {schema}")
        
        print("✓ All tests completed successfully!")
        
    except Exception as e:
        print(f"✗ Client test failed: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            print(f"Testing server availability: {self.server_params.command}")
            
            # Check if the server command exists
            import shutil
            if not shutil.which(self.server_params.command):
                print(f"✗ Command '{self.server_params.command}' not found in PATH")
                return False
            
            # Check if server file exists (for file-based servers)
            if len(self.server_params.args or []) > 0:
                import os
                server_file = self.server_params.args[0]
                if not os.path.exists(server_file):
                    print(f"✗ Server file not found: {server_file}")
                    return False
                print(f"✓ Server file exists: {server_file}")
            
            # Try a quick connection test
            async def test_operation(session):
                # Try to list available tools as a basic connectivity test
                try:
                    tools = await session.list_tools()
                    print(f"✓ Server responded with {len(tools.tools) if tools and hasattr(tools, 'tools') else 0} tools")
                    return True
                except Exception as e:
                    print(f"✗ Server connection test failed: {e}")
                    return False
            
            result = await self.execute_with_session(test_operation)
            return result
            
        except Exception as e:
            print(f"✗ Server availability test failed: {e}")
            return False
    
    async def execute_with_session(self, operation_func):
        """Execute an operation with proper session management and error handling"""
        if not self.server_params:
            raise RuntimeError("Server parameters not set. Call set_server_params() first.")
        
        try:
            print(f"Attempting to connect to MCP server: {self.server_params.command} {' '.join(self.server_params.args or [])}")
            
            async with stdio_client(self.server_params) as (read, write):
                print("✓ Stdio connection established")
                
                async with ClientSession(read, write) as session:
                    print("✓ Client session created")
                    
                    # Add timeout to initialization
                    await asyncio.wait_for(session.initialize(), timeout=10.0)
                    print("✓ Session initialized successfully")
                    
                    return await operation_func(session)
                    
        except asyncio.TimeoutError:
            print("✗ Timeout during session initialization (server may not be responding)")
            raise RuntimeError("MCP server initialization timeout - check if server is running and accessible")
        except FileNotFoundError as e:
            print(f"✗ Server command not found: {e}")
            raise RuntimeError(f"MCP server command not found: {self.server_params.command}")
        except ConnectionError as e:
            print(f"✗ Connection error: {e}")
            raise RuntimeError(f"Failed to connect to MCP server: {e}")
        except Exception as e:
            print(f"✗ Unexpected error during session execution: {e}")
            print(f"Error type: {type(e).__name__}")
            
            # Recursively extract nested exceptions from TaskGroup/ExceptionGroup
            def extract_root_exceptions(exc, level=0):
                indent = "  " * level
                print(f"{indent}Exception: {type(exc).__name__}: {exc}")
                
                # Handle ExceptionGroup (Python 3.11+)
                if hasattr(exc, 'exceptions'):
                    print(f"{indent}Sub-exceptions ({len(exc.exceptions)}):")
                    for i, sub_exc in enumerate(exc.exceptions):
                        print(f"{indent}  [{i}]:")
                        extract_root_exceptions(sub_exc, level + 2)
                
                # Handle nested __cause__ and __context__
                if hasattr(exc, '__cause__') and exc.__cause__:
                    print(f"{indent}Caused by:")
                    extract_root_exceptions(exc.__cause__, level + 1)
                elif hasattr(exc, '__context__') and exc.__context__:
                    print(f"{indent}Context:")
                    extract_root_exceptions(exc.__context__, level + 1)
            
            print("=== Detailed Exception Analysis ===")
            extract_root_exceptions(e)
            print("=== End Exception Analysis ===")
            
            import traceback
            print("=== Full Traceback ===")
            traceback.print_exc()
            print("=== End Traceback ===")
            
            raise
    
    async def _call_tool(self, session, tool_name: str, arguments: Dict) -> Any:
        """Call an MCP tool and handle the response"""
        try:
            print(f"Calling MCP tool: {tool_name} with arguments: {arguments}")
            
            # Call the tool
            result = await session.call_tool(tool_name, arguments)
            
            print(f"Raw result type: {type(result)}")
            print(f"Raw result: {result}")
            
            # Handle the response based on MCP protocol
            if hasattr(result, 'content') and result.content:
                # MCP responses typically have a content array
                content = result.content[0]
                
                # Check if it's a text content type
                if hasattr(content, 'text'):
                    try:
                        # Try to parse as JSON
                        parsed_data = json.loads(content.text)
                        print(f"Parsed JSON result: {parsed_data}")
                        return parsed_data
                    except json.JSONDecodeError:
                        # Return as plain text if not JSON
                        print(f"Plain text result: {content.text}")
                        return content.text
                else:
                    # Return content directly if it's already structured
                    print(f"Direct content result: {content}")
                    return content
            
            # If no content, return the result as-is
            print(f"Direct result: {result}")
            return result
            
        except Exception as e:
            print(f"Error calling tool {tool_name}: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def get_mapping(self, table_name: str) -> Optional[Dict]:
        """Get column mapping for a table"""
        async def operation(session):
            return await self._call_tool(session, "get_mapping", {"table_name": table_name})
        
        try:
            return await self.execute_with_session(operation)
        except Exception as e:
            print(f"Error getting mapping for {table_name}: {e}")
            return None
    
    async def get_sql_schema(self, table_name: str) -> Optional[Dict]:
        """Get schema information from SQL Server table"""
        async def operation(session):
            return await self._call_tool(session, "get_sql_schema", {"table_name": table_name})
        
        try:
            return await self.execute_with_session(operation)
        except Exception as e:
            print(f"Error getting schema for {table_name}: {e}")
            return None
    
    async def extract_data(self, table_name: str, limit: int = 1000) -> Optional[List[Dict]]:
        """Extract data from SQL Server table"""
        async def operation(session):
            result = await self._call_tool(session, "extract_data", {
                "table_name": table_name,
                "limit": limit
            })
            
            # Ensure we return a list
            if isinstance(result, list):
                return result
            elif result is not None:
                return [result]
            else:
                return []
        
        try:
            return await self.execute_with_session(operation)
        except Exception as e:
            print(f"Error extracting data from {table_name}: {e}")
            return []
    
    async def create_databricks_table(self, table_name: str, schema: Dict) -> Optional[Dict]:
        """Create table in Databricks"""
        async def operation(session):
            return await self._call_tool(session, "create_databricks_table", {
                "table_name": table_name,
                "schema": schema
            })
        
        try:
            return await self.execute_with_session(operation)
        except Exception as e:
            print(f"Error creating Databricks table {table_name}: {e}")
            return None
    
    async def load_data(self, table_name: str, data: List[Dict]) -> Optional[Dict]:
        """Load data into Databricks table"""
        async def operation(session):
            return await self._call_tool(session, "load_data", {
                "table_name": table_name,
                "data": data
            })
        
        try:
            return await self.execute_with_session(operation)
        except Exception as e:
            print(f"Error loading data to {table_name}: {e}")
            return None

    # Convenience methods for backward compatibility
    async def connect(self, command: List[str]):
        """Set server parameters (for backward compatibility)"""
        self.set_server_params(command)
        print("✓ Server parameters configured")
        return True  # Return success indicator
    
    async def close(self):
        """No-op for backward compatibility (connections are auto-managed)"""
        print("✓ No cleanup needed (connections are auto-managed)")
        return True  # Return success indicator


# Simple direct server test
async def test_server_directly():
    """Test the MCP server directly without our client wrapper"""
    import sys
    
    print("=== Direct Server Test ===")
    
    try:
        from mcp.client.stdio import stdio_client
        from mcp import ClientSession, StdioServerParameters
        
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["mcp_server/server.py"]
        )
        
        print(f"Testing direct connection to: {sys.executable} mcp_server/server.py")
        
        # Test just the stdio_client connection
        print("Step 1: Testing stdio_client connection...")
        async with stdio_client(server_params) as (read, write):
            print("✓ stdio_client connection successful")
            
            # Test ClientSession creation
            print("Step 2: Testing ClientSession creation...")
            async with ClientSession(read, write) as session:
                print("✓ ClientSession created successfully")
                
                # Test initialization
                print("Step 3: Testing session initialization...")
                await asyncio.wait_for(session.initialize(), timeout=15.0)
                print("✓ Session initialized successfully")
                
                # Test a simple operation
                print("Step 4: Testing list_tools...")
                try:
                    tools = await session.list_tools()
                    print(f"✓ Got tools response: {len(tools.tools) if tools and hasattr(tools, 'tools') else 'unknown'} tools")
                    if tools and hasattr(tools, 'tools'):
                        for tool in tools.tools[:3]:  # Show first 3 tools
                            print(f"  - {tool.name}: {tool.description[:50]}...")
                except Exception as tool_error:
                    print(f"✗ list_tools failed: {tool_error}")
                    # This might be expected if the server doesn't implement tools
                
        print("✓ Direct server test completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Direct server test failed: {e}")
        
        # Enhanced error extraction for direct test
        def extract_all_errors(exc, level=0):
            indent = "  " * level
            print(f"{indent}Error: {type(exc).__name__}: {exc}")
            
            if hasattr(exc, 'exceptions'):
                for i, sub_exc in enumerate(exc.exceptions):
                    print(f"{indent}Sub-error [{i}]:")
                    extract_all_errors(sub_exc, level + 1)
            
            if hasattr(exc, '__cause__') and exc.__cause__:
                print(f"{indent}Caused by:")
                extract_all_errors(exc.__cause__, level + 1)
        
        print("=== Error Details ===")
        extract_all_errors(e)
        
        import traceback
        print("=== Full Traceback ===")
        traceback.print_exc()
        
        return False
    """Test function to verify the MCP client works"""
    client = DataMigrationClient()
    
    try:
        # Set server parameters
        await client.connect(["python", "mcp_server/server.py"])
        
        # Test server availability first
        print("Testing server availability...")
        is_available = await client.test_server_availability()
        
        if not is_available:
            print("✗ Server is not available. Please check:")
            print("  1. Server file exists: mcp_server/server.py")
            print("  2. Python environment has required dependencies")
            print("  3. Server script runs without errors")
            return
        
        print("✓ Server is available")
        
        # Test a simple tool call
        print("Testing get_mapping...")
        mapping = await client.get_mapping("test_table")
        print(f"Mapping result: {mapping}")
        
        print("✓ Client test successful!")
        
    except Exception as e:
        print(f"✗ Client test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await client.close()

# Additional debugging function
async def debug_server():
    """Debug function to help diagnose server issues"""
    import os
    import subprocess
    import sys
    
    server_file = "mcp_server/server.py"
    
    print("=== MCP Server Debug Information ===")
    print(f"Current Python executable: {sys.executable}")
    
    # Check if server file exists
    if os.path.exists(server_file):
        print(f"✓ Server file exists: {server_file}")
    else:
        print(f"✗ Server file not found: {server_file}")
        print("Please ensure the server file is in the correct location")
        return
    
    # Check yaml import in current Python
    try:
        import yaml
        print(f"✓ yaml module available in current Python: {yaml.__version__}")
    except ImportError:
        print("✗ yaml module not available in current Python")
        print("Run: pip install pyyaml")
        return
    
    # Check MCP import in current Python
    try:
        import mcp
        print(f"✓ mcp module available in current Python")
    except ImportError:
        print("✗ mcp module not available in current Python")
        print("Run: pip install mcp")
        return
    
    # Check if Python can run the server with current executable
    try:
        result = subprocess.run(
            [sys.executable, server_file, "--help"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        if result.returncode == 0:
            print("✓ Server script runs successfully with current Python")
            if result.stdout:
                print(f"Server output: {result.stdout[:200]}...")
        else:
            print(f"✗ Server script failed with return code: {result.returncode}")
            if result.stderr:
                print(f"stderr: {result.stderr}")
            if result.stdout:
                print(f"stdout: {result.stdout}")
    except subprocess.TimeoutExpired:
        print("✗ Server script timed out (may be running as server)")
        print("This might be normal if the server is waiting for MCP client connection")
    except Exception as e:
        print(f"✗ Error running server: {e}")
    
    # Test yaml import specifically with the same Python
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import yaml; print('yaml import successful')"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        if result.returncode == 0:
            print("✓ yaml imports successfully in subprocess")
        else:
            print(f"✗ yaml import failed in subprocess: {result.stderr}")
    except Exception as e:
        print(f"✗ Error testing yaml import: {e}")
    
    print("=== End Debug Information ===\n")

if __name__ == "__main__":
    print("=== MCP Client Test Suite ===")
    
    # Run debug check first
    asyncio.run(debug_server())
    
    # Test server directly
    print("Step 1: Testing server directly...")
    direct_test_success = asyncio.run(test_server_directly())
    
    if direct_test_success:
        print("\nStep 2: Testing with simplified client wrapper...")
        asyncio.run(test_client_simple())
        
        print("\nStep 3: Testing with availability check...")
        asyncio.run(test_client())
    else:
        print("\n✗ Direct server test failed - skipping client wrapper test")
        print("Please fix the server issues shown above before proceeding.")