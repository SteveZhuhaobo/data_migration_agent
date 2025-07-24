import asyncio
import json
import yaml
from typing import List, Dict
from openai import AzureOpenAI
from mcp_client.client import DataMigrationClient

class DataMigrationAgent:
    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize Azure OpenAI client
        self.openai_client = AzureOpenAI(
            azure_endpoint=self.config['azure_openai']['endpoint'],
            api_key=self.config['azure_openai']['api_key'],
            api_version=self.config['azure_openai']['api_version']
        )
        
        self.mcp_client = DataMigrationClient()
        
    async def initialize(self):
        """Initialize the agent by connecting to MCP server"""
        try:
            # If connect returns a context manager, use it properly
            result = self.mcp_client.connect(["python", "mcp_server/server.py"])
            
            # Check if result is a coroutine or context manager
            if hasattr(result, '__aenter__'):
                # It's an async context manager
                self.connection_context = result
                await self.connection_context.__aenter__()
            else:
                # It's a regular coroutine
                await result
                
        except Exception as e:
            print(f"Error in initialize: {e}")
            raise
    
    async def close(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'connection_context'):
                await self.connection_context.__aexit__(None, None, None)
            else:
                await self.mcp_client.close()
        except Exception as e:
            print(f"Error in close: {e}")
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the AI agent"""
        return """
        You are a data migration assistant that helps migrate data from SQL Server to Databricks.
        
        You have access to the following tools through MCP:
        - get_sql_schema: Get schema information from SQL Server table
        - extract_data: Extract data from SQL Server table
        - create_databricks_table: Create table in Databricks
        - load_data: Load transformed data into Databricks
        - get_mapping: Get column mapping for a table
        
        Your role is to:
        1. Analyze the source table structure
        2. Create appropriate target tables in Databricks
        3. Extract and transform data according to mappings
        4. Load data into Databricks
        
        Always provide step-by-step explanations of what you're doing.
        """
    
    async def chat_with_ai(self, messages: List[Dict]) -> str:
        """Chat with Azure OpenAI"""
        try:
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=self.config['azure_openai']['deployment_name'],
                messages=messages,
                temperature=0.1,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error calling Azure OpenAI: {str(e)}"
    
    async def _safe_mcp_call(self, method_name: str, *args, **kwargs):
        """Safely call MCP client methods, handling both regular coroutines and context managers"""
        try:
            method = getattr(self.mcp_client, method_name)
            result = method(*args, **kwargs)
            
            # Check if it's an async context manager
            if hasattr(result, '__aenter__'):
                async with result as context_result:
                    return context_result
            else:
                # Regular coroutine
                return await result
                
        except Exception as e:
            print(f"Error in {method_name}: {e}")
            raise
    
    async def migrate_table(self, table_name: str) -> Dict:
        """Migrate a single table from SQL Server to Databricks"""
        results = {"steps": [], "status": "started"}
        
        try:
            # Step 1: Get table mapping
            results["steps"].append("Getting table mapping...")
            mapping = await self._safe_mcp_call('get_mapping', table_name)
            if not mapping:
                results["status"] = "error"
                results["error"] = f"No mapping found for table {table_name}"
                return results
            
            # Step 2: Get source schema
            results["steps"].append("Getting source schema...")
            source_table = mapping.get('source_table', table_name)
            schema = await self._safe_mcp_call('get_sql_schema', source_table)
            results["source_schema"] = schema
            
            # Step 3: Create target table
            results["steps"].append("Creating target table...")
            create_result = await self._safe_mcp_call('create_databricks_table', table_name, schema)
            results["create_table_result"] = create_result
            
            # Step 4: Extract data
            results["steps"].append("Extracting data...")
            data = await self._safe_mcp_call('extract_data', source_table, limit=1000)
            results["extracted_rows"] = len(data) if data else 0
            
            # Step 5: Load data
            results["steps"].append("Loading data...")
            load_result = await self._safe_mcp_call('load_data', table_name, data)
            results["load_result"] = load_result
            
            results["status"] = "completed"
            
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            import traceback
            traceback.print_exc()  # Add detailed error info
        
        return results
    
    async def chat_interface(self):
        """Interactive chat interface for the agent"""
        print("Data Migration Agent initialized. Type 'quit' to exit.")
        print("Available commands:")
        print("- migrate <table_name>: Migrate a specific table")
        print("- schema <table_name>: Get schema for a table")
        print("- mapping <table_name>: Get mapping for a table")
        print("- Or ask any question about data migration")
        print()
        
        conversation = [{"role": "system", "content": self._get_system_prompt()}]
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() == 'quit':
                break
            
            try:
                # Handle specific commands
                if user_input.startswith('migrate '):
                    table_name = user_input.split(' ', 1)[1]
                    print(f"Starting migration for table: {table_name}")
                    result = await self.migrate_table(table_name)
                    print(f"Migration result: {json.dumps(result, indent=2)}")
                    continue
                
                elif user_input.startswith('schema '):
                    table_name = user_input.split(' ', 1)[1]
                    schema = await self._safe_mcp_call('get_sql_schema', table_name)
                    print(f"Schema for {table_name}:")
                    print(json.dumps(schema, indent=2))
                    continue
                
                elif user_input.startswith('mapping '):
                    table_name = user_input.split(' ', 1)[1]
                    mapping = await self._safe_mcp_call('get_mapping', table_name)
                    print(f"Mapping for {table_name}:")
                    print(json.dumps(mapping, indent=2))
                    continue
                
                # General AI conversation
                conversation.append({"role": "user", "content": user_input})
                
                ai_response = await self.chat_with_ai(conversation)
                print(f"Agent: {ai_response}")
                
                conversation.append({"role": "assistant", "content": ai_response})
                
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
    
    async def migrate_all_tables(self) -> Dict:
        """Migrate all tables defined in the mapping"""
        results = {"overall_status": "started", "tables": {}}
        
        try:
            # Get list of tables from mapping
            with open("mappings/column_mapping.json", 'r') as f:
                mapping = json.load(f)
            
            for table_name in mapping['tables'].keys():
                print(f"Migrating table: {table_name}")
                table_result = await self.migrate_table(table_name)
                results["tables"][table_name] = table_result
                
                if table_result["status"] == "error":
                    print(f"Error migrating {table_name}: {table_result.get('error', 'Unknown error')}")
                else:
                    print(f"Successfully migrated {table_name}")
            
            # Check overall status
            failed_tables = [name for name, result in results["tables"].items() if result["status"] == "error"]
            if failed_tables:
                results["overall_status"] = "partial_success"
                results["failed_tables"] = failed_tables
            else:
                results["overall_status"] = "success"
                
        except Exception as e:
            results["overall_status"] = "error"
            results["error"] = str(e)
            import traceback
            traceback.print_exc()
        
        return results