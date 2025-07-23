import asyncio
import json
import yaml
import pyodbc
import pandas as pd
from databricks import sql
from mcp.server import Server
from mcp.types import Resource, Tool
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class DataMigrationServer:
    def __init__(self, config_path: str = "config/config.yaml", mapping_path: str = "mappings/column_mapping.json"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        with open(mapping_path, 'r') as f:
            self.mapping = json.load(f)
        
        self.server = Server("data-migration-server")
        self._setup_tools()
    
    def _setup_tools(self):
        """Setup MCP tools for data migration"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
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
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[str]:
            if name == "get_sql_schema":
                return await self._get_sql_schema(arguments["table_name"])
            elif name == "extract_data":
                return await self._extract_data(arguments["table_name"], arguments.get("limit", 1000))
            elif name == "create_databricks_table":
                return await self._create_databricks_table(arguments["table_name"], arguments["schema"])
            elif name == "load_data":
                return await self._load_data(arguments["table_name"], arguments["data"])
            elif name == "get_mapping":
                return await self._get_mapping(arguments["table_name"])
            else:
                return [f"Unknown tool: {name}"]
    
    def _get_sql_connection(self):
        """Create SQL Server connection"""
        conn_str = f"""
        DRIVER={{{self.config['sql_server']['driver']}}};
        SERVER={self.config['sql_server']['server']};
        DATABASE={self.config['sql_server']['database']};
        UID={self.config['sql_server']['username']};
        PWD={self.config['sql_server']['password']};
        Encrypt=yes;
        TrustServerCertificate=no;
        Connection Timeout=30;
        """
        return pyodbc.connect(conn_str)
    
    def _get_databricks_connection(self):
        """Create Databricks connection"""
        return sql.connect(
            server_hostname=self.config['databricks']['server_hostname'],
            http_path=self.config['databricks']['http_path'],
            access_token=self.config['databricks']['access_token']
        )
    
    async def _get_sql_schema(self, table_name: str) -> List[str]:
        """Get schema information from SQL Server"""
        try:
            conn = self._get_sql_connection()
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
            return [json.dumps(schema_info, indent=2)]
        except Exception as e:
            return [f"Error getting schema: {str(e)}"]
    
    async def _extract_data(self, table_name: str, limit: int = 1000) -> List[str]:
        """Extract data from SQL Server"""
        try:
            conn = self._get_sql_connection()
            
            # Get table mapping
            table_config = None
            for table_key, config in self.mapping['tables'].items():
                if config['source_table'] == table_name:
                    table_config = config
                    break
            
            if not table_config:
                return [f"No mapping found for table: {table_name}"]
            
            # Build SELECT query with transformations
            select_columns = []
            for source_col, config in table_config['columns'].items():
                if config['transformation']:
                    select_columns.append(f"{config['transformation']} as {source_col}")
                else:
                    select_columns.append(source_col)
            
            query = f"SELECT TOP {limit} {', '.join(select_columns)} FROM {table_name}"
            
            df = pd.read_sql(query, conn)
            conn.close()
            
            # Convert to JSON for transport
            data = df.to_dict('records')
            return [json.dumps(data)]
            
        except Exception as e:
            return [f"Error extracting data: {str(e)}"]
    
    async def _create_databricks_table(self, table_name: str, schema: Dict) -> List[str]:
        """Create table in Databricks"""
        try:
            conn = self._get_databricks_connection()
            cursor = conn.cursor()
            
            # Get target table mapping
            table_config = self.mapping['tables'].get(table_name)
            if not table_config:
                return [f"No mapping found for table: {table_name}"]
            
            target_table = table_config['target_table']
            
            # Build CREATE TABLE statement
            columns = []
            for source_col, config in table_config['columns'].items():
                target_col = config['target']
                data_type = config['type']
                columns.append(f"{target_col} {data_type}")
            
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {self.config['databricks']['catalog']}.{self.config['databricks']['schema']}.{target_table} (
                {', '.join(columns)}
            )
            """
            
            cursor.execute(create_sql)
            conn.close()
            
            return [f"Table {target_table} created successfully"]
            
        except Exception as e:
            return [f"Error creating table: {str(e)}"]
    
    async def _load_data(self, table_name: str, data: List[Dict]) -> List[str]:
        """Load data into Databricks"""
        try:
            table_config = self.mapping['tables'].get(table_name)
            if not table_config:
                return [f"No mapping found for table: {table_name}"]
            
            target_table = table_config['target_table']
            
            # Transform column names
            transformed_data = []
            for row in data:
                new_row = {}
                for source_col, config in table_config['columns'].items():
                    if source_col in row:
                        new_row[config['target']] = row[source_col]
                transformed_data.append(new_row)
            
            if not transformed_data:
                return ["No data to load"]
            
            # Create DataFrame and load to Databricks
            df = pd.DataFrame(transformed_data)
            
            conn = self._get_databricks_connection()
            cursor = conn.cursor()
            
            # Simple INSERT (for small datasets)
            full_table_name = f"{self.config['databricks']['catalog']}.{self.config['databricks']['schema']}.{target_table}"
            
            for _, row in df.iterrows():
                columns = ', '.join(row.index)
                values = ', '.join([f"'{v}'" if isinstance(v, str) else str(v) for v in row.values])
                insert_sql = f"INSERT INTO {full_table_name} ({columns}) VALUES ({values})"
                cursor.execute(insert_sql)
            
            conn.close()
            
            return [f"Loaded {len(transformed_data)} rows into {target_table}"]
            
        except Exception as e:
            return [f"Error loading data: {str(e)}"]
    
    async def _get_mapping(self, table_name: str) -> List[str]:
        """Get column mapping for a table"""
        table_config = self.mapping['tables'].get(table_name)
        if table_config:
            return [json.dumps(table_config, indent=2)]
        else:
            return [f"No mapping found for table: {table_name}"]
    
    async def run(self):
        """Run the MCP server"""
        import mcp.server.stdio
        await mcp.server.stdio.stdio_server(self.server)

if __name__ == "__main__":
    server = DataMigrationServer()
    asyncio.run(server.run())