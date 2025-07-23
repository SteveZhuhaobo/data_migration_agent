import asyncio
import sys
import argparse
from agent.migration_agent import DataMigrationAgent

async def main():
    parser = argparse.ArgumentParser(description='Data Migration Agent')
    parser.add_argument('--mode', choices=['chat', 'migrate', 'table'], default='chat',
                       help='Mode: chat (interactive), migrate (all tables), or table (single table)')
    parser.add_argument('--table', help='Table name for single table migration')
    
    args = parser.parse_args()
    
    agent = DataMigrationAgent()
    
    try:
        await agent.initialize()
        print("Data Migration Agent started successfully!")
        
        if args.mode == 'chat':
            await agent.chat_interface()
        
        elif args.mode == 'migrate':
            print("Starting migration of all tables...")
            results = await agent.migrate_all_tables()
            print(f"Migration completed with status: {results['overall_status']}")
            
            if results['overall_status'] == 'partial_success':
                print(f"Failed tables: {results['failed_tables']}")
        
        elif args.mode == 'table':
            if not args.table:
                print("Please specify --table when using table mode")
                return
            
            print(f"Migrating table: {args.table}")
            result = await agent.migrate_table(args.table)
            print(f"Result: {result['status']}")
            
            if result['status'] == 'error':
                print(f"Error: {result['error']}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
    
    finally:
        await agent.close()

if __name__ == "__main__":
    asyncio.run(main())