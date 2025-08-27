#!/usr/bin/env python3
"""
SQL Server MCP Server - A Model Context Protocol server for SQL Server operations
"""

import asyncio
import json
import yaml
import pyodbc
from typing import Dict, Any, List, Optional
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
import mcp.server.stdio

# Create the server instance
server = Server("sqlserver-mcp-server")

# Global config (loaded on startup)
config = None

def load_config():
    """Load configuration files"""
    global config
    
    try:
        # Get the directory where this script is located
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "config", "config.yaml")
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        # Fallback config for testing
        config = {
            'sql_server': {
                'driver': 'ODBC Driver 17 for SQL Server',
                'server': 'localhost',
                'database': 'Test_Steve',
                'username': 'steve_test',
                'password': 'SteveTest!23',
                'encrypt': 'no',
                'trust_server_certificate': 'yes',
                'use_windows_auth': False
            }
        }

def get_connection():
    """Create SQL Server connection"""
    sql_config = config['sql_server']
    
    if sql_config.get('use_windows_auth', False):
        # Use Windows Authentication
        conn_str = f"""
        DRIVER={{{sql_config['driver']}}};
        SERVER={sql_config['server']};
        DATABASE={sql_config['database']};
        Trusted_Connection=yes;
        Encrypt={sql_config.get('encrypt', 'yes')};
        TrustServerCertificate={sql_config.get('trust_server_certificate', 'yes')};
        Connection Timeout=30;
        """
    else:
        # Use SQL Server Authentication
        conn_str = f"""
        DRIVER={{{sql_config['driver']}}};
        SERVER={sql_config['server']};
        DATABASE={sql_config['database']};
        UID={sql_config['username']};
        PWD={sql_config['password']};
        Encrypt={sql_config.get('encrypt', 'yes')};
        TrustServerCertificate={sql_config.get('trust_server_certificate', 'yes')};
        Connection Timeout=30;
        """
    
    return pyodbc.connect(conn_str)

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available SQL Server tools"""
    return [
        Tool(
            name="execute_query",
            description="Execute a SQL query and return results",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL query to execute"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_table_schema",
            description="Get schema information for a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table"}
                },
                "required": ["table_name"]
            }
        ),
        Tool(
            name="list_tables",
            description="List all tables in the SQL Server database",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="create_table",
            description="Create a new table in SQL Server",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table to create"},
                    "columns": {"type": "array", "description": "Column definitions", "items": {"type": "string"}}
                },
                "required": ["table_name", "columns"]
            }
        ),
        Tool(
            name="insert_data",
            description="Insert data into a SQL Server table",
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
                    }
                },
                "required": ["table_name", "data"]
            }
        ),
        Tool(
            name="test_connection",
            description="Test the SQL Server connection and return basic info",
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
        elif name == "get_table_schema":
            result = await get_table_schema(arguments["table_name"])
        elif name == "list_tables":
            result = await list_tables()
        elif name == "create_table":
            result = await create_table(arguments["table_name"], arguments["columns"])
        elif name == "insert_data":
            result = await insert_data(arguments["table_name"], arguments["data"])
        elif name == "test_connection":
            result = await test_connection()
        else:
            result = f"Unknown tool: {name}"
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}"
        return [TextContent(type="text", text=error_msg)]

async def execute_query(query: str) -> str:
    """Execute a SQL query on SQL Server"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Check if it's a SELECT query
        if query.strip().upper().startswith("SELECT"):
            results = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            # Convert to list of dictionaries
            data = []
            for row in results:
                data.append(dict(zip(columns, row)))
            
            conn.close()
            return json.dumps({
                "success": True,
                "columns": columns,
                "data": data,
                "row_count": len(data)
            }, indent=2)
        else:
            # For INSERT, UPDATE, DELETE, etc.
            conn.commit()
            affected_rows = cursor.rowcount
            conn.close()
            return json.dumps({
                "success": True,
                "message": f"Query executed successfully. Affected rows: {affected_rows}"
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)

async def get_table_schema(table_name: str) -> str:
    """Get schema information for a SQL Server table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = f"""
        SELECT 
            COLUMN_NAME, 
            DATA_TYPE, 
            IS_NULLABLE, 
            COLUMN_DEFAULT,
            CHARACTER_MAXIMUM_LENGTH,
            NUMERIC_PRECISION,
            NUMERIC_SCALE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table_name}'
        ORDER BY ORDINAL_POSITION
        """
        
        cursor.execute(query)
        schema_info = cursor.fetchall()
        
        columns = []
        for col in schema_info:
            columns.append({
                "column_name": col[0],
                "data_type": col[1],
                "is_nullable": col[2] == "YES",
                "default_value": col[3],
                "max_length": col[4],
                "precision": col[5],
                "scale": col[6]
            })
        
        conn.close()
        
        return json.dumps({
            "table_name": table_name,
            "columns": columns
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)

async def list_tables() -> str:
    """List all tables in the SQL Server database"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # First, verify we're connected to the right database
        cursor.execute("SELECT DB_NAME() as current_database")
        current_db = cursor.fetchone()[0]
        
        # Use a more explicit query that doesn't rely on default schema context
        query = """
        SELECT 
            TABLE_SCHEMA,
            TABLE_NAME,
            TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
        """
        
        cursor.execute(query)
        table_info = cursor.fetchall()
        
        tables = []
        for table in table_info:
            tables.append({
                "schema": table[0],
                "table_name": table[1],
                "table_type": table[2],
                "full_name": f"{table[0]}.{table[1]}"
            })
        
        conn.close()
        
        return json.dumps({
            "success": True,
            "current_database": current_db,
            "tables": tables,
            "count": len(tables)
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)

async def create_table(table_name: str, columns: List[str]) -> str:
    """Create a new table in SQL Server"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        columns_str = ", ".join(columns)
        create_sql = f"CREATE TABLE {table_name} ({columns_str})"
        
        cursor.execute(create_sql)
        conn.commit()
        conn.close()
        
        return json.dumps({
            "success": True,
            "message": f"Table '{table_name}' created successfully",
            "sql": create_sql
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)

async def insert_data(table_name: str, data: List[Dict]) -> str:
    """Insert data into a SQL Server table"""
    try:
        if not data:
            return json.dumps({
                "success": False,
                "error": "No data provided"
            }, indent=2)
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get column names from first row
        columns = list(data[0].keys())
        placeholders = ", ".join(["?" for _ in columns])
        columns_str = ", ".join(columns)
        
        insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        # Insert all rows
        rows_inserted = 0
        for row in data:
            values = [row.get(col) for col in columns]
            cursor.execute(insert_sql, values)
            rows_inserted += 1
        
        conn.commit()
        conn.close()
        
        return json.dumps({
            "success": True,
            "message": f"Inserted {rows_inserted} rows into '{table_name}'",
            "rows_inserted": rows_inserted
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)

async def test_connection() -> str:
    """Test SQL Server connection and return basic database info"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get basic database info
        cursor.execute("SELECT DB_NAME() as current_database, USER_NAME() as database_user, @@VERSION as sql_version")
        info = cursor.fetchone()
        
        # Get schema list
        cursor.execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA ORDER BY SCHEMA_NAME")
        schemas = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return json.dumps({
            "success": True,
            "current_database": info[0],
            "database_user": info[1],
            "sql_version": info[2][:100] + "..." if len(info[2]) > 100 else info[2],  # Truncate version string
            "available_schemas": schemas
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)

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