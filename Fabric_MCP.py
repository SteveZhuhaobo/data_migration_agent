#!/usr/bin/env python3
"""
Microsoft Fabric MCP Server - A Model Context Protocol server for Microsoft Fabric operations
"""

import asyncio
import json
import yaml
import os
import time
import requests
from typing import Dict, Any, List, Optional
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
import mcp.server.stdio

# Azure authentication imports
try:
    from azure.identity import ClientSecretCredential
    from azure.core.exceptions import ClientAuthenticationError
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

# Create the server instance
server = Server("fabric-mcp-server")

# Global config and authentication (loaded on startup)
config = None
credential = None
access_token = None
token_expires_at = None

def load_config():
    """Load configuration files with validation"""
    global config
    
    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "config", "config.yaml")
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # Validate required Fabric configuration fields
        if 'fabric' not in config:
            raise ValueError("Missing 'fabric' section in configuration")
            
        fabric_config = config['fabric']
        required_fields = ['tenant_id', 'client_id']
        
        for field in required_fields:
            if field not in fabric_config or not fabric_config[field]:
                raise ValueError(f"Missing required Fabric configuration field: {field}")
        
        # Check for client_secret in config or environment
        if 'client_secret' not in fabric_config or not fabric_config['client_secret']:
            # Try to get from environment variable
            client_secret = os.getenv('FABRIC_CLIENT_SECRET')
            if not client_secret:
                raise ValueError("Missing client_secret in configuration or FABRIC_CLIENT_SECRET environment variable")
            fabric_config['client_secret'] = client_secret
        
        # Set default values if not provided
        if 'timeout' not in fabric_config:
            fabric_config['timeout'] = 120
        if 'max_retries' not in fabric_config:
            fabric_config['max_retries'] = 3
        if 'retry_delay' not in fabric_config:
            fabric_config['retry_delay'] = 5
            
    except FileNotFoundError:
        raise Exception(f"Configuration file not found at: {config_path}")
    except yaml.YAMLError as e:
        raise Exception(f"Error parsing YAML configuration file: {str(e)}")
    except Exception as e:
        raise Exception(f"Configuration error: {str(e)}")

def validate_connection():
    """Validate Fabric connection configuration"""
    try:
        fabric_config = config['fabric']
        
        # Basic validation of tenant_id format (should be a GUID)
        tenant_id = fabric_config['tenant_id']
        if not tenant_id or not isinstance(tenant_id, str) or len(tenant_id) != 36:
            raise ValueError("Invalid tenant_id - must be a valid GUID")
            
        # Basic validation of client_id format (should be a GUID)
        client_id = fabric_config['client_id']
        if not client_id or not isinstance(client_id, str) or len(client_id) != 36:
            raise ValueError("Invalid client_id - must be a valid GUID")
            
        # Basic validation of client_secret
        client_secret = fabric_config['client_secret']
        if not client_secret or not isinstance(client_secret, str) or len(client_secret) < 10:
            raise ValueError("Invalid client_secret - must be a valid secret string")
            
        return True
        
    except Exception as e:
        raise Exception(f"Connection validation failed: {str(e)}")

def get_azure_credential():
    """Create Azure credential for authentication"""
    global credential
    
    if not AZURE_AVAILABLE:
        raise Exception("azure-identity package not installed. Please install it with: pip install azure-identity")
    
    if credential is None:
        fabric_config = config['fabric']
        
        try:
            credential = ClientSecretCredential(
                tenant_id=fabric_config['tenant_id'],
                client_id=fabric_config['client_id'],
                client_secret=fabric_config['client_secret']
            )
        except Exception as e:
            raise Exception(f"Failed to create Azure credential: {str(e)}")
    
    return credential

async def get_access_token(force_refresh: bool = False):
    """Get access token for Microsoft Fabric API calls"""
    global access_token, token_expires_at
    
    # Check if we have a valid token
    if not force_refresh and access_token and token_expires_at:
        # Add 5 minute buffer before expiration
        if time.time() < (token_expires_at - 300):
            return access_token
    
    try:
        credential = get_azure_credential()
        
        # Microsoft Fabric API scope
        scope = "https://api.fabric.microsoft.com/.default"
        
        # Get token
        token = credential.get_token(scope)
        access_token = token.token
        token_expires_at = token.expires_on
        
        return access_token
        
    except ClientAuthenticationError as e:
        raise Exception(f"Authentication failed: {str(e)}. Please check your tenant_id, client_id, and client_secret.")
    except Exception as e:
        raise Exception(f"Failed to get access token: {str(e)}")

async def test_authentication():
    """Test authentication by getting a token"""
    try:
        token = await get_access_token()
        if token:
            return True, "Authentication successful"
        else:
            return False, "Failed to get access token"
    except Exception as e:
        return False, str(e)

class FabricAPIClient:
    """Microsoft Fabric REST API client"""
    
    def __init__(self):
        self.base_url = "https://api.fabric.microsoft.com/v1"
        self.session = None
        
    async def get_session(self):
        """Get authenticated HTTP session"""
        if self.session is None:
            self.session = requests.Session()
            self.session.headers.update({
                'Content-Type': 'application/json',
                'User-Agent': 'fabric-mcp-server/1.0'
            })
            
            # Set timeout from config
            timeout = config['fabric'].get('timeout', 120)
            self.session.timeout = timeout
        
        # Get fresh access token
        token = await get_access_token()
        self.session.headers.update({
            'Authorization': f'Bearer {token}'
        })
        
        return self.session
    
    async def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Fabric API with retry logic"""
        max_retries = config['fabric'].get('max_retries', 3)
        retry_delay = config['fabric'].get('retry_delay', 5)
        
        for attempt in range(max_retries + 1):
            try:
                session = await self.get_session()
                url = f"{self.base_url}{endpoint}"
                
                response = session.request(method, url, **kwargs)
                
                # Handle different response codes
                if response.status_code == 200:
                    return response.json() if response.content else {}
                elif response.status_code == 401:
                    # Token might be expired, try to refresh
                    if attempt < max_retries:
                        await get_access_token(force_refresh=True)
                        continue
                    else:
                        raise Exception("Authentication failed: Invalid or expired token")
                elif response.status_code == 403:
                    raise Exception("Access denied: Insufficient permissions")
                elif response.status_code == 404:
                    raise Exception("Resource not found")
                elif response.status_code == 429:
                    # Rate limited
                    retry_after = int(response.headers.get('Retry-After', retry_delay))
                    if attempt < max_retries:
                        time.sleep(retry_after)
                        continue
                    else:
                        raise Exception("Rate limit exceeded")
                else:
                    raise Exception(f"API request failed with status {response.status_code}: {response.text}")
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries:
                    time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    raise Exception("Request timeout: Please check your network connectivity")
            except requests.exceptions.ConnectionError:
                if attempt < max_retries:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                else:
                    raise Exception("Connection error: Unable to connect to Microsoft Fabric API")
            except Exception as e:
                if attempt < max_retries and "timeout" in str(e).lower():
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                else:
                    raise e
        
        raise Exception("Max retries exceeded")
    
    async def list_workspaces(self) -> List[Dict[str, Any]]:
        """List all accessible workspaces"""
        try:
            response = await self.make_request('GET', '/workspaces')
            return response.get('value', [])
        except Exception as e:
            raise Exception(f"Failed to list workspaces: {str(e)}")
    
    async def get_workspace(self, workspace_id: str) -> Dict[str, Any]:
        """Get workspace information"""
        try:
            response = await self.make_request('GET', f'/workspaces/{workspace_id}')
            return response
        except Exception as e:
            raise Exception(f"Failed to get workspace {workspace_id}: {str(e)}")
    
    async def list_lakehouses(self, workspace_id: str) -> List[Dict[str, Any]]:
        """List lakehouses in a workspace"""
        try:
            response = await self.make_request('GET', f'/workspaces/{workspace_id}/lakehouses')
            return response.get('value', [])
        except Exception as e:
            raise Exception(f"Failed to list lakehouses in workspace {workspace_id}: {str(e)}")
    
    async def get_lakehouse(self, workspace_id: str, lakehouse_id: str) -> Dict[str, Any]:
        """Get lakehouse information"""
        try:
            response = await self.make_request('GET', f'/workspaces/{workspace_id}/lakehouses/{lakehouse_id}')
            return response
        except Exception as e:
            raise Exception(f"Failed to get lakehouse {lakehouse_id}: {str(e)}")
    
    async def list_warehouses(self, workspace_id: str) -> List[Dict[str, Any]]:
        """List warehouses in a workspace"""
        try:
            response = await self.make_request('GET', f'/workspaces/{workspace_id}/warehouses')
            return response.get('value', [])
        except Exception as e:
            raise Exception(f"Failed to list warehouses in workspace {workspace_id}: {str(e)}")
    
    async def get_warehouse(self, workspace_id: str, warehouse_id: str) -> Dict[str, Any]:
        """Get warehouse information"""
        try:
            response = await self.make_request('GET', f'/workspaces/{workspace_id}/warehouses/{warehouse_id}')
            return response
        except Exception as e:
            raise Exception(f"Failed to get warehouse {warehouse_id}: {str(e)}")

# Global API client instance
fabric_client = FabricAPIClient()

class FabricSQLExecutor:
    """SQL execution engine for Microsoft Fabric"""
    
    def __init__(self, api_client: FabricAPIClient):
        self.api_client = api_client
    
    async def execute_query(self, query: str, resource_type: str, resource_id: str, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute SQL query against Fabric resource"""
        try:
            # Use default workspace if not provided
            if not workspace_id:
                workspace_id = config['fabric'].get('workspace_id')
                if not workspace_id:
                    raise Exception("No workspace_id provided and no default workspace configured")
            
            # Determine the SQL endpoint based on resource type
            if resource_type.lower() == 'lakehouse':
                endpoint = f'/workspaces/{workspace_id}/lakehouses/{resource_id}/sqlEndpoint/queries'
            elif resource_type.lower() == 'warehouse':
                endpoint = f'/workspaces/{workspace_id}/warehouses/{resource_id}/queries'
            else:
                raise Exception(f"Unsupported resource type: {resource_type}")
            
            # Prepare query payload
            payload = {
                "query": query,
                "parameters": {}
            }
            
            # Execute the query
            response = await self.api_client.make_request('POST', endpoint, json=payload)
            
            # Format response similar to Databricks server
            if self._is_select_query(query):
                return self._format_select_result(response, query)
            else:
                return self._format_dml_result(response, query)
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _is_select_query(self, query: str) -> bool:
        """Check if query is a SELECT statement"""
        query_upper = query.strip().upper()
        return (query_upper.startswith("SELECT") or 
                query_upper.startswith("SHOW") or 
                query_upper.startswith("DESCRIBE") or
                query_upper.startswith("EXPLAIN"))
    
    def _format_select_result(self, response: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Format SELECT query results"""
        try:
            # Extract columns and data from Fabric response
            # Note: Actual response format may vary - this is based on typical patterns
            columns = response.get('columns', [])
            rows = response.get('rows', [])
            
            # Convert to list of dictionaries
            data = []
            if columns and rows:
                column_names = [col.get('name', f'col_{i}') for i, col in enumerate(columns)]
                for row in rows:
                    data.append(dict(zip(column_names, row)))
            
            return {
                "success": True,
                "columns": [col.get('name', f'col_{i}') for i, col in enumerate(columns)],
                "data": data,
                "row_count": len(data),
                "query_type": "SELECT"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to format SELECT result: {str(e)}",
                "error_type": "ResultFormattingError"
            }
    
    def _format_dml_result(self, response: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Format DML/DDL query results"""
        try:
            affected_rows = response.get('rowsAffected', 0)
            
            return {
                "success": True,
                "message": f"Query executed successfully. Affected rows: {affected_rows}",
                "affected_rows": affected_rows,
                "query_type": "DML/DDL"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to format DML result: {str(e)}",
                "error_type": "ResultFormattingError"
            }
    
    async def get_tables(self, resource_type: str, resource_id: str, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of tables in a resource"""
        try:
            query = "SHOW TABLES"
            result = await self.execute_query(query, resource_type, resource_id, workspace_id)
            
            if result.get('success'):
                return result.get('data', [])
            else:
                raise Exception(result.get('error', 'Failed to get tables'))
                
        except Exception as e:
            raise Exception(f"Failed to list tables: {str(e)}")
    
    async def get_table_schema(self, table_name: str, resource_type: str, resource_id: str, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """Get table schema information"""
        try:
            query = f"DESCRIBE TABLE {table_name}"
            result = await self.execute_query(query, resource_type, resource_id, workspace_id)
            
            if result.get('success'):
                # Format schema information
                columns = []
                for row in result.get('data', []):
                    columns.append({
                        "column_name": row.get('col_name', ''),
                        "data_type": row.get('data_type', ''),
                        "comment": row.get('comment', ''),
                        "is_nullable": True  # Default assumption
                    })
                
                return {
                    "success": True,
                    "table_name": table_name,
                    "columns": columns,
                    "column_count": len(columns)
                }
            else:
                return result
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }

# Global SQL executor instance
sql_executor = FabricSQLExecutor(fabric_client)

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available Microsoft Fabric tools"""
    return [
        Tool(
            name="execute_query",
            description="Execute a SQL query on Microsoft Fabric and return results",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL query to execute"},
                    "resource_type": {"type": "string", "description": "Resource type: 'lakehouse' or 'warehouse'", "enum": ["lakehouse", "warehouse"]},
                    "resource_id": {"type": "string", "description": "ID of the lakehouse or warehouse"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="list_workspaces",
            description="List all accessible Microsoft Fabric workspaces",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="list_lakehouses",
            description="List lakehouses in a workspace",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string", "description": "Workspace ID (optional, uses default if not provided)"}
                }
            }
        ),
        Tool(
            name="list_warehouses",
            description="List warehouses in a workspace",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string", "description": "Workspace ID (optional, uses default if not provided)"}
                }
            }
        ),
        Tool(
            name="list_tables",
            description="List tables in a lakehouse or warehouse",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_type": {"type": "string", "description": "Resource type: 'lakehouse' or 'warehouse'", "enum": ["lakehouse", "warehouse"]},
                    "resource_id": {"type": "string", "description": "ID of the lakehouse or warehouse"},
                    "workspace_id": {"type": "string", "description": "Workspace ID (optional)"}
                },
                "required": ["resource_type", "resource_id"]
            }
        ),
        Tool(
            name="get_table_schema",
            description="Get detailed schema information for a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table"},
                    "resource_type": {"type": "string", "description": "Resource type: 'lakehouse' or 'warehouse'", "enum": ["lakehouse", "warehouse"]},
                    "resource_id": {"type": "string", "description": "ID of the lakehouse or warehouse"}
                },
                "required": ["table_name", "resource_type", "resource_id"]
            }
        ),
        Tool(
            name="describe_table",
            description="Get comprehensive table metadata",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table"},
                    "resource_type": {"type": "string", "description": "Resource type: 'lakehouse' or 'warehouse'", "enum": ["lakehouse", "warehouse"]},
                    "resource_id": {"type": "string", "description": "ID of the lakehouse or warehouse"}
                },
                "required": ["table_name", "resource_type", "resource_id"]
            }
        ),
        Tool(
            name="create_table",
            description="Create a new table in Microsoft Fabric",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table to create"},
                    "columns": {"type": "array", "description": "Column definitions", "items": {"type": "string"}},
                    "resource_type": {"type": "string", "description": "Resource type: 'lakehouse' or 'warehouse'", "enum": ["lakehouse", "warehouse"]},
                    "resource_id": {"type": "string", "description": "ID of the lakehouse or warehouse"}
                },
                "required": ["table_name", "columns", "resource_type", "resource_id"]
            }
        ),
        Tool(
            name="insert_data",
            description="Insert data into a Microsoft Fabric table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table"},
                    "data": {
                        "type": "array", 
                        "description": "Array of row objects to insert",
                        "items": {
                            "type": "object",
                            "description": "Row data as key-value pairs"
                        }
                    },
                    "resource_type": {"type": "string", "description": "Resource type: 'lakehouse' or 'warehouse'", "enum": ["lakehouse", "warehouse"]},
                    "resource_id": {"type": "string", "description": "ID of the lakehouse or warehouse"}
                },
                "required": ["table_name", "data", "resource_type", "resource_id"]
            }
        ),
        Tool(
            name="get_workspace_info",
            description="Get detailed information about a workspace",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string", "description": "Workspace ID (optional, uses default if not provided)"}
                }
            }
        ),
        Tool(
            name="ping",
            description="Simple ping test to check if the MCP server is responsive",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="test_connection",
            description="Test the connection to Microsoft Fabric and return basic info",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Optional[Dict[str, Any]] = None) -> List[TextContent]:
    """Handle tool calls"""
    if arguments is None:
        arguments = {}
    
    try:
        if name == "ping":
            result = await ping_tool()
        elif name == "test_connection":
            result = await test_connection_tool()
        elif name == "list_workspaces":
            result = await list_workspaces_tool()
        elif name == "list_lakehouses":
            result = await list_lakehouses_tool(arguments.get("workspace_id"))
        elif name == "list_warehouses":
            result = await list_warehouses_tool(arguments.get("workspace_id"))
        elif name == "list_tables":
            result = await list_tables_tool(
                arguments["resource_type"],
                arguments["resource_id"],
                arguments.get("workspace_id")
            )
        elif name == "get_workspace_info":
            result = await get_workspace_info_tool(arguments.get("workspace_id"))
        elif name == "get_table_schema":
            result = await get_table_schema_tool(
                arguments["table_name"],
                arguments["resource_type"],
                arguments["resource_id"]
            )
        elif name == "describe_table":
            result = await describe_table_tool(
                arguments["table_name"],
                arguments["resource_type"],
                arguments["resource_id"]
            )
        elif name == "create_table":
            result = await create_table_tool(
                arguments["table_name"],
                arguments["columns"],
                arguments["resource_type"],
                arguments["resource_id"]
            )
        elif name == "insert_data":
            result = await insert_data_tool(
                arguments["table_name"],
                arguments["data"],
                arguments["resource_type"],
                arguments["resource_id"]
            )
        elif name == "execute_query":
            result = await execute_query_tool(
                arguments["query"],
                arguments.get("resource_type"),
                arguments.get("resource_id")
            )
        else:
            result = f"Tool '{name}' not yet implemented"
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}"
        return [TextContent(type="text", text=error_msg)]

# Utility Tools
async def ping_tool() -> str:
    """Simple ping test"""
    return json.dumps({
        "success": True,
        "message": "Microsoft Fabric MCP Server is responsive",
        "server": "fabric-mcp-server",
        "version": "1.0.0"
    }, indent=2)

async def test_connection_tool() -> str:
    """Test connection to Microsoft Fabric"""
    try:
        if config is None:
            return json.dumps({
                "success": False,
                "error": "Configuration not loaded"
            }, indent=2)
        
        # Validate configuration
        validate_connection()
        
        # Test authentication
        auth_success, auth_message = await test_authentication()
        
        result = {
            "success": auth_success,
            "message": auth_message,
            "tenant_id": config['fabric']['tenant_id'],
            "client_id": config['fabric']['client_id'],
            "workspace_id": config['fabric'].get('workspace_id', 'Not configured'),
            "azure_identity_available": AZURE_AVAILABLE
        }
        
        if auth_success:
            result["token_expires_at"] = token_expires_at
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

# Resource Discovery Tools
async def list_workspaces_tool() -> str:
    """List all accessible Microsoft Fabric workspaces"""
    try:
        workspaces = await fabric_client.list_workspaces()
        
        return json.dumps({
            "success": True,
            "workspaces": workspaces,
            "count": len(workspaces)
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def list_lakehouses_tool(workspace_id: Optional[str] = None) -> str:
    """List lakehouses in a workspace"""
    try:
        # Use provided workspace_id or default from config
        if not workspace_id:
            workspace_id = config['fabric'].get('workspace_id')
            if not workspace_id:
                return json.dumps({
                    "success": False,
                    "error": "No workspace_id provided and no default workspace configured"
                }, indent=2)
        
        lakehouses = await fabric_client.list_lakehouses(workspace_id)
        
        return json.dumps({
            "success": True,
            "workspace_id": workspace_id,
            "lakehouses": lakehouses,
            "count": len(lakehouses)
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def list_warehouses_tool(workspace_id: Optional[str] = None) -> str:
    """List warehouses in a workspace"""
    try:
        # Use provided workspace_id or default from config
        if not workspace_id:
            workspace_id = config['fabric'].get('workspace_id')
            if not workspace_id:
                return json.dumps({
                    "success": False,
                    "error": "No workspace_id provided and no default workspace configured"
                }, indent=2)
        
        warehouses = await fabric_client.list_warehouses(workspace_id)
        
        return json.dumps({
            "success": True,
            "workspace_id": workspace_id,
            "warehouses": warehouses,
            "count": len(warehouses)
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def list_tables_tool(resource_type: str, resource_id: str, workspace_id: Optional[str] = None) -> str:
    """List tables in a lakehouse or warehouse"""
    try:
        tables = await sql_executor.get_tables(resource_type, resource_id, workspace_id)
        
        return json.dumps({
            "success": True,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "workspace_id": workspace_id or config['fabric'].get('workspace_id'),
            "tables": tables,
            "count": len(tables)
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def get_workspace_info_tool(workspace_id: Optional[str] = None) -> str:
    """Get detailed information about a workspace"""
    try:
        # Use provided workspace_id or default from config
        if not workspace_id:
            workspace_id = config['fabric'].get('workspace_id')
            if not workspace_id:
                return json.dumps({
                    "success": False,
                    "error": "No workspace_id provided and no default workspace configured"
                }, indent=2)
        
        workspace_info = await fabric_client.get_workspace(workspace_id)
        
        return json.dumps({
            "success": True,
            "workspace_info": workspace_info
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

# Table Schema and Metadata Tools
async def get_table_schema_tool(table_name: str, resource_type: str, resource_id: str) -> str:
    """Get detailed schema information for a table"""
    try:
        schema_info = await sql_executor.get_table_schema(table_name, resource_type, resource_id)
        
        return json.dumps(schema_info, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def describe_table_tool(table_name: str, resource_type: str, resource_id: str) -> str:
    """Get comprehensive table metadata"""
    try:
        # Get basic schema information
        schema_result = await sql_executor.get_table_schema(table_name, resource_type, resource_id)
        
        if not schema_result.get('success'):
            return json.dumps(schema_result, indent=2)
        
        # Try to get additional table details using DESCRIBE DETAIL if supported
        try:
            detail_query = f"DESCRIBE DETAIL {table_name}"
            detail_result = await sql_executor.execute_query(detail_query, resource_type, resource_id)
            
            if detail_result.get('success'):
                table_detail = detail_result.get('data', [])
                if table_detail:
                    # Combine schema and detail information
                    result = {
                        "success": True,
                        "table_name": table_name,
                        "resource_type": resource_type,
                        "resource_id": resource_id,
                        "columns": schema_result.get('columns', []),
                        "table_detail": table_detail[0] if table_detail else {},
                        "column_count": schema_result.get('column_count', 0)
                    }
                else:
                    result = schema_result
            else:
                # Fall back to schema information only
                result = schema_result
                
        except Exception:
            # If DESCRIBE DETAIL fails, just return schema information
            result = schema_result
        
        return json.dumps(result, indent=2, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

# Data Management Tools
async def create_table_tool(table_name: str, columns: List[str], resource_type: str, resource_id: str) -> str:
    """Create a new table in Microsoft Fabric"""
    try:
        # Build CREATE TABLE statement
        columns_str = ", ".join(columns)
        create_sql = f"CREATE TABLE {table_name} ({columns_str})"
        
        # Execute the CREATE TABLE statement
        result = await sql_executor.execute_query(create_sql, resource_type, resource_id)
        
        if result.get('success'):
            return json.dumps({
                "success": True,
                "message": f"Table '{table_name}' created successfully",
                "table_name": table_name,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "sql": create_sql
            }, indent=2)
        else:
            return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def insert_data_tool(table_name: str, data: List[Dict], resource_type: str, resource_id: str) -> str:
    """Insert data into a Microsoft Fabric table"""
    try:
        if not data:
            return json.dumps({
                "success": False,
                "error": "No data provided"
            }, indent=2)
        
        # Get column names from first row
        columns = list(data[0].keys())
        
        # Build INSERT statements
        rows_inserted = 0
        errors = []
        
        for i, row in enumerate(data):
            try:
                # Build VALUES clause for this row
                values = []
                for col in columns:
                    value = row.get(col)
                    if value is None:
                        values.append("NULL")
                    elif isinstance(value, str):
                        # Escape single quotes in strings
                        escaped_value = value.replace("'", "''")
                        values.append(f"'{escaped_value}'")
                    else:
                        values.append(str(value))
                
                values_str = ", ".join(values)
                columns_str = ", ".join(columns)
                insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str})"
                
                # Execute the INSERT statement
                result = await sql_executor.execute_query(insert_sql, resource_type, resource_id)
                
                if result.get('success'):
                    rows_inserted += 1
                else:
                    errors.append(f"Row {i+1}: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                errors.append(f"Row {i+1}: {str(e)}")
        
        # Return results
        if rows_inserted > 0:
            result = {
                "success": True,
                "message": f"Inserted {rows_inserted} rows into '{table_name}'",
                "table_name": table_name,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "rows_inserted": rows_inserted,
                "total_rows": len(data)
            }
            
            if errors:
                result["errors"] = errors
                result["message"] += f" ({len(errors)} errors occurred)"
            
            return json.dumps(result, indent=2)
        else:
            return json.dumps({
                "success": False,
                "error": "No rows were inserted",
                "errors": errors
            }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

# Query Execution Tools
async def execute_query_tool(query: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None) -> str:
    """Execute a SQL query on Microsoft Fabric"""
    try:
        # If resource_type and resource_id are not provided, try to use defaults
        if not resource_type or not resource_id:
            # Try to use default lakehouse first
            if not resource_type:
                resource_type = "lakehouse"
            
            if not resource_id:
                resource_id = config['fabric'].get('default_lakehouse')
                if not resource_id:
                    # Try default warehouse
                    resource_type = "warehouse"
                    resource_id = config['fabric'].get('default_warehouse')
                    
                if not resource_id:
                    return json.dumps({
                        "success": False,
                        "error": "No resource_type/resource_id provided and no default lakehouse or warehouse configured"
                    }, indent=2)
        
        # Execute the query
        result = await sql_executor.execute_query(query, resource_type, resource_id)
        
        return json.dumps(result, indent=2, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def main():
    """Main entry point"""
    try:
        # Load configuration on startup
        load_config()
        print("Configuration loaded successfully")
        
        # Run the MCP server
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    except Exception as e:
        print(f"Failed to start server: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())