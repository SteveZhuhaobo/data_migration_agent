#!/usr/bin/env python3
"""
Snowflake MCP Server - A Model Context Protocol server for Snowflake operations
Containerized version with environment variable support
"""

import asyncio
import json
import yaml
import os
from typing import Dict, Any, List, Optional
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
import mcp.server.stdio

# Import environment validator
from env_validator import validate_environment

# Snowflake connector imports
try:
    import snowflake.connector
    from snowflake.connector import DictCursor
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    SNOWFLAKE_AVAILABLE = True
except ImportError:
    SNOWFLAKE_AVAILABLE = False

# Create the server instance
server = Server("snowflake-mcp-server")

# Global config and connection (loaded on startup)
config = None
connection_pool = []

def load_config():
    """Load configuration from environment variables with fallback to config file"""
    global config
    
    try:
        # Initialize config structure
        config = {
            'snowflake': {}
        }
        
        # Load from environment variables first
        snowflake_config = config['snowflake']
        
        # Required fields
        snowflake_config['account'] = os.getenv('SNOWFLAKE_ACCOUNT')
        snowflake_config['user'] = os.getenv('SNOWFLAKE_USER')
        
        # Authentication - password or private key
        password = os.getenv('SNOWFLAKE_PASSWORD')
        private_key_path = os.getenv('SNOWFLAKE_PRIVATE_KEY_PATH')
        
        if password:
            snowflake_config['password'] = password
        elif private_key_path:
            snowflake_config['private_key_path'] = private_key_path
            private_key_passphrase = os.getenv('SNOWFLAKE_PRIVATE_KEY_PASSPHRASE')
            if private_key_passphrase:
                snowflake_config['private_key_passphrase'] = private_key_passphrase
        
        # Optional connection settings
        if os.getenv('SNOWFLAKE_DATABASE'):
            snowflake_config['database'] = os.getenv('SNOWFLAKE_DATABASE')
        if os.getenv('SNOWFLAKE_SCHEMA'):
            snowflake_config['schema'] = os.getenv('SNOWFLAKE_SCHEMA')
        if os.getenv('SNOWFLAKE_WAREHOUSE'):
            snowflake_config['warehouse'] = os.getenv('SNOWFLAKE_WAREHOUSE')
        if os.getenv('SNOWFLAKE_ROLE'):
            snowflake_config['role'] = os.getenv('SNOWFLAKE_ROLE')
        
        # Connection settings with defaults
        snowflake_config['timeout'] = int(os.getenv('SNOWFLAKE_TIMEOUT', '120'))
        snowflake_config['max_retries'] = int(os.getenv('SNOWFLAKE_MAX_RETRIES', '3'))
        snowflake_config['retry_delay'] = int(os.getenv('SNOWFLAKE_RETRY_DELAY', '5'))
        snowflake_config['pool_size'] = int(os.getenv('SNOWFLAKE_POOL_SIZE', '5'))
        snowflake_config['pool_timeout'] = int(os.getenv('SNOWFLAKE_POOL_TIMEOUT', '30'))
        
        # Fallback to config file if environment variables are not complete
        if not snowflake_config.get('account') or not snowflake_config.get('user'):
            try:
                config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "config.yaml")
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        file_config = yaml.safe_load(f)
                    
                    # Merge file config with environment config (env takes precedence)
                    if 'snowflake' in file_config:
                        for key, value in file_config['snowflake'].items():
                            if key not in snowflake_config or snowflake_config[key] is None:
                                snowflake_config[key] = value
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
        
        # Validate required fields
        required_fields = ['account', 'user']
        for field in required_fields:
            if not snowflake_config.get(field):
                raise ValueError(f"Missing required Snowflake configuration: {field}. Set SNOWFLAKE_{field.upper()} environment variable.")
        
        # Check authentication method
        has_password = snowflake_config.get('password')
        has_private_key = snowflake_config.get('private_key_path')
        
        if not has_password and not has_private_key:
            raise ValueError("Missing authentication method: set SNOWFLAKE_PASSWORD or SNOWFLAKE_PRIVATE_KEY_PATH environment variable")
        
        print("Configuration loaded successfully from environment variables")
        
    except Exception as e:
        raise Exception(f"Configuration error: {str(e)}")

def validate_connection():
    """Validate Snowflake connection configuration"""
    try:
        snowflake_config = config['snowflake']
        
        # Basic validation of account format
        account = snowflake_config['account']
        if not account or not isinstance(account, str):
            raise ValueError("Invalid account - must be a valid Snowflake account identifier")
            
        # Basic validation of user
        user = snowflake_config['user']
        if not user or not isinstance(user, str):
            raise ValueError("Invalid user - must be a valid username")
        
        # Validate authentication method
        if 'password' in snowflake_config and snowflake_config['password']:
            password = snowflake_config['password']
            if not isinstance(password, str) or len(password) < 1:
                raise ValueError("Invalid password - must be a non-empty string")
        elif 'private_key_path' in snowflake_config and snowflake_config['private_key_path']:
            key_path = snowflake_config['private_key_path']
            if not os.path.exists(key_path):
                raise ValueError(f"Private key file not found: {key_path}")
        else:
            raise ValueError("No valid authentication method configured")
            
        return True
        
    except Exception as e:
        raise Exception(f"Connection validation failed: {str(e)}")

def load_private_key():
    """Load and parse private key for key pair authentication"""
    try:
        snowflake_config = config['snowflake']
        key_path = snowflake_config['private_key_path']
        passphrase = snowflake_config.get('private_key_passphrase')
        
        with open(key_path, 'rb') as key_file:
            private_key_data = key_file.read()
        
        # Parse the private key
        if passphrase:
            passphrase_bytes = passphrase.encode('utf-8')
        else:
            passphrase_bytes = None
            
        private_key = load_pem_private_key(
            private_key_data,
            password=passphrase_bytes
        )
        
        # Serialize to DER format for Snowflake connector
        private_key_der = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        return private_key_der
        
    except Exception as e:
        raise Exception(f"Failed to load private key: {str(e)}")

async def create_snowflake_connection():
    """Create a new Snowflake connection"""
    if not SNOWFLAKE_AVAILABLE:
        raise Exception("snowflake-connector-python package not installed. Please install it with: pip install snowflake-connector-python")
    
    try:
        snowflake_config = config['snowflake']
        
        # Base connection parameters
        conn_params = {
            'account': snowflake_config['account'],
            'user': snowflake_config['user'],
            'timeout': snowflake_config.get('timeout', 120)
        }
        
        # Add optional parameters if configured
        if 'database' in snowflake_config and snowflake_config['database']:
            conn_params['database'] = snowflake_config['database']
        if 'schema' in snowflake_config and snowflake_config['schema']:
            conn_params['schema'] = snowflake_config['schema']
        if 'warehouse' in snowflake_config and snowflake_config['warehouse']:
            conn_params['warehouse'] = snowflake_config['warehouse']
        if 'role' in snowflake_config and snowflake_config['role']:
            conn_params['role'] = snowflake_config['role']
        
        # Authentication method
        if 'password' in snowflake_config and snowflake_config['password']:
            # Username/password authentication
            conn_params['password'] = snowflake_config['password']
        elif 'private_key_path' in snowflake_config and snowflake_config['private_key_path']:
            # Key pair authentication
            private_key = load_private_key()
            conn_params['private_key'] = private_key
        else:
            raise Exception("No valid authentication method configured")
        
        # Create connection
        connection = snowflake.connector.connect(**conn_params)
        
        # Test the connection
        cursor = connection.cursor()
        cursor.execute("SELECT CURRENT_VERSION()")
        version = cursor.fetchone()
        cursor.close()
        
        return connection
        
    except snowflake.connector.errors.DatabaseError as e:
        if "authentication" in str(e).lower() or "login" in str(e).lower():
            raise Exception(f"Authentication failed: {str(e)}")
        elif "timeout" in str(e).lower():
            raise Exception(f"Connection timeout: {str(e)}")
        else:
            raise Exception(f"Database error: {str(e)}")
    except Exception as e:
        if "Failed to load private key" in str(e):
            raise e
        else:
            raise Exception(f"Failed to connect to Snowflake: {str(e)}")

async def get_connection():
    """Get a connection from the pool or create a new one"""
    global connection_pool
    
    # Simple connection reuse - in production, implement proper pooling
    if connection_pool:
        try:
            # Test if connection is still valid
            conn = connection_pool[0]
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return conn
        except:
            # Connection is stale, remove it and create new one
            try:
                connection_pool[0].close()
            except:
                pass
            connection_pool.clear()
    
    # Create new connection
    connection = await create_snowflake_connection()
    connection_pool = [connection]  # Simple single connection pool
    return connection

async def test_authentication():
    """Test authentication by creating a connection"""
    try:
        connection = await create_snowflake_connection()
        
        # Get some basic info
        cursor = connection.cursor(DictCursor)
        cursor.execute("SELECT CURRENT_VERSION(), CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_WAREHOUSE()")
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        
        return True, "Authentication successful", result
    except Exception as e:
        return False, str(e), None

class SnowflakeConnectionManager:
    """Manages Snowflake connections with pooling and retry logic"""
    
    def __init__(self):
        self.connections = []
        # Initialize with defaults, will be updated when config is available
        self.max_connections = 5
        self.connection_timeout = 30
        
    def _ensure_config(self):
        """Ensure configuration is loaded and update settings"""
        if config and 'snowflake' in config:
            self.max_connections = config['snowflake'].get('pool_size', 5)
            self.connection_timeout = config['snowflake'].get('pool_timeout', 30)
    
    async def get_connection(self):
        """Get a connection from the pool or create a new one"""
        self._ensure_config()
        # For now, use simple single connection approach
        # In production, implement proper connection pooling
        return await get_connection()
    
    async def execute_query(self, query: str, warehouse: Optional[str] = None, 
                          database: Optional[str] = None, schema: Optional[str] = None) -> Dict[str, Any]:
        """Execute query with proper error handling and retry logic"""
        self._ensure_config()
        max_retries = config['snowflake'].get('max_retries', 3) if config else 3
        retry_delay = config['snowflake'].get('retry_delay', 5) if config else 5
        
        for attempt in range(max_retries + 1):
            try:
                connection = await self.get_connection()
                cursor = connection.cursor(DictCursor)
                
                # Set session parameters if provided
                if warehouse:
                    cursor.execute(f"USE WAREHOUSE {warehouse}")
                if database:
                    cursor.execute(f"USE DATABASE {database}")
                if schema:
                    cursor.execute(f"USE SCHEMA {schema}")
                
                # Execute the main query
                cursor.execute(query)
                
                # Handle different query types
                if self._is_select_query(query):
                    results = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    
                    cursor.close()
                    
                    return {
                        "success": True,
                        "columns": columns,
                        "data": results,
                        "row_count": len(results),
                        "query_type": "SELECT"
                    }
                else:
                    # For DML/DDL operations
                    affected_rows = cursor.rowcount if cursor.rowcount >= 0 else 0
                    cursor.close()
                    
                    return {
                        "success": True,
                        "message": f"Query executed successfully. Affected rows: {affected_rows}",
                        "affected_rows": affected_rows,
                        "query_type": "DML/DDL"
                    }
                    
            except snowflake.connector.errors.ProgrammingError as e:
                # SQL syntax or logic errors - don't retry
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": "ProgrammingError"
                }
            except snowflake.connector.errors.DatabaseError as e:
                if attempt < max_retries and ("timeout" in str(e).lower() or "connection" in str(e).lower()):
                    # Retry for connection/timeout issues
                    await asyncio.sleep(retry_delay * (2 ** attempt))
                    continue
                else:
                    return {
                        "success": False,
                        "error": str(e),
                        "error_type": "DatabaseError"
                    }
            except Exception as e:
                if attempt < max_retries and "timeout" in str(e).lower():
                    await asyncio.sleep(retry_delay * (2 ** attempt))
                    continue
                else:
                    return {
                        "success": False,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
        
        return {
            "success": False,
            "error": "Max retries exceeded",
            "error_type": "RetryExhausted"
        }
    
    def _is_select_query(self, query: str) -> bool:
        """Check if query is a SELECT statement"""
        query_upper = query.strip().upper()
        return (query_upper.startswith("SELECT") or 
                query_upper.startswith("SHOW") or 
                query_upper.startswith("DESCRIBE") or
                query_upper.startswith("EXPLAIN") or
                query_upper.startswith("WITH"))
    
    async def close_connections(self):
        """Close all connections in the pool"""
        global connection_pool
        for conn in connection_pool:
            try:
                conn.close()
            except:
                pass
        connection_pool.clear()

# Global instances (will be initialized after config is loaded)
connection_manager = None
sql_executor = None

class SnowflakeSQLExecutor:
    """SQL execution engine for Snowflake with enhanced functionality"""
    
    def __init__(self, connection_manager: SnowflakeConnectionManager):
        self.connection_manager = connection_manager
    
    async def execute_query(self, query: str, warehouse: Optional[str] = None, 
                          database: Optional[str] = None, schema: Optional[str] = None) -> Dict[str, Any]:
        """Execute SQL query with enhanced error handling and metadata"""
        try:
            result = await self.connection_manager.execute_query(query, warehouse, database, schema)
            
            # Add additional metadata for successful queries
            if result.get('success'):
                result['warehouse_used'] = warehouse or config['snowflake'].get('warehouse', 'Default')
                result['database_used'] = database or config['snowflake'].get('database', 'Default')
                result['schema_used'] = schema or config['snowflake'].get('schema', 'Default')
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def get_table_schema(self, table_name: str, database: Optional[str] = None, 
                             schema: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed table schema information"""
        try:
            # Build the fully qualified table name
            db = database or config['snowflake'].get('database')
            sch = schema or config['snowflake'].get('schema')
            
            if not db or not sch:
                return {
                    "success": False,
                    "error": "Database and schema must be specified or configured as defaults"
                }
            
            # Query to get table schema
            query = f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                COMMENT
            FROM {db}.INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = '{sch}' 
            AND TABLE_NAME = '{table_name.upper()}'
            ORDER BY ORDINAL_POSITION
            """
            
            result = await self.connection_manager.execute_query(query, database=database, schema=schema)
            
            if result.get('success'):
                columns = []
                for row in result.get('data', []):
                    columns.append({
                        "column_name": row.get('COLUMN_NAME', ''),
                        "data_type": row.get('DATA_TYPE', ''),
                        "is_nullable": row.get('IS_NULLABLE', 'YES') == 'YES',
                        "default_value": row.get('COLUMN_DEFAULT'),
                        "comment": row.get('COMMENT', '')
                    })
                
                return {
                    "success": True,
                    "table_name": f"{db}.{sch}.{table_name}",
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
    
    async def describe_table(self, table_name: str, database: Optional[str] = None, 
                           schema: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive table metadata including statistics"""
        try:
            # Get basic schema first
            schema_result = await self.get_table_schema(table_name, database, schema)
            
            if not schema_result.get('success'):
                return schema_result
            
            # Build the fully qualified table name
            db = database or config['snowflake'].get('database')
            sch = schema or config['snowflake'].get('schema')
            full_table_name = f"{db}.{sch}.{table_name}"
            
            # Get table statistics
            stats_query = f"""
            SELECT 
                ROW_COUNT,
                BYTES,
                CREATED,
                LAST_ALTERED,
                TABLE_TYPE,
                COMMENT
            FROM {db}.INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = '{sch}' 
            AND TABLE_NAME = '{table_name.upper()}'
            """
            
            stats_result = await self.connection_manager.execute_query(stats_query, database=database, schema=schema)
            
            result = schema_result.copy()
            
            if stats_result.get('success') and stats_result.get('data'):
                table_stats = stats_result['data'][0]
                result['table_statistics'] = {
                    "row_count": table_stats.get('ROW_COUNT'),
                    "size_bytes": table_stats.get('BYTES'),
                    "created": table_stats.get('CREATED'),
                    "last_altered": table_stats.get('LAST_ALTERED'),
                    "table_type": table_stats.get('TABLE_TYPE'),
                    "comment": table_stats.get('COMMENT')
                }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def get_tables(self, database: Optional[str] = None, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of tables in a schema"""
        try:
            db = database or config['snowflake'].get('database')
            sch = schema or config['snowflake'].get('schema')
            
            if not db or not sch:
                raise Exception("Database and schema must be specified or configured as defaults")
            
            query = f"""
            SELECT 
                TABLE_NAME,
                TABLE_TYPE,
                ROW_COUNT,
                BYTES,
                CREATED,
                COMMENT
            FROM {db}.INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = '{sch}'
            ORDER BY TABLE_NAME
            """
            
            result = await self.connection_manager.execute_query(query, database=database, schema=schema)
            
            if result.get('success'):
                return result.get('data', [])
            else:
                raise Exception(result.get('error', 'Failed to get tables'))
                
        except Exception as e:
            raise Exception(f"Failed to list tables: {str(e)}")

# Global SQL executor instance (will be initialized after config is loaded)
sql_executor = None

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available Snowflake tools"""
    return [
        Tool(
            name="execute_query",
            description="Execute a SQL query on Snowflake and return results",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL query to execute"},
                    "warehouse": {"type": "string", "description": "Warehouse to use for execution (optional)"},
                    "database": {"type": "string", "description": "Database to use (optional)"},
                    "schema": {"type": "string", "description": "Schema to use (optional)"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="list_databases",
            description="List all accessible Snowflake databases",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="list_schemas",
            description="List schemas in a database",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {"type": "string", "description": "Database name (optional, uses default if not provided)"}
                }
            }
        ),
        Tool(
            name="list_tables",
            description="List tables in a schema",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {"type": "string", "description": "Database name (optional)"},
                    "schema": {"type": "string", "description": "Schema name (optional)"}
                }
            }
        ),
        Tool(
            name="list_warehouses",
            description="List available Snowflake warehouses",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_table_schema",
            description="Get detailed schema information for a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table"},
                    "database": {"type": "string", "description": "Database name (optional)"},
                    "schema": {"type": "string", "description": "Schema name (optional)"}
                },
                "required": ["table_name"]
            }
        ),
        Tool(
            name="describe_table",
            description="Get comprehensive table metadata",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table"},
                    "database": {"type": "string", "description": "Database name (optional)"},
                    "schema": {"type": "string", "description": "Schema name (optional)"}
                },
                "required": ["table_name"]
            }
        ),
        Tool(
            name="create_table",
            description="Create a new table in Snowflake",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table to create"},
                    "columns": {"type": "array", "description": "Column definitions", "items": {"type": "string"}},
                    "database": {"type": "string", "description": "Database name (optional)"},
                    "schema": {"type": "string", "description": "Schema name (optional)"}
                },
                "required": ["table_name", "columns"]
            }
        ),
        Tool(
            name="insert_data",
            description="Insert data into a Snowflake table",
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
                    "database": {"type": "string", "description": "Database name (optional)"},
                    "schema": {"type": "string", "description": "Schema name (optional)"}
                },
                "required": ["table_name", "data"]
            }
        ),
        Tool(
            name="get_warehouse_status",
            description="Get status information for warehouses",
            inputSchema={
                "type": "object",
                "properties": {
                    "warehouse_name": {"type": "string", "description": "Warehouse name (optional, gets all if not provided)"}
                }
            }
        ),
        Tool(
            name="start_warehouse",
            description="Start/resume a Snowflake warehouse",
            inputSchema={
                "type": "object",
                "properties": {
                    "warehouse_name": {"type": "string", "description": "Name of the warehouse to start"}
                },
                "required": ["warehouse_name"]
            }
        ),
        Tool(
            name="stop_warehouse",
            description="Suspend a Snowflake warehouse",
            inputSchema={
                "type": "object",
                "properties": {
                    "warehouse_name": {"type": "string", "description": "Name of the warehouse to suspend"}
                },
                "required": ["warehouse_name"]
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
        ),
        Tool(
            name="test_connection",
            description="Test the connection to Snowflake and return basic info",
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
        elif name == "list_databases":
            result = await list_databases_tool()
        elif name == "list_schemas":
            result = await list_schemas_tool(arguments.get("database"))
        elif name == "list_tables":
            result = await list_tables_tool(arguments.get("database"), arguments.get("schema"))
        elif name == "list_warehouses":
            result = await list_warehouses_tool()
        elif name == "get_table_schema":
            result = await get_table_schema_tool(
                arguments["table_name"], 
                arguments.get("database"), 
                arguments.get("schema")
            )
        elif name == "describe_table":
            result = await describe_table_tool(
                arguments["table_name"], 
                arguments.get("database"), 
                arguments.get("schema")
            )
        elif name == "create_table":
            result = await create_table_tool(
                arguments["table_name"], 
                arguments["columns"], 
                arguments.get("database"), 
                arguments.get("schema")
            )
        elif name == "insert_data":
            result = await insert_data_tool(
                arguments["table_name"], 
                arguments["data"], 
                arguments.get("database"), 
                arguments.get("schema")
            )
        elif name == "execute_query":
            result = await execute_query_tool(
                arguments["query"], 
                arguments.get("warehouse"), 
                arguments.get("database"), 
                arguments.get("schema")
            )
        elif name == "get_warehouse_status":
            result = await get_warehouse_status_tool(arguments.get("warehouse_name"))
        elif name == "start_warehouse":
            result = await start_warehouse_tool(arguments["warehouse_name"])
        elif name == "stop_warehouse":
            result = await stop_warehouse_tool(arguments["warehouse_name"])
        elif name == "health_check":
            result = await health_check_tool()
        else:
            result = json.dumps({
                "success": False,
                "error": f"Unknown tool: {name}"
            }, indent=2)
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        error_result = json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)
        return [TextContent(type="text", text=error_result)]

# Tool implementations
async def ping_tool() -> str:
    """Simple ping test"""
    return json.dumps({
        "success": True,
        "message": "Snowflake MCP Server is running",
        "server_name": "snowflake-mcp-server",
        "snowflake_connector_available": SNOWFLAKE_AVAILABLE
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

async def test_connection_tool() -> str:
    """Test connection to Snowflake"""
    try:
        if config is None:
            return json.dumps({
                "success": False,
                "error": "Configuration not loaded"
            }, indent=2)
        
        # Validate configuration
        validate_connection()
        
        # Test authentication
        auth_success, auth_message, connection_info = await test_authentication()
        
        result = {
            "success": auth_success,
            "message": auth_message,
            "account": config['snowflake']['account'],
            "user": config['snowflake']['user'],
            "database": config['snowflake'].get('database', 'Not configured'),
            "schema": config['snowflake'].get('schema', 'Not configured'),
            "warehouse": config['snowflake'].get('warehouse', 'Not configured'),
            "snowflake_connector_available": SNOWFLAKE_AVAILABLE
        }
        
        if auth_success and connection_info:
            result["connection_info"] = connection_info
        
        return json.dumps(result, indent=2, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

# Resource Discovery Tools
async def list_databases_tool() -> str:
    """List all accessible Snowflake databases"""
    try:
        query = "SHOW DATABASES"
        result = await connection_manager.execute_query(query)
        
        if result.get('success'):
            databases = []
            for row in result.get('data', []):
                databases.append({
                    "name": row.get('name', ''),
                    "owner": row.get('owner', ''),
                    "comment": row.get('comment', ''),
                    "created_on": row.get('created_on'),
                    "retention_time": row.get('retention_time')
                })
            
            return json.dumps({
                "success": True,
                "databases": databases,
                "count": len(databases)
            }, indent=2, default=str)
        else:
            return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def list_schemas_tool(database: Optional[str] = None) -> str:
    """List schemas in a database"""
    try:
        # Use provided database or default from config
        db = database or config['snowflake'].get('database')
        if not db:
            return json.dumps({
                "success": False,
                "error": "No database provided and no default database configured"
            }, indent=2)
        
        query = f"SHOW SCHEMAS IN DATABASE {db}"
        result = await connection_manager.execute_query(query, database=db)
        
        if result.get('success'):
            schemas = []
            for row in result.get('data', []):
                schemas.append({
                    "name": row.get('name', ''),
                    "database_name": db,
                    "owner": row.get('owner', ''),
                    "comment": row.get('comment', ''),
                    "created_on": row.get('created_on')
                })
            
            return json.dumps({
                "success": True,
                "database": db,
                "schemas": schemas,
                "count": len(schemas)
            }, indent=2, default=str)
        else:
            return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def list_tables_tool(database: Optional[str] = None, schema: Optional[str] = None) -> str:
    """List tables in a schema"""
    try:
        global connection_manager, sql_executor
        
        # Initialize if not already done
        if connection_manager is None or sql_executor is None:
            if config is None:
                load_config()
            initialize_global_instances()
        
        tables = await sql_executor.get_tables(database, schema)
        
        # Format the response
        formatted_tables = []
        for table in tables:
            formatted_tables.append({
                "table_name": table.get('TABLE_NAME', ''),
                "table_type": table.get('TABLE_TYPE', ''),
                "row_count": table.get('ROW_COUNT'),
                "size_bytes": table.get('BYTES'),
                "created": table.get('CREATED'),
                "comment": table.get('COMMENT', '')
            })
        
        return json.dumps({
            "success": True,
            "database": database or config['snowflake'].get('database'),
            "schema": schema or config['snowflake'].get('schema'),
            "tables": formatted_tables,
            "count": len(formatted_tables)
        }, indent=2, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def list_warehouses_tool() -> str:
    """List available Snowflake warehouses"""
    try:
        query = "SHOW WAREHOUSES"
        result = await connection_manager.execute_query(query)
        
        if result.get('success'):
            warehouses = []
            for row in result.get('data', []):
                warehouses.append({
                    "name": row.get('name', ''),
                    "state": row.get('state', ''),
                    "type": row.get('type', ''),
                    "size": row.get('size', ''),
                    "running": row.get('running', 0),
                    "queued": row.get('queued', 0),
                    "is_default": row.get('is_default', 'N') == 'Y',
                    "auto_suspend": row.get('auto_suspend'),
                    "auto_resume": row.get('auto_resume', 'false') == 'true',
                    "comment": row.get('comment', '')
                })
            
            return json.dumps({
                "success": True,
                "warehouses": warehouses,
                "count": len(warehouses)
            }, indent=2, default=str)
        else:
            return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

# Table Schema and Metadata Tools
async def get_table_schema_tool(table_name: str, database: Optional[str] = None, schema: Optional[str] = None) -> str:
    """Get detailed schema information for a table"""
    try:
        schema_info = await sql_executor.get_table_schema(table_name, database, schema)
        return json.dumps(schema_info, indent=2, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def describe_table_tool(table_name: str, database: Optional[str] = None, schema: Optional[str] = None) -> str:
    """Get comprehensive table metadata"""
    try:
        table_info = await sql_executor.describe_table(table_name, database, schema)
        return json.dumps(table_info, indent=2, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

# Data Management Tools
async def create_table_tool(table_name: str, columns: List[str], database: Optional[str] = None, schema: Optional[str] = None) -> str:
    """Create a new table in Snowflake"""
    try:
        # Build CREATE TABLE statement
        columns_str = ", ".join(columns)
        
        # Build fully qualified table name
        db = database or config['snowflake'].get('database')
        sch = schema or config['snowflake'].get('schema')
        
        if db and sch:
            full_table_name = f"{db}.{sch}.{table_name}"
        else:
            full_table_name = table_name
        
        create_sql = f"CREATE TABLE {full_table_name} ({columns_str})"
        
        # Execute the CREATE TABLE statement
        result = await connection_manager.execute_query(create_sql, database=database, schema=schema)
        
        if result.get('success'):
            return json.dumps({
                "success": True,
                "message": f"Table '{full_table_name}' created successfully",
                "table_name": full_table_name,
                "database": db,
                "schema": sch,
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

async def insert_data_tool(table_name: str, data: List[Dict], database: Optional[str] = None, schema: Optional[str] = None) -> str:
    """Insert data into a Snowflake table"""
    try:
        if not data:
            return json.dumps({
                "success": False,
                "error": "No data provided"
            }, indent=2)
        
        # Build fully qualified table name
        db = database or config['snowflake'].get('database')
        sch = schema or config['snowflake'].get('schema')
        
        if db and sch:
            full_table_name = f"{db}.{sch}.{table_name}"
        else:
            full_table_name = table_name
        
        # Get column names from first row
        columns = list(data[0].keys())
        
        # Build INSERT statements (batch approach for better performance)
        rows_inserted = 0
        errors = []
        
        try:
            # Build VALUES clauses for all rows
            values_clauses = []
            for i, row in enumerate(data):
                try:
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
                    
                    values_clauses.append(f"({', '.join(values)})")
                    
                except Exception as e:
                    errors.append(f"Row {i+1}: {str(e)}")
            
            if values_clauses:
                # Execute batch insert
                columns_str = ", ".join(columns)
                values_str = ", ".join(values_clauses)
                insert_sql = f"INSERT INTO {full_table_name} ({columns_str}) VALUES {values_str}"
                
                result = await connection_manager.execute_query(insert_sql, database=database, schema=schema)
                
                if result.get('success'):
                    rows_inserted = len(values_clauses)
                else:
                    errors.append(f"Batch insert failed: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            errors.append(f"Batch processing failed: {str(e)}")
        
        # Return results
        if rows_inserted > 0:
            result = {
                "success": True,
                "message": f"Inserted {rows_inserted} rows into '{full_table_name}'",
                "table_name": full_table_name,
                "database": db,
                "schema": sch,
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
async def execute_query_tool(query: str, warehouse: Optional[str] = None, database: Optional[str] = None, schema: Optional[str] = None) -> str:
    """Execute a SQL query on Snowflake"""
    try:
        global connection_manager, sql_executor
        
        # Initialize if not already done
        if connection_manager is None or sql_executor is None:
            if config is None:
                load_config()
            initialize_global_instances()
        
        result = await sql_executor.execute_query(query, warehouse, database, schema)
        return json.dumps(result, indent=2, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

# Warehouse Management Tools
async def get_warehouse_status_tool(warehouse_name: Optional[str] = None) -> str:
    """Get status information for warehouses"""
    try:
        if warehouse_name:
            query = f"SHOW WAREHOUSES LIKE '{warehouse_name}'"
        else:
            query = "SHOW WAREHOUSES"
        
        result = await connection_manager.execute_query(query)
        
        if result.get('success'):
            warehouses = []
            for row in result.get('data', []):
                warehouse_info = {
                    "name": row.get('name', ''),
                    "state": row.get('state', ''),
                    "type": row.get('type', ''),
                    "size": row.get('size', ''),
                    "running": row.get('running', 0),
                    "queued": row.get('queued', 0),
                    "is_default": row.get('is_default', 'N') == 'Y',
                    "auto_suspend": row.get('auto_suspend'),
                    "auto_resume": row.get('auto_resume', 'false') == 'true',
                    "available": row.get('available', ''),
                    "provisioning": row.get('provisioning', ''),
                    "quiescing": row.get('quiescing', ''),
                    "other": row.get('other', ''),
                    "created_on": row.get('created_on'),
                    "resumed_on": row.get('resumed_on'),
                    "updated_on": row.get('updated_on'),
                    "owner": row.get('owner', ''),
                    "comment": row.get('comment', '')
                }
                warehouses.append(warehouse_info)
            
            return json.dumps({
                "success": True,
                "warehouses": warehouses,
                "count": len(warehouses)
            }, indent=2, default=str)
        else:
            return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def start_warehouse_tool(warehouse_name: str) -> str:
    """Start/resume a Snowflake warehouse"""
    try:
        query = f"ALTER WAREHOUSE {warehouse_name} RESUME"
        result = await connection_manager.execute_query(query)
        
        if result.get('success'):
            return json.dumps({
                "success": True,
                "message": f"Warehouse '{warehouse_name}' start command executed successfully",
                "warehouse_name": warehouse_name,
                "action": "RESUME"
            }, indent=2)
        else:
            return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

async def stop_warehouse_tool(warehouse_name: str) -> str:
    """Suspend a Snowflake warehouse"""
    try:
        query = f"ALTER WAREHOUSE {warehouse_name} SUSPEND"
        result = await connection_manager.execute_query(query)
        
        if result.get('success'):
            return json.dumps({
                "success": True,
                "message": f"Warehouse '{warehouse_name}' suspend command executed successfully",
                "warehouse_name": warehouse_name,
                "action": "SUSPEND"
            }, indent=2)
        else:
            return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

def initialize_global_instances():
    """Initialize global instances after config is loaded"""
    global connection_manager, sql_executor
    
    if config is None:
        raise Exception("Configuration must be loaded before initializing instances")
    
    connection_manager = SnowflakeConnectionManager()
    sql_executor = SnowflakeSQLExecutor(connection_manager)

async def main():
    """Main entry point"""
    try:
        # Validate environment variables first
        print("🔍 Validating environment configuration...")
        if not validate_environment():
            print("❌ Environment validation failed. Server cannot start.")
            return
        
        # Load configuration on startup
        load_config()
        print("✅ Configuration loaded successfully")
        
        # Initialize global instances after config is loaded
        initialize_global_instances()
        print("✅ Global instances initialized successfully")
        
        print("🚀 Starting Snowflake MCP Server...")
        
        # Run the MCP server
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())