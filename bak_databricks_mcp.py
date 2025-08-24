#!/usr/bin/env python3
"""
Databricks MCP Server - A Model Context Protocol server for Databricks operations
"""

import asyncio
import json
import yaml
import requests
from typing import Dict, Any, List, Optional
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
import mcp.server.stdio

# Create the server instance
server = Server("databricks-mcp-server")

# Global config (loaded on startup)
config = None

def load_config():
    """Load configuration files with validation"""
    global config
    
    try:
        with open("config/config.yaml", 'r') as f:
            config = yaml.safe_load(f)
            
        # Validate required Databricks configuration fields
        if 'databricks' not in config:
            raise ValueError("Missing 'databricks' section in configuration")
            
        databricks_config = config['databricks']
        required_fields = ['server_hostname', 'http_path', 'access_token']
        
        for field in required_fields:
            if field not in databricks_config or not databricks_config[field]:
                raise ValueError(f"Missing required Databricks configuration field: {field}")
        
        # Set default catalog and schema if not provided
        if 'catalog' not in databricks_config:
            databricks_config['catalog'] = 'hive_metastore'
        if 'schema' not in databricks_config:
            databricks_config['schema'] = 'default'
            
    except FileNotFoundError:
        raise Exception("Configuration file 'config/config.yaml' not found")
    except yaml.YAMLError as e:
        raise Exception(f"Error parsing YAML configuration file: {str(e)}")
    except Exception as e:
        raise Exception(f"Configuration error: {str(e)}")

def validate_connection():
    """Validate Databricks connection configuration"""
    try:
        databricks_config = config['databricks']
        
        # Basic validation of hostname format
        hostname = databricks_config['server_hostname']
        if not hostname or not isinstance(hostname, str):
            raise ValueError("Invalid server_hostname")
            
        # Basic validation of http_path format
        http_path = databricks_config['http_path']
        if not http_path or not isinstance(http_path, str) or not http_path.startswith('/'):
            raise ValueError("Invalid http_path - must start with '/'")
            
        # Basic validation of access_token
        access_token = databricks_config['access_token']
        if not access_token or not isinstance(access_token, str) or len(access_token) < 10:
            raise ValueError("Invalid access_token - must be a valid token string")
            
        return True
        
    except Exception as e:
        raise Exception(f"Connection validation failed: {str(e)}")

def get_sql_connection():
    """Create Databricks SQL connection with error handling and retries"""
    try:
        from databricks import sql
        
        databricks_config = config['databricks']
        
        # Validate configuration before attempting connection
        validate_connection()
        
        connection = sql.connect(
            server_hostname=databricks_config['server_hostname'],
            http_path=databricks_config['http_path'],
            access_token=databricks_config['access_token'],
            _user_agent_entry="databricks-mcp-server/1.0"
        )
        
        # Test the connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        
        return connection
        
    except ImportError:
        raise Exception("databricks-sql-connector not installed. Please install with: pip install databricks-sql-connector")
    except Exception as e:
        if "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
            raise Exception(f"Authentication failed: Please check your access token. Error: {str(e)}")
        elif "timeout" in str(e).lower():
            raise Exception(f"Connection timeout: Please check your server hostname and network connectivity. Error: {str(e)}")
        else:
            raise Exception(f"Failed to connect to Databricks: {str(e)}")

def get_rest_client():
    """Create REST API client session with authentication and error handling"""
    try:
        databricks_config = config['databricks']
        
        # Validate configuration
        validate_connection()
        
        session = requests.Session()
        session.headers.update({
            'Authorization': f'Bearer {databricks_config["access_token"]}',
            'Content-Type': 'application/json',
            'User-Agent': 'databricks-mcp-server/1.0'
        })
        
        # Set timeout for requests
        session.timeout = 30
        
        # Test the connection with a simple API call
        base_url = f"https://{databricks_config['server_hostname']}"
        response = session.get(f"{base_url}/api/2.0/clusters/list")
        
        if response.status_code == 401:
            raise Exception("Authentication failed: Invalid access token")
        elif response.status_code == 403:
            raise Exception("Access denied: Insufficient permissions")
        elif response.status_code >= 400:
            raise Exception(f"API request failed with status {response.status_code}: {response.text}")
        
        return session, base_url
        
    except requests.exceptions.Timeout:
        raise Exception("Request timeout: Please check your network connectivity")
    except requests.exceptions.ConnectionError:
        raise Exception("Connection error: Please check your server hostname")
    except Exception as e:
        if "Authentication failed" in str(e) or "Access denied" in str(e):
            raise e
        else:
            raise Exception(f"Failed to create REST client: {str(e)}")

def get_full_table_name(table_name: str, catalog: Optional[str] = None, schema: Optional[str] = None) -> str:
    """Construct full table name with catalog and schema"""
    databricks_config = config['databricks']
    
    # Use provided values or fall back to config defaults
    catalog = catalog or databricks_config.get('catalog', 'hive_metastore')
    schema = schema or databricks_config.get('schema', 'default')
    
    return f"{catalog}.{schema}.{table_name}"@server.lis
t_tools()
async def list_tools() -> List[Tool]:
    """List available Databricks tools"""
    return [
        Tool(
            name="execute_query",
            description="Execute a SQL query on Databricks and return results",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL query to execute"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="list_catalogs",
            description="List all available catalogs in Databricks",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="list_schemas",
            description="List schemas in a catalog",
            inputSchema={
                "type": "object",
                "properties": {
                    "catalog": {"type": "string", "description": "Catalog name (optional, uses default if not provided)"}
                }
            }
        ),
        Tool(
            name="list_tables",
            description="List tables in a schema",
            inputSchema={
                "type": "object",
                "properties": {
                    "catalog": {"type": "string", "description": "Catalog name (optional)"},
                    "schema": {"type": "string", "description": "Schema name (optional)"}
                }
            }
        ),
        Tool(
            name="get_table_schema",
            description="Get detailed schema information for a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table"},
                    "catalog": {"type": "string", "description": "Catalog name (optional)"},
                    "schema": {"type": "string", "description": "Schema name (optional)"}
                },
                "required": ["table_name"]
            }
        ),
        Tool(
            name="describe_table",
            description="Get comprehensive table metadata including location and format",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table"},
                    "catalog": {"type": "string", "description": "Catalog name (optional)"},
                    "schema": {"type": "string", "description": "Schema name (optional)"}
                },
                "required": ["table_name"]
            }
        ),
        Tool(
            name="create_table",
            description="Create a new table in Databricks",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table to create"},
                    "columns": {"type": "array", "description": "Column definitions", "items": {"type": "string"}},
                    "catalog": {"type": "string", "description": "Catalog name (optional)"},
                    "schema": {"type": "string", "description": "Schema name (optional)"}
                },
                "required": ["table_name", "columns"]
            }
        ),
        Tool(
            name="insert_data",
            description="Insert data into a Databricks table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table"},
                    "data": {"type": "array", "description": "Array of row objects to insert"},
                    "catalog": {"type": "string", "description": "Catalog name (optional)"},
                    "schema": {"type": "string", "description": "Schema name (optional)"}
                },
                "required": ["table_name", "data"]
            }
        ),
        Tool(
            name="list_clusters",
            description="List available Databricks compute clusters",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_cluster_status",
            description="Get status information for a specific cluster",
            inputSchema={
                "type": "object",
                "properties": {
                    "cluster_id": {"type": "string", "description": "ID of the cluster"}
                },
                "required": ["cluster_id"]
            }
        ),
        Tool(
            name="list_jobs",
            description="List available Databricks jobs",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="run_job",
            description="Trigger execution of a Databricks job",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {"type": "string", "description": "ID of the job to run"}
                },
                "required": ["job_id"]
            }
        ),
        Tool(
            name="get_job_run_status",
            description="Get status of a job run",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {"type": "string", "description": "ID of the job run"}
                },
                "required": ["run_id"]
            }
        )
    ]@serv
er.call_tool()
async def call_tool(name: str, arguments: Optional[Dict[str, Any]] = None) -> List[TextContent]:
    """Handle tool calls"""
    if arguments is None:
        arguments = {}
    
    try:
        if name == "execute_query":
            result = await execute_query(arguments["query"])
        elif name == "list_catalogs":
            result = await list_catalogs()
        elif name == "list_schemas":
            result = await list_schemas(arguments.get("catalog"))
        elif name == "list_tables":
            result = await list_tables(arguments.get("catalog"), arguments.get("schema"))
        elif name == "get_table_schema":
            result = await get_table_schema(
                arguments["table_name"], 
                arguments.get("catalog"), 
                arguments.get("schema")
            )
        elif name == "describe_table":
            result = await describe_table(
                arguments["table_name"], 
                arguments.get("catalog"), 
                arguments.get("schema")
            )
        elif name == "create_table":
            result = await create_table(
                arguments["table_name"], 
                arguments["columns"],
                arguments.get("catalog"), 
                arguments.get("schema")
            )
        elif name == "insert_data":
            result = await insert_data(
                arguments["table_name"], 
                arguments["data"],
                arguments.get("catalog"), 
                arguments.get("schema")
            )
        elif name == "list_clusters":
            result = await list_clusters()
        elif name == "get_cluster_status":
            result = await get_cluster_status(arguments["cluster_id"])
        elif name == "list_jobs":
            result = await list_jobs()
        elif name == "run_job":
            result = await run_job(arguments["job_id"])
        elif name == "get_job_run_status":
            result = await get_job_run_status(arguments["run_id"])
        else:
            result = f"Unknown tool: {name}"
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}"
        return [TextContent(type="text", text=error_msg)]