import asyncio
import json
import yaml
import pyodbc
import pandas as pd
from databricks import sql
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import mcp.server.stdio

# Create the server instance
server = Server("data-migration-server")

# Global config and mapping (loaded on startup)
config = None
mapping = None

def load_config():
    """Load configuration files"""
    global config, mapping
    
    try:
        with open("config/config.yaml", 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        # Fallback config for testing
        config = {
            'sql_server': {
                'driver': 'ODBC Driver 17 for SQL Server',
                'server': 'localhost',
                'database': 'testdb',
                'username': 'user',
                'password': 'pass'
            },
            'databricks': {
                'server_hostname': 'your-workspace.databricks.com',
                'http_path': '/sql/1.0/warehouses/your-warehouse',
                'access_token': 'your-token',
                'catalog': 'main',
                'schema': 'default'
            }
        }
    
    try:
        with open("mappings/column_mapping.json", 'r') as f:
            mapping = json.load(f)
    except FileNotFoundError:
        # Fallback mapping for testing
        mapping = {
            'tables': {
                'test_table': {
                    'source_table': 'test_table',
                    'target_table': 'test_table_target',
                    'columns': {
                        'id': {'target': 'id', 'type': 'INT', 'transformation': None},
                        'name': {'target': 'name', 'type': 'STRING', 'transformation': None}
                    }
                }
            }
        }

def get_sql_connection():
    """Create SQL Server connection"""
    conn_str = f"""
    DRIVER={{{config['sql_server']['driver']}}};
    SERVER={config['sql_server']['server']};
    DATABASE={config['sql_server']['database']};
    UID={config['sql_server']['username']};
    PWD={config['sql_server']['password']};
    Encrypt=yes;
    TrustServerCertificate=yes;
    Connection Timeout=30;
    """
    return pyodbc.connect(conn_str)

def get_databricks_connection():
    """Create Databricks connection"""
    return sql.connect(
        server_hostname=config['databricks']['server_hostname'],
        http_path=config['databricks']['http_path'],
        access_token=config['databricks']['access_token']
    )

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="get_sql_schema",
            description="Get schema information from SQL Server table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string"}
                },
                "required": ["table_name"]
            }
        ),
        Tool(
            name="extract_data",
            description="Extract data from SQL Server table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string"},
                    "limit": {"type": "integer", "default": 1000}
                },
                "required": ["table_name"]
            }
        ),
        Tool(
            name="create_databricks_table",
            description="Create table in Databricks",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string"},
                    "schema": {"type": "object"}
                },
                "required": ["table_name", "schema"]
            }
        ),
        Tool(
            name="load_data",
            description="Load transformed data into Databricks",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string"},
                    "data": {"type": "array"}
                },
                "required": ["table_name", "data"]
            }
        ),
        Tool(
            name="get_mapping",
            description="Get column mapping for a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string"}
                },
                "required": ["table_name"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Optional[Dict[str, Any]] = None) -> List[TextContent]:
    """Handle tool calls"""
    if arguments is None:
        arguments = {}
    
    try:
        if name == "get_sql_schema":
            result = await get_sql_schema(arguments["table_name"])
        elif name == "extract_data":
            result = await extract_data(arguments["table_name"], arguments.get("limit", 1000))
        elif name == "create_databricks_table":
            result = await create_databricks_table(arguments["table_name"], arguments["schema"])
        elif name == "load_data":
            result = await load_data(arguments["table_name"], arguments["data"])
        elif name == "get_mapping":
            result = await get_mapping(arguments["table_name"])
        else:
            result = f"Unknown tool: {name}"
        
        # Return as TextContent
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}"
        return [TextContent(type="text", text=error_msg)]

async def get_sql_schema(table_name: str) -> str:
    """Get schema information from SQL Server"""
    try:
        # For testing without actual DB connection
        ##if config['sql_server']['server'] == 'localhost':
            ##return json.dumps({
                ##"message": f"Schema for {table_name} (mock data)",
                ##"columns": [
                    ##{"column_name": "id", "data_type": "int", "is_nullable": "NO"},
                    ##{"column_name": "name", "data_type": "varchar", "is_nullable": "YES"}
                ##]
            ##}, indent=2)
        
        conn = get_sql_connection()
        cursor = conn.cursor()
        
        query = f"""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table_name.split('.')[-1]}'
        ORDER BY ORDINAL_POSITION
        """
        
        cursor.execute(query)
        columns = cursor.fetchall()
        
        schema_info = []
        for col in columns:
            schema_info.append({
                "column_name": col[0],
                "data_type": col[1],
                "is_nullable": col[2],
                "max_length": col[3]
            })
        
        conn.close()
        return json.dumps(schema_info, indent=2)
    except Exception as e:
        return f"Error getting schema: {str(e)}"

async def extract_data(table_name: str, limit: int = 1000) -> str:
    """Extract data from SQL Server"""
    try:
        # For testing without actual DB connection
        ##if config['sql_server']['server'] == 'localhost':
            ##return json.dumps([
                ##{"id": 1, "name": "Test Record 1"},
                ##{"id": 2, "name": "Test Record 2"}
            ##])
        
        conn = get_sql_connection()
        
        # Get table mapping
        table_config = None
        for table_key, config_data in mapping['tables'].items():
            if config_data['source_table'] == table_name:
                table_config = config_data
                break
        
        if not table_config:
            return f"No mapping found for table: {table_name}"
        
        # Build SELECT query with transformations
        select_columns = []
        for source_col, col_config in table_config['columns'].items():
            if col_config['transformation']:
                select_columns.append(f"{col_config['transformation']} as {source_col}")
            else:
                select_columns.append(source_col)
        
        query = f"SELECT TOP {limit} {', '.join(select_columns)} FROM {table_name}"
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Convert to JSON for transport
        data = df.to_dict('records')
        return json.dumps(data)
        
    except Exception as e:
        return f"Error extracting data: {str(e)}"

async def create_databricks_table(table_name: str, schema: Dict) -> str:
    """Create table in Databricks"""
    try:
        # For testing without actual Databricks connection
        if config['databricks']['server_hostname'] == 'your-workspace.databricks.com':
            return f"Mock: Table {table_name} would be created with schema: {json.dumps(schema)}"
        
        conn = get_databricks_connection()
        cursor = conn.cursor()
        
        # Get target table mapping
        table_config = mapping['tables'].get(table_name)
        if not table_config:
            return f"No mapping found for table: {table_name}"
        
        target_table = table_config['target_table']
        
        # Build CREATE TABLE statement
        columns = []
        for source_col, col_config in table_config['columns'].items():
            target_col = col_config['target']
            data_type = col_config['type']
            columns.append(f"{target_col} {data_type}")
        
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {config['databricks']['catalog']}.{config['databricks']['schema']}.{target_table} (
            {', '.join(columns)}
        )
        """
        
        cursor.execute(create_sql)
        conn.close()
        
        return f"Table {target_table} created successfully"
        
    except Exception as e:
        return f"Error creating table: {str(e)}"

async def load_data(table_name: str, data: List[Dict]) -> str:
    """Load data into Databricks"""
    try:
        # For testing without actual Databricks connection
        if config['databricks']['server_hostname'] == 'your-workspace.databricks.com':
            return f"Mock: Would load {len(data)} rows into {table_name}"
        
        table_config = mapping['tables'].get(table_name)
        if not table_config:
            return f"No mapping found for table: {table_name}"
        
        target_table = table_config['target_table']
        
        # Transform column names
        transformed_data = []
        for row in data:
            new_row = {}
            for source_col, col_config in table_config['columns'].items():
                if source_col in row:
                    new_row[col_config['target']] = row[source_col]
            transformed_data.append(new_row)
        
        if not transformed_data:
            return "No data to load"
        
        # Create DataFrame and load to Databricks
        df = pd.DataFrame(transformed_data)
        
        conn = get_databricks_connection()
        cursor = conn.cursor()
        
        # Simple INSERT (for small datasets)
        full_table_name = f"{config['databricks']['catalog']}.{config['databricks']['schema']}.{target_table}"
        
        for _, row in df.iterrows():
            columns = ', '.join(row.index)
            values = ', '.join([f"'{v}'" if isinstance(v, str) else str(v) for v in row.values])
            insert_sql = f"INSERT INTO {full_table_name} ({columns}) VALUES ({values})"
            cursor.execute(insert_sql)
        
        conn.close()
        
        return f"Loaded {len(transformed_data)} rows into {target_table}"
        
    except Exception as e:
        return f"Error loading data: {str(e)}"

async def get_mapping(table_name: str) -> str:
    """Get column mapping for a table"""
    table_config = mapping['tables'].get(table_name)
    if table_config:
        return json.dumps(table_config, indent=2)
    else:
        return f"No mapping found for table: {table_name}"

async def main():
    """Main server entry point"""
    # Load configuration
    load_config()
    
    # Run the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())