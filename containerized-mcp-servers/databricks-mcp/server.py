#!/usr/bin/env python3
"""
Databricks MCP Server - A Model Context Protocol server for Databricks operations
Containerized version with environment variable support
"""

import asyncio
import json
import yaml
import requests
import os
from typing import Dict, Any, List, Optional
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
import mcp.server.stdio

# Import environment validator
from env_validator import validate_environment

# Create the server instance
server = Server("databricks-mcp-server")

# Global config (loaded on startup)
config = None

def load_config():
    """Load configuration from environment variables or config file"""
    global config
    
    try:
        # Try to load from environment variables first
        config = {
            'databricks': {
                'server_hostname': os.getenv('DATABRICKS_SERVER_HOSTNAME'),
                'http_path': os.getenv('DATABRICKS_HTTP_PATH'),
                'access_token': os.getenv('DATABRICKS_ACCESS_TOKEN'),
                'catalog': os.getenv('DATABRICKS_CATALOG', 'hive_metastore'),
                'schema': os.getenv('DATABRICKS_SCHEMA', 'default')
            }
        }
        
        # If environment variables are not set, try to load from config file
        if not all([config['databricks']['server_hostname'], 
                   config['databricks']['http_path'], 
                   config['databricks']['access_token']]):
            
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, "config", "config.yaml")
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
                    
                # Merge file config with environment variables (env vars take precedence)
                if 'databricks' in file_config:
                    for key, value in file_config['databricks'].items():
                        if not config['databricks'].get(key):
                            config['databricks'][key] = value
            
        # Validate required Databricks configuration fields
        if 'databricks' not in config:
            raise ValueError("Missing 'databricks' section in configuration")
            
        databricks_config = config['databricks']
        required_fields = ['server_hostname', 'http_path', 'access_token']
        
        for field in required_fields:
            if field not in databricks_config or not databricks_config[field]:
                raise ValueError(f"Missing required Databricks configuration field: {field}. Set DATABRICKS_{field.upper()} environment variable or provide in config file.")
        
        # Set default catalog and schema if not provided
        if 'catalog' not in databricks_config or not databricks_config['catalog']:
            databricks_config['catalog'] = 'hive_metastore'
        if 'schema' not in databricks_config or not databricks_config['schema']:
            databricks_config['schema'] = 'default'
            
    except FileNotFoundError:
        # If no config file and no env vars, raise error
        if not all([os.getenv('DATABRICKS_SERVER_HOSTNAME'), 
                   os.getenv('DATABRICKS_HTTP_PATH'), 
                   os.getenv('DATABRICKS_ACCESS_TOKEN')]):
            raise Exception("Configuration not found. Please set environment variables or provide config file.")
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
    """Create Databricks SQL connection with error handling and retries for serverless warehouses"""
    try:
        # Check if databricks-sql-connector is available
        try:
            from databricks import sql
        except ImportError:
            raise Exception("databricks-sql-connector package not installed. Please install it with: pip install databricks-sql-connector")
        
        if config is None:
            raise Exception("Configuration not loaded. Please check environment variables or config.yaml file.")
            
        databricks_config = config.get('databricks', {})
        if not databricks_config:
            raise Exception("Databricks configuration not found")
        
        # Validate configuration before attempting connection
        validate_connection()
        
        # Extended timeout for serverless warehouse cold starts
        connection = sql.connect(
            server_hostname=databricks_config['server_hostname'],
            http_path=databricks_config['http_path'],
            access_token=databricks_config['access_token'],
            _user_agent_entry="databricks-mcp-server/1.0",
            # Extended timeouts for serverless warehouses
            _connect_timeout=120,  # 2 minutes for connection
            _socket_timeout=300    # 5 minutes for query execution
        )
        
        # Test the connection with retry logic for cold starts
        max_retries = 3
        retry_delay = 10  # seconds
        
        for attempt in range(max_retries):
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                break  # Success, exit retry loop
            except Exception as e:
                if attempt < max_retries - 1 and ("timeout" in str(e).lower() or "warehouse" in str(e).lower()):
                    print(f"Connection attempt {attempt + 1} failed (likely cold start), retrying in {retry_delay}s...")
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise e
        
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
        
        # Extended timeout for serverless warehouse operations
        session.timeout = 120  # 2 minutes for REST API calls
        
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
    
    return f"{catalog}.{schema}.{table_name}"

def check_warehouse_status():
    """Check if the serverless warehouse is running and start it if needed"""
    try:
        session, base_url = get_rest_client()
        databricks_config = config['databricks']
        
        # Extract warehouse ID from http_path
        # Format: /sql/1.0/warehouses/{warehouse_id}
        http_path = databricks_config['http_path']
        if '/warehouses/' in http_path:
            warehouse_id = http_path.split('/warehouses/')[-1]
            
            # Get warehouse status
            response = session.get(f"{base_url}/api/2.0/sql/warehouses/{warehouse_id}")
            if response.status_code == 200:
                warehouse_data = response.json()
                state = warehouse_data.get('state', 'UNKNOWN')
                
                if state in ['STOPPED', 'STOPPING']:
                    print(f"Warehouse is {state}, starting it...")
                    # Start the warehouse
                    start_response = session.post(f"{base_url}/api/2.0/sql/warehouses/{warehouse_id}/start")
                    if start_response.status_code == 200:
                        print("Warehouse start request sent successfully")
                        return True, "Warehouse starting"
                    else:
                        return False, f"Failed to start warehouse: {start_response.text}"
                elif state == 'RUNNING':
                    return True, "Warehouse is running"
                else:
                    return True, f"Warehouse state: {state}"
            else:
                return False, f"Failed to get warehouse status: {response.text}"
        else:
            return True, "Cannot determine warehouse ID from http_path"
            
    except Exception as e:
        return False, f"Error checking warehouse status: {str(e)}"

@server.list_tools()
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
                    "data": {
                        "type": "array", 
                        "description": "Array of row objects to insert",
                        "items": {
                            "type": "object",
                            "description": "Row data as key-value pairs"
                        }
                    },
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
        ),
        Tool(
            name="check_warehouse_status",
            description="Check the status of the serverless warehouse and start it if needed",
            inputSchema={
                "type": "object",
                "properties": {}
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
            name="health_check",
            description="Comprehensive health check of the server and database connection",
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
        elif name == "check_warehouse_status":
            result = await check_warehouse_status_tool()
        elif name == "ping":
            result = await ping_tool()
        elif name == "health_check":
            result = await health_check_tool()
        else:
            result = f"Unknown tool: {name}"
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}"
        return [TextContent(type="text", text=error_msg)]

# SQL Operations
async def execute_query(query: str) -> str:
    """Execute a SQL query on Databricks"""
    try:
        # Check warehouse status first for serverless warehouses
        warehouse_ok, warehouse_msg = check_warehouse_status()
        if not warehouse_ok:
            return json.dumps({
                "success": False,
                "error": f"Warehouse check failed: {warehouse_msg}",
                "error_type": "WarehouseError"
            }, indent=2)
        
        connection = get_sql_connection()
        cursor = connection.cursor()
        
        # Execute the query
        cursor.execute(query)
        
        # Check if it's a SELECT query
        if query.strip().upper().startswith("SELECT") or query.strip().upper().startswith("SHOW") or query.strip().upper().startswith("DESCRIBE"):
            results = cursor.fetchall()
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            # Convert to list of dictionaries
            data = []
            for row in results:
                data.append(dict(zip(columns, row)))
            
            cursor.close()
            connection.close()
            
            return json.dumps({
                "success": True,
                "columns": columns,
                "data": data,
                "row_count": len(data),
                "query_type": "SELECT"
            }, indent=2, default=str)
        else:
            # For INSERT, UPDATE, DELETE, CREATE, etc.
            affected_rows = cursor.rowcount if cursor.rowcount >= 0 else 0
            cursor.close()
            connection.close()
            
            return json.dumps({
                "success": True,
                "message": f"Query executed successfully. Affected rows: {affected_rows}",
                "affected_rows": affected_rows,
                "query_type": "DML/DDL"
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

# Schema Operations
async def list_catalogs() -> str:
    """List all available catalogs"""
    try:
        connection = get_sql_connection()
        cursor = connection.cursor()
        
        cursor.execute("SHOW CATALOGS")
        results = cursor.fetchall()
        
        catalogs = []
        for row in results:
            catalogs.append({
                "catalog_name": row[0] if len(row) > 0 else "unknown"
            })
        
        cursor.close()
        connection.close()
        
        return json.dumps({
            "success": True,
            "catalogs": catalogs,
            "count": len(catalogs)
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def list_schemas(catalog: Optional[str] = None) -> str:
    """List schemas in a catalog"""
    try:
        connection = get_sql_connection()
        cursor = connection.cursor()
        
        # Use provided catalog or default from config
        catalog = catalog or config['databricks'].get('catalog', 'hive_metastore')
        
        cursor.execute(f"SHOW SCHEMAS IN {catalog}")
        results = cursor.fetchall()
        
        schemas = []
        for row in results:
            schemas.append({
                "catalog_name": catalog,
                "schema_name": row[0] if len(row) > 0 else "unknown"
            })
        
        cursor.close()
        connection.close()
        
        return json.dumps({
            "success": True,
            "catalog": catalog,
            "schemas": schemas,
            "count": len(schemas)
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def list_tables(catalog: Optional[str] = None, schema: Optional[str] = None) -> str:
    """List tables in a schema"""
    try:
        connection = get_sql_connection()
        cursor = connection.cursor()
        
        # Use provided values or defaults from config
        databricks_config = config['databricks']
        catalog = catalog or databricks_config.get('catalog', 'hive_metastore')
        schema = schema or databricks_config.get('schema', 'default')
        
        cursor.execute(f"SHOW TABLES IN {catalog}.{schema}")
        results = cursor.fetchall()
        
        tables = []
        for row in results:
            # SHOW TABLES returns: database, tableName, isTemporary
            tables.append({
                "catalog": catalog,
                "schema": row[0] if len(row) > 0 else schema,
                "table_name": row[1] if len(row) > 1 else "unknown",
                "is_temporary": row[2] if len(row) > 2 else False
            })
        
        cursor.close()
        connection.close()
        
        return json.dumps({
            "success": True,
            "catalog": catalog,
            "schema": schema,
            "tables": tables,
            "count": len(tables)
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def get_table_schema(table_name: str, catalog: Optional[str] = None, schema: Optional[str] = None) -> str:
    """Get detailed schema information for a table"""
    try:
        connection = get_sql_connection()
        cursor = connection.cursor()
        
        full_table_name = get_full_table_name(table_name, catalog, schema)
        
        cursor.execute(f"DESCRIBE TABLE EXTENDED {full_table_name}")
        results = cursor.fetchall()
        
        columns = []
        table_info = {}
        in_table_info = False
        
        for row in results:
            if len(row) >= 3:
                col_name = row[0]
                data_type = row[1]
                comment = row[2]
                
                # Check if we've reached the table information section
                if col_name and col_name.startswith('#'):
                    in_table_info = True
                    continue
                elif in_table_info and col_name:
                    # Parse table information
                    if ':' in str(col_name):
                        key, value = str(col_name).split(':', 1)
                        table_info[key.strip()] = value.strip()
                elif not in_table_info and col_name and col_name.strip():
                    # Regular column information
                    columns.append({
                        "column_name": col_name,
                        "data_type": data_type or "unknown",
                        "comment": comment or "",
                        "is_nullable": True  # Databricks doesn't enforce NOT NULL by default
                    })
        
        cursor.close()
        connection.close()
        
        return json.dumps({
            "success": True,
            "table_name": full_table_name,
            "columns": columns,
            "table_info": table_info,
            "column_count": len(columns)
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def describe_table(table_name: str, catalog: Optional[str] = None, schema: Optional[str] = None) -> str:
    """Get comprehensive table metadata including location and format"""
    try:
        connection = get_sql_connection()
        cursor = connection.cursor()
        
        full_table_name = get_full_table_name(table_name, catalog, schema)
        
        cursor.execute(f"DESCRIBE DETAIL {full_table_name}")
        results = cursor.fetchall()
        
        if results and len(results) > 0:
            # DESCRIBE DETAIL returns detailed information in a single row
            row = results[0]
            columns = [description[0] for description in cursor.description]
            
            table_detail = dict(zip(columns, row))
            
            cursor.close()
            connection.close()
            
            return json.dumps({
                "success": True,
                "table_name": full_table_name,
                "table_detail": table_detail
            }, indent=2, default=str)
        else:
            cursor.close()
            connection.close()
            
            return json.dumps({
                "success": False,
                "error": f"Table {full_table_name} not found or no details available"
            }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

# Table Management Operations
async def create_table(table_name: str, columns: List[str], catalog: Optional[str] = None, schema: Optional[str] = None) -> str:
    """Create a new table in Databricks"""
    try:
        connection = get_sql_connection()
        cursor = connection.cursor()
        
        full_table_name = get_full_table_name(table_name, catalog, schema)
        
        # Build CREATE TABLE statement
        columns_str = ", ".join(columns)
        create_sql = f"CREATE TABLE {full_table_name} ({columns_str})"
        
        cursor.execute(create_sql)
        cursor.close()
        connection.close()
        
        return json.dumps({
            "success": True,
            "message": f"Table '{full_table_name}' created successfully",
            "table_name": full_table_name,
            "sql": create_sql
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def insert_data(table_name: str, data: List[Dict], catalog: Optional[str] = None, schema: Optional[str] = None) -> str:
    """Insert data into a Databricks table"""
    try:
        if not data:
            return json.dumps({
                "success": False,
                "error": "No data provided for insertion"
            }, indent=2)
        
        connection = get_sql_connection()
        cursor = connection.cursor()
        
        full_table_name = get_full_table_name(table_name, catalog, schema)
        
        # Get column names from the first row
        columns = list(data[0].keys())
        columns_str = ", ".join(columns)
        
        # Build INSERT statement
        placeholders = ", ".join(["?" for _ in columns])
        insert_sql = f"INSERT INTO {full_table_name} ({columns_str}) VALUES ({placeholders})"
        
        # Prepare data for insertion
        rows_to_insert = []
        for row in data:
            row_values = [row.get(col) for col in columns]
            rows_to_insert.append(row_values)
        
        # Execute batch insert
        cursor.executemany(insert_sql, rows_to_insert)
        rows_inserted = len(rows_to_insert)
        
        cursor.close()
        connection.close()
        
        return json.dumps({
            "success": True,
            "message": f"Inserted {rows_inserted} rows into '{full_table_name}'",
            "table_name": full_table_name,
            "rows_inserted": rows_inserted
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

# Cluster and Job Management Operations
async def list_clusters() -> str:
    """List available Databricks compute clusters"""
    try:
        session, base_url = get_rest_client()
        
        response = session.get(f"{base_url}/api/2.0/clusters/list")
        response.raise_for_status()
        
        data = response.json()
        clusters = data.get('clusters', [])
        
        # Format cluster information
        cluster_info = []
        for cluster in clusters:
            cluster_info.append({
                "cluster_id": cluster.get("cluster_id"),
                "cluster_name": cluster.get("cluster_name"),
                "state": cluster.get("state"),
                "node_type_id": cluster.get("node_type_id"),
                "num_workers": cluster.get("num_workers"),
                "spark_version": cluster.get("spark_version"),
                "runtime_engine": cluster.get("runtime_engine"),
                "creator_user_name": cluster.get("creator_user_name")
            })
        
        return json.dumps({
            "success": True,
            "clusters": cluster_info,
            "count": len(cluster_info)
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def get_cluster_status(cluster_id: str) -> str:
    """Get status information for a specific cluster"""
    try:
        session, base_url = get_rest_client()
        
        response = session.get(f"{base_url}/api/2.0/clusters/get", params={"cluster_id": cluster_id})
        response.raise_for_status()
        
        cluster_data = response.json()
        
        return json.dumps({
            "success": True,
            "cluster_id": cluster_id,
            "cluster_info": {
                "cluster_name": cluster_data.get("cluster_name"),
                "state": cluster_data.get("state"),
                "state_message": cluster_data.get("state_message"),
                "node_type_id": cluster_data.get("node_type_id"),
                "num_workers": cluster_data.get("num_workers"),
                "spark_version": cluster_data.get("spark_version"),
                "runtime_engine": cluster_data.get("runtime_engine"),
                "creator_user_name": cluster_data.get("creator_user_name"),
                "start_time": cluster_data.get("start_time"),
                "terminated_time": cluster_data.get("terminated_time"),
                "last_state_loss_time": cluster_data.get("last_state_loss_time")
            }
        }, indent=2, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def list_jobs() -> str:
    """List available Databricks jobs"""
    try:
        session, base_url = get_rest_client()
        
        response = session.get(f"{base_url}/api/2.1/jobs/list")
        response.raise_for_status()
        
        data = response.json()
        jobs = data.get('jobs', [])
        
        # Format job information
        job_info = []
        for job in jobs:
            job_info.append({
                "job_id": job.get("job_id"),
                "job_name": job.get("settings", {}).get("name"),
                "job_type": job.get("settings", {}).get("job_type"),
                "creator_user_name": job.get("creator_user_name"),
                "created_time": job.get("created_time"),
                "timeout_seconds": job.get("settings", {}).get("timeout_seconds"),
                "max_concurrent_runs": job.get("settings", {}).get("max_concurrent_runs")
            })
        
        return json.dumps({
            "success": True,
            "jobs": job_info,
            "count": len(job_info)
        }, indent=2, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def run_job(job_id: str) -> str:
    """Trigger execution of a Databricks job"""
    try:
        session, base_url = get_rest_client()
        
        payload = {"job_id": int(job_id)}
        response = session.post(f"{base_url}/api/2.1/jobs/run-now", json=payload)
        response.raise_for_status()
        
        data = response.json()
        run_id = data.get("run_id")
        
        return json.dumps({
            "success": True,
            "message": f"Job {job_id} triggered successfully",
            "job_id": job_id,
            "run_id": run_id
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def get_job_run_status(run_id: str) -> str:
    """Get status of a job run"""
    try:
        session, base_url = get_rest_client()
        
        response = session.get(f"{base_url}/api/2.1/jobs/runs/get", params={"run_id": run_id})
        response.raise_for_status()
        
        run_data = response.json()
        
        return json.dumps({
            "success": True,
            "run_id": run_id,
            "run_info": {
                "job_id": run_data.get("job_id"),
                "run_name": run_data.get("run_name"),
                "state": run_data.get("state"),
                "life_cycle_state": run_data.get("state", {}).get("life_cycle_state"),
                "result_state": run_data.get("state", {}).get("result_state"),
                "state_message": run_data.get("state", {}).get("state_message"),
                "start_time": run_data.get("start_time"),
                "end_time": run_data.get("end_time"),
                "setup_duration": run_data.get("setup_duration"),
                "execution_duration": run_data.get("execution_duration"),
                "cleanup_duration": run_data.get("cleanup_duration"),
                "creator_user_name": run_data.get("creator_user_name")
            }
        }, indent=2, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def check_warehouse_status_tool() -> str:
    """Tool wrapper for checking warehouse status"""
    try:
        warehouse_ok, warehouse_msg = check_warehouse_status()
        return json.dumps({
            "success": warehouse_ok,
            "message": warehouse_msg,
            "status": "running" if warehouse_ok else "error"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def ping_tool() -> str:
    """Simple ping test to verify MCP server is responsive"""
    import time
    start_time = time.time()
    
    try:
        # Simple test that doesn't require Databricks connection
        response_time = round((time.time() - start_time) * 1000, 2)
        
        return json.dumps({
            "success": True,
            "message": "Pong! MCP server is responsive",
            "response_time_ms": response_time,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def health_check_tool() -> str:
    """Comprehensive health check"""
    try:
        from health_check import get_health_status
        return await get_health_status()
    except Exception as e:
        return json.dumps({
            "status": "unhealthy",
            "error": f"Health check failed: {str(e)}",
            "error_type": type(e).__name__
        }, indent=2)

async def main():
    """Main server entry point"""
    try:
        # Validate environment variables first
        print("🔍 Validating environment configuration...")
        if not validate_environment():
            print("❌ Environment validation failed. Server cannot start.")
            return
        
        # Load and validate configuration
        try:
            load_config()
            print("✅ Configuration loaded successfully")
        except Exception as e:
            print(f"❌ Configuration error: {e}")
            return
        
        print("🚀 Starting Databricks MCP Server...")
            
        # Run the server
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
            
    except Exception as e:
        # Log to stderr instead of stdout to avoid interfering with JSON-RPC
        import sys
        import traceback
        print(f"❌ Failed to start Databricks MCP Server: {e}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        raise

if __name__ == "__main__":
    asyncio.run(main())