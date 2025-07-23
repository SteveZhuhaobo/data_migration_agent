#!/usr/bin/env python3
"""
Example usage script for the Data Migration Agent
This script demonstrates different ways to use the agent
"""

import asyncio
import json
from agent.migration_agent import DataMigrationAgent

async def example_interactive_session():
    """Example of how to use the agent programmatically"""
    agent = DataMigrationAgent()
    
    try:
        await agent.initialize()
        print("=== Interactive Session Example ===")
        
        # Get schema information
        print("\n1. Getting schema for customers table...")
        schema = await agent.mcp_client.get_sql_schema("dbo.Customers")
        print(f"Schema: {json.dumps(schema, indent=2)}")
        
        # Get mapping information
        print("\n2. Getting mapping for customers table...")
        mapping = await agent.mcp_client.get_mapping("customers")
        print(f"Mapping: {json.dumps(mapping, indent=2)}")
        
        # Extract sample data
        print("\n3. Extracting sample data...")
        data = await agent.mcp_client.extract_data("dbo.Customers", limit=5)
        print(f"Sample data (5 rows): {json.dumps(data, indent=2)}")
        
        # Ask AI for analysis
        print("\n4. Getting AI analysis...")
        messages = [
            {"role": "system", "content": agent._get_system_prompt()},
            {"role": "user", "content": f"Analyze this table schema and suggest the migration approach: {schema}"}
        ]
        ai_response = await agent.chat_with_ai(messages)
        print(f"AI Analysis: {ai_response}")
        
    finally:
        await agent.close()

async def example_single_table_migration():
    """Example of migrating a single table"""
    agent = DataMigrationAgent()
    
    try:
        await agent.initialize()
        print("\n=== Single Table Migration Example ===")
        
        table_name = "customers"  # From your mapping file
        print(f"Migrating table: {table_name}")
        
        result = await agent.migrate_table(table_name)
        
        print(f"\nMigration Result:")
        print(f"Status: {result['status']}")
        print(f"Steps completed: {len(result['steps'])}")
        
        if result['status'] == 'completed':
            print(f"Rows migrated: {result.get('extracted_rows', 'Unknown')}")
            print("Migration successful!")
        else:
            print(f"Migration failed: {result.get('error', 'Unknown error')}")
            
    finally:
        await agent.close()

async def example_ai_guided_migration():
    """Example of using AI to guide the migration process"""
    agent = DataMigrationAgent()
    
    try:
        await agent.initialize()
        print("\n=== AI-Guided Migration Example ===")
        
        # Simulate a conversation with the AI
        conversation = [
            {"role": "system", "content": agent._get_system_prompt()}
        ]
        
        questions = [
            "What tables are available for migration?",
            "What's the best order to migrate the tables?",
            "Are there any potential issues with the customer table migration?",
            "How should I handle data transformations?"
        ]
        
        for question in questions:
            print(f"\nUser: {question}")
            conversation.append({"role": "user", "content": question})
            
            response = await agent.chat_with_ai(conversation)
            print(f"Agent: {response}")
            
            conversation.append({"role": "assistant", "content": response})
            
            # Add a small delay to be respectful to the API
            await asyncio.sleep(1)
            
    finally:
        await agent.close()

async def example_batch_migration_with_validation():
    """Example of batch migration with validation steps"""
    agent = DataMigrationAgent()
    
    try:
        await agent.initialize()
        print("\n=== Batch Migration with Validation Example ===")
        
        # Get list of tables from mapping
        with open("mappings/column_mapping.json", 'r') as f:
            mapping = json.load(f)
        
        tables = list(mapping['tables'].keys())
        print(f"Tables to migrate: {tables}")
        
        migration_plan = []
        
        # Phase 1: Validation
        print("\n--- Phase 1: Validation ---")
        for table in tables:
            print(f"Validating {table}...")
            
            # Check source schema
            source_table = mapping['tables'][table]['source_table']
            schema = await agent.mcp_client.get_sql_schema(source_table)
            
            if not schema:
                print(f"  ❌ Cannot access source table {source_table}")
                continue
            
            # Check mapping configuration
            table_mapping = await agent.mcp_client.get_mapping(table)
            if not table_mapping:
                print(f"  ❌ No mapping configuration for {table}")
                continue
            
            print(f"  ✅ {table} validation passed")
            migration_plan.append(table)
        
        # Phase 2: Migration
        print(f"\n--- Phase 2: Migration ---")
        print(f"Migrating {len(migration_plan)} validated tables...")
        
        results = {"completed": [], "failed": []}
        
        for table in migration_plan:
            print(f"\nMigrating {table}...")
            result = await agent.migrate_table(table)
            
            if result['status'] == 'completed':
                print(f"  ✅ {table} migrated successfully")
                results["completed"].append(table)
            else:
                print(f"  ❌ {table} migration failed: {result.get('error', 'Unknown')}")
                results["failed"].append(table)
        
        # Phase 3: Summary
        print(f"\n--- Migration Summary ---")
        print(f"Successfully migrated: {len(results['completed'])} tables")
        print(f"Failed migrations: {len(results['failed'])} tables")
        
        if results['completed']:
            print(f"Completed: {', '.join(results['completed'])}")
        
        if results['failed']:
            print(f"Failed: {', '.join(results['failed'])}")
            
    finally:
        await agent.close()

async def main():
    """Run all examples"""
    print("Data Migration Agent - Usage Examples")
    print("=====================================")
    
    examples = [
        ("Interactive Session", example_interactive_session),
        ("Single Table Migration", example_single_table_migration),
        ("AI-Guided Migration", example_ai_guided_migration),
        ("Batch Migration with Validation", example_batch_migration_with_validation)
    ]
    
    for name, example_func in examples:
        try:
            print(f"\n{'='*50}")
            print(f"Running: {name}")
            print(f"{'='*50}")
            await example_func()
        except Exception as e:
            print(f"Error in {name}: {str(e)}")
        
        print(f"\n{'-'*50}")
        input("Press Enter to continue to next example...")

if __name__ == "__main__":
    # Run specific example or all examples
    import sys
    
    if len(sys.argv) > 1:
        example_name = sys.argv[1]
        examples = {
            "interactive": example_interactive_session,
            "single": example_single_table_migration,
            "ai": example_ai_guided_migration,
            "batch": example_batch_migration_with_validation
        }
        
        if example_name in examples:
            asyncio.run(examples[example_name]())
        else:
            print(f"Unknown example: {example_name}")
            print(f"Available examples: {', '.join(examples.keys())}")
    else:
        asyncio.run(main())