#!/usr/bin/env python3
"""
SQL Server to Snowflake Migration Tool
Migrates customers and orders tables with metadata columns
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MigrationConfig:
    """Configuration for the migration process"""
    target_database: str = "steve_mcp"
    target_schema: str = "data_migration"
    batch_size: int = 1000
    max_retries: int = 3
    retry_delay: int = 5

@dataclass
class MigrationResult:
    """Result of a table migration"""
    table_name: str
    success: bool
    records_migrated: int = 0
    error_message: str = ""
    start_time: datetime = None
    end_time: datetime = None

@dataclass
class ColumnMapping:
    """Mapping between SQL Server and Snowflake column definitions"""
    sql_server_name: str
    sql_server_type: str
    snowflake_name: str
    snowflake_type: str
    is_nullable: bool
    max_length: Optional[int] = None

class SchemaAnalyzer:
    """Analyzes and maps database schemas"""
    
    # SQL Server to Snowflake data type mapping
    TYPE_MAPPING = {
        'nvarchar': 'VARCHAR',
        'varchar': 'VARCHAR', 
        'int': 'INTEGER',
        'bigint': 'BIGINT',
        'bit': 'BOOLEAN',
        'datetime2': 'TIMESTAMP_NTZ',
        'datetime': 'TIMESTAMP_NTZ',
        'decimal': 'NUMBER',
        'numeric': 'NUMBER',
        'float': 'FLOAT',
        'real': 'REAL',
        'money': 'NUMBER(19,4)',
        'smallmoney': 'NUMBER(10,4)',
        'text': 'TEXT',
        'ntext': 'TEXT'
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def map_sql_server_to_snowflake(self, sql_schema: Dict[str, Any]) -> List[ColumnMapping]:
        """Map SQL Server schema to Snowflake equivalent"""
        mappings = []
        
        for column in sql_schema.get('columns', []):
            sql_type = column['data_type'].lower()
            snowflake_type = self._convert_data_type(sql_type, column)
            
            mapping = ColumnMapping(
                sql_server_name=column['column_name'],
                sql_server_type=column['data_type'],
                snowflake_name=column['column_name'],
                snowflake_type=snowflake_type,
                is_nullable=column['is_nullable'],
                max_length=column.get('max_length')
            )
            mappings.append(mapping)
        
        return mappings
    
    def _convert_data_type(self, sql_type: str, column_info: Dict) -> str:
        """Convert SQL Server data type to Snowflake equivalent"""
        base_type = sql_type.lower()
        
        if base_type in self.TYPE_MAPPING:
            snowflake_type = self.TYPE_MAPPING[base_type]
            
            # Handle types that need length/precision
            if base_type in ['nvarchar', 'varchar']:
                max_length = column_info.get('max_length')
                if max_length and max_length > 0:
                    return f"{snowflake_type}({max_length})"
                else:
                    return snowflake_type
            elif base_type in ['decimal', 'numeric']:
                precision = column_info.get('precision', 18)
                scale = column_info.get('scale', 0)
                return f"{snowflake_type}({precision},{scale})"
            
            return snowflake_type
        else:
            self.logger.warning(f"Unknown data type: {sql_type}, defaulting to VARCHAR")
            return "VARCHAR"
    
    def add_metadata_columns(self, mappings: List[ColumnMapping]) -> List[ColumnMapping]:
        """Add migration metadata columns to the schema"""
        metadata_columns = [
            ColumnMapping(
                sql_server_name="is_migrated",
                sql_server_type="int",
                snowflake_name="is_migrated",
                snowflake_type="INTEGER",
                is_nullable=False
            ),
            ColumnMapping(
                sql_server_name="migrated_at",
                sql_server_type="datetime2",
                snowflake_name="migrated_at", 
                snowflake_type="TIMESTAMP_NTZ",
                is_nullable=False
            )
        ]
        
        return mappings + metadata_columns
    
    def generate_create_table_sql(self, mappings: List[ColumnMapping], table_name: str, 
                                database: str, schema: str) -> str:
        """Generate Snowflake CREATE TABLE SQL statement"""
        column_definitions = []
        
        for mapping in mappings:
            null_constraint = "NOT NULL" if not mapping.is_nullable else "NULL"
            column_def = f"{mapping.snowflake_name} {mapping.snowflake_type} {null_constraint}"
            column_definitions.append(column_def)
        
        full_table_name = f"{database}.{schema}.{table_name}"
        columns_sql = ",\n    ".join(column_definitions)
        
        return f"""CREATE OR REPLACE TABLE {full_table_name} (
    {columns_sql}
)"""

class DatabaseConnection:
    """Base class for database connections"""
    
    def __init__(self, connection_type: str):
        self.connection_type = connection_type
        self.connected = False
    
    async def connect(self) -> bool:
        """Connect to the database"""
        raise NotImplementedError
    
    async def disconnect(self) -> bool:
        """Disconnect from the database"""
        raise NotImplementedError
    
    async def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute a query and return results"""
        raise NotImplementedError
    
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get table schema information"""
        raise NotImplementedError

class DataExtractor:
    """Extracts data from SQL Server using MCP tools"""
    
    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
        self.logger = logging.getLogger(__name__)
    
    async def extract_table_data(self, table_name: str) -> List[Dict[str, Any]]:
        """Extract all data from a SQL Server table"""
        try:
            self.logger.info(f"Extracting data from table: {table_name}")
            
            # This will be replaced with actual MCP calls during execution
            # For now, return empty list as placeholder
            self.logger.info(f"Data extraction for {table_name} - implementation pending")
            return []
                
        except Exception as e:
            self.logger.error(f"Error extracting data from {table_name}: {str(e)}")
            raise
    
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get table schema from SQL Server"""
        try:
            # This will be replaced with actual MCP calls during execution
            # For now, return empty schema as placeholder
            self.logger.info(f"Schema extraction for {table_name} - implementation pending")
            return {"columns": []}
            
        except Exception as e:
            self.logger.error(f"Error getting schema for {table_name}: {str(e)}")
            raise

class SnowflakeTableCreator:
    """Creates tables in Snowflake using MCP tools"""
    
    def __init__(self, database: str, schema: str):
        self.database = database
        self.schema = schema
        self.logger = logging.getLogger(__name__)
    
    async def create_table(self, table_name: str, column_mappings: List[ColumnMapping]) -> bool:
        """Create a table in Snowflake with the specified schema"""
        try:
            self.logger.info(f"Creating table {self.database}.{self.schema}.{table_name}")
            
            # Generate CREATE TABLE SQL
            analyzer = SchemaAnalyzer()
            create_sql = analyzer.generate_create_table_sql(
                column_mappings, table_name, self.database, self.schema
            )
            
            self.logger.info(f"CREATE TABLE SQL: {create_sql}")
            
            # This will be replaced with actual MCP Snowflake call during execution
            self.logger.info(f"Table creation for {table_name} - implementation pending")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating table {table_name}: {str(e)}")
            raise
    
    async def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in Snowflake"""
        try:
            # This will be replaced with actual MCP Snowflake call during execution
            self.logger.info(f"Checking if table {table_name} exists - implementation pending")
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking table existence {table_name}: {str(e)}")
            return False

class DataTransformer:
    """Transforms data for Snowflake loading"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def transform_row(self, row: Dict[str, Any], column_mappings: List[ColumnMapping]) -> Dict[str, Any]:
        """Transform a single row of data"""
        transformed_row = {}
        
        # Copy original columns
        for mapping in column_mappings:
            if mapping.sql_server_name in ["is_migrated", "migrated_at"]:
                continue  # Skip metadata columns, they'll be added separately
            
            original_value = row.get(mapping.sql_server_name)
            transformed_row[mapping.snowflake_name] = self._convert_value(
                original_value, mapping.snowflake_type
            )
        
        # Add metadata columns
        transformed_row["is_migrated"] = 1
        transformed_row["migrated_at"] = datetime.now().isoformat()
        
        return transformed_row
    
    def _convert_value(self, value: Any, target_type: str) -> Any:
        """Convert a value to the target Snowflake type"""
        if value is None:
            return None
        
        # Handle boolean conversion
        if target_type == "BOOLEAN":
            if isinstance(value, bool):
                return value
            elif isinstance(value, int):
                return value == 1
            elif isinstance(value, str):
                return value.lower() in ['true', '1', 'yes']
        
        # Handle timestamp conversion
        if "TIMESTAMP" in target_type:
            if isinstance(value, str):
                return value
            elif hasattr(value, 'isoformat'):
                return value.isoformat()
        
        return value
    
    def batch_transform(self, rows: List[Dict[str, Any]], 
                       column_mappings: List[ColumnMapping]) -> List[Dict[str, Any]]:
        """Transform a batch of rows"""
        return [self.transform_row(row, column_mappings) for row in rows]

class SnowflakeDataLoader:
    """Loads data into Snowflake using MCP tools"""
    
    def __init__(self, database: str, schema: str):
        self.database = database
        self.schema = schema
        self.logger = logging.getLogger(__name__)
    
    async def load_data(self, table_name: str, data: List[Dict[str, Any]]) -> int:
        """Load data into Snowflake table"""
        try:
            if not data:
                self.logger.info(f"No data to load for table {table_name}")
                return 0
            
            self.logger.info(f"Loading {len(data)} records into {table_name}")
            
            # This will be replaced with actual MCP Snowflake call during execution
            self.logger.info(f"Data loading for {table_name} - implementation pending")
            return len(data)
            
        except Exception as e:
            self.logger.error(f"Error loading data into {table_name}: {str(e)}")
            raise

class MigrationEngine:
    """Main migration orchestration engine"""
    
    def __init__(self, config: MigrationConfig):
        self.config = config
        self.sql_connection = None
        self.snowflake_connection = None
        self.migration_results = []
        self.schema_analyzer = SchemaAnalyzer()
        self.data_extractor = DataExtractor(config.batch_size)
        self.table_creator = SnowflakeTableCreator(config.target_database, config.target_schema)
        self.data_transformer = DataTransformer()
        self.data_loader = SnowflakeDataLoader(config.target_database, config.target_schema)
    
    async def initialize_connections(self):
        """Initialize database connections"""
        logger.info("Initializing database connections...")
        # Connections will be initialized in subsequent tasks
        pass
    
    async def migrate_tables(self, table_names: List[str]) -> List[MigrationResult]:
        """Migrate specified tables"""
        logger.info(f"Starting migration of tables: {table_names}")
        results = []
        
        for table_name in table_names:
            logger.info(f"Migrating table: {table_name}")
            result = await self.migrate_table(table_name)
            results.append(result)
            self.migration_results.append(result)
        
        return results
    
    async def migrate_table(self, table_name: str) -> MigrationResult:
        """Migrate a single table"""
        result = MigrationResult(
            table_name=table_name,
            success=False,
            start_time=datetime.now()
        )
        
        try:
            logger.info(f"Starting migration of table: {table_name}")
            
            # Step 1: Get source table schema
            logger.info(f"Step 1: Analyzing schema for {table_name}")
            source_schema = await self.data_extractor.get_table_schema(table_name)
            
            # Step 2: Map schema to Snowflake
            logger.info(f"Step 2: Mapping schema for {table_name}")
            column_mappings = self.schema_analyzer.map_sql_server_to_snowflake(source_schema)
            column_mappings = self.schema_analyzer.add_metadata_columns(column_mappings)
            
            # Step 3: Create target table
            logger.info(f"Step 3: Creating target table for {table_name}")
            await self.table_creator.create_table(table_name, column_mappings)
            
            # Step 4: Extract source data
            logger.info(f"Step 4: Extracting data from {table_name}")
            source_data = await self.data_extractor.extract_table_data(table_name)
            
            # Step 5: Transform data
            logger.info(f"Step 5: Transforming data for {table_name}")
            transformed_data = self.data_transformer.batch_transform(source_data, column_mappings)
            
            # Step 6: Load data to Snowflake
            logger.info(f"Step 6: Loading data to {table_name}")
            records_loaded = await self.data_loader.load_data(table_name, transformed_data)
            
            result.success = True
            result.records_migrated = records_loaded
            logger.info(f"Successfully migrated {records_loaded} records for table {table_name}")
            
        except Exception as e:
            logger.error(f"Error migrating table {table_name}: {str(e)}")
            result.error_message = str(e)
        
        result.end_time = datetime.now()
        return result
    
    def generate_migration_report(self) -> Dict[str, Any]:
        """Generate a comprehensive migration report"""
        total_records = sum(r.records_migrated for r in self.migration_results)
        successful_tables = [r for r in self.migration_results if r.success]
        failed_tables = [r for r in self.migration_results if not r.success]
        
        return {
            "migration_summary": {
                "total_tables": len(self.migration_results),
                "successful_tables": len(successful_tables),
                "failed_tables": len(failed_tables),
                "total_records_migrated": total_records
            },
            "table_results": [
                {
                    "table_name": r.table_name,
                    "success": r.success,
                    "records_migrated": r.records_migrated,
                    "error_message": r.error_message,
                    "duration_seconds": (r.end_time - r.start_time).total_seconds() if r.end_time and r.start_time else 0
                }
                for r in self.migration_results
            ]
        }

async def main():
    """Main migration entry point"""
    logger.info("Starting SQL Server to Snowflake migration")
    
    # Initialize configuration
    config = MigrationConfig()
    
    # Initialize migration engine
    engine = MigrationEngine(config)
    
    try:
        # Initialize connections
        await engine.initialize_connections()
        
        # Define tables to migrate
        tables_to_migrate = ["customers", "orders"]
        
        # Execute migration
        results = await engine.migrate_tables(tables_to_migrate)
        
        # Generate and display report
        report = engine.generate_migration_report()
        logger.info("Migration completed!")
        logger.info(f"Migration Report: {json.dumps(report, indent=2)}")
        
        return report
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())