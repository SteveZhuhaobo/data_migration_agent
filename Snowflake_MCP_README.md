# Snowflake MCP Server

A Model Context Protocol (MCP) server that provides integration with Snowflake, enabling programmatic access to Snowflake databases, schemas, tables, and warehouses through standardized MCP tools.

## Features

- **Authentication**: Secure authentication using username/password or key pair methods
- **Resource Discovery**: List and explore databases, schemas, tables, and warehouses
- **SQL Execution**: Execute queries against Snowflake with proper result formatting
- **Data Management**: Create tables and insert data into Snowflake resources
- **Schema Operations**: Get detailed table schema and metadata information
- **Warehouse Management**: Start, stop, and monitor Snowflake warehouses
- **Error Handling**: Comprehensive error handling with retry logic and detailed error messages

## Prerequisites

- Python 3.8 or higher
- Snowflake account with appropriate permissions
- Snowflake user credentials or key pair for authentication
- Required Python packages (see snowflake_requirements.txt)

## Installation

1. **Install dependencies**:
   ```bash
   pip install -r snowflake_requirements.txt
   ```

2. **Set up configuration**:
   - Copy `config/snowflake_config.yaml` to `config/config.yaml`
   - Update the configuration with your Snowflake settings

## Configuration

Create a `config/config.yaml` file with the following structure:

### Username/Password Authentication

```yaml
snowflake:
  # Required: Snowflake account identifier
  account: "your-account.snowflakecomputing.com"
  user: "your-username"
  password: "your-password"  # or use SNOWFLAKE_PASSWORD env var
  
  # Optional: Default connection settings
  database: "your-default-database"
  schema: "your-default-schema"
  warehouse: "your-default-warehouse"
  role: "your-default-role"
```

### Key Pair Authentication

```yaml
snowflake:
  account: "your-account.snowflakecomputing.com"
  user: "your-username"
  private_key_path: "/path/to/your/private_key.p8"
  private_key_passphrase: "your-key-passphrase"  # optional
  
  database: "your-default-database"
  schema: "your-default-schema"
  warehouse: "your-default-warehouse"
```

### Environment Variables

For security, you can use environment variables for sensitive information:

```bash
export SNOWFLAKE_PASSWORD="your-password"
```

## Usage

### Running the MCP Server

```bash
python Snowflake_MCP.py
```

### Testing the Server

Run the test script to verify basic functionality:

```bash
python test_snowflake_mcp.py
```

### Available Tools

The server provides the following MCP tools:

#### Resource Discovery
- `list_databases`: List all accessible databases
- `list_schemas`: List schemas in a database
- `list_tables`: List tables in a schema
- `list_warehouses`: List available warehouses with status

#### Query Execution
- `execute_query`: Execute SQL queries against Snowflake
- `get_table_schema`: Get detailed table schema information
- `describe_table`: Get comprehensive table metadata

#### Data Management
- `create_table`: Create new tables in databases
- `insert_data`: Insert data into existing tables

#### Warehouse Management
- `get_warehouse_status`: Get detailed warehouse status information
- `start_warehouse`: Start/resume a warehouse
- `stop_warehouse`: Suspend a warehouse

#### Utility Tools
- `ping`: Test server responsiveness
- `test_connection`: Test Snowflake connectivity and authentication

### Example Tool Usage

#### List Databases
```json
{
  "name": "list_databases",
  "arguments": {}
}
```

#### Execute Query
```json
{
  "name": "execute_query",
  "arguments": {
    "query": "SELECT * FROM my_table LIMIT 10",
    "warehouse": "COMPUTE_WH",
    "database": "MY_DB",
    "schema": "PUBLIC"
  }
}
```

#### Create Table
```json
{
  "name": "create_table",
  "arguments": {
    "table_name": "test_table",
    "columns": ["id NUMBER", "name VARCHAR(100)", "created_date DATE"],
    "database": "MY_DB",
    "schema": "PUBLIC"
  }
}
```

#### Warehouse Management
```json
{
  "name": "start_warehouse",
  "arguments": {
    "warehouse_name": "COMPUTE_WH"
  }
}
```

## Architecture

The server consists of several key components:

- **Authentication Layer**: Handles Snowflake authentication (password or key pair)
- **Connection Manager**: Manages connections with pooling and retry logic
- **SQL Execution Engine**: Handles SQL query execution and result formatting
- **Resource Discovery**: Provides database, schema, and table exploration
- **Warehouse Management**: Controls warehouse lifecycle operations
- **MCP Tools**: Implements the various MCP tools for different operations

## Snowflake-Specific Features

### Data Types
- Full support for Snowflake data types including VARIANT, OBJECT, and ARRAY
- Proper handling of semi-structured data
- Time travel capabilities (can be extended)

### Warehouse Management
- Automatic warehouse startup for queries
- Warehouse status monitoring
- Cost-aware operations with suspend/resume capabilities

### Authentication Methods
- Username/password authentication
- Private key authentication for service accounts
- Support for encrypted private keys

## Error Handling

The server implements comprehensive error handling:

- **Authentication Errors**: Clear messages for credential issues
- **Connection Errors**: Network and timeout error handling with retries
- **Resource Errors**: Detailed information about missing or inaccessible resources
- **Query Errors**: SQL syntax and execution error reporting
- **Warehouse Errors**: Warehouse state and availability issues

## Security Considerations

- Store sensitive credentials in environment variables
- Use least-privilege principle for user permissions
- Support for encrypted private keys
- All communication uses HTTPS
- No sensitive data is logged

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify account, username, and password/private key are correct
   - Check if account URL format is correct (account.region.snowflakecomputing.com)
   - Ensure user has proper permissions

2. **Resource Not Found**
   - Verify database, schema, or table names are correct
   - Check if you have access to the specified resources
   - Ensure resources exist in the specified database/schema

3. **Warehouse Issues**
   - Check if warehouse exists and you have usage permissions
   - Verify warehouse is not suspended (or use start_warehouse tool)
   - Check for sufficient credits in your account

4. **Connection Timeout**
   - Check network connectivity to Snowflake
   - Increase timeout value in configuration
   - Verify Snowflake service availability

### Key Pair Authentication Setup

1. Generate RSA key pair:
   ```bash
   openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
   openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
   ```

2. Add public key to Snowflake user:
   ```sql
   ALTER USER your_username SET RSA_PUBLIC_KEY='MIIBIjANBgkqhkiG9w0B...';
   ```

3. Configure private key path in config.yaml

## Performance Tips

- Use connection pooling for high-frequency operations
- Leverage warehouse auto-suspend to control costs
- Use appropriate warehouse sizes for your workload
- Consider batch operations for data insertion

## Contributing

When contributing to this project:

1. Follow the existing code style and patterns
2. Add appropriate error handling for new features
3. Update documentation for any new tools or configuration options
4. Test thoroughly with real Snowflake resources

## License

This project follows the same license as your other MCP servers.

## Related Projects

- [Databricks MCP Server](./Databricks_MCP.py) - Similar functionality for Databricks
- [Microsoft Fabric MCP Server](./Fabric_MCP.py) - Microsoft Fabric integration
- [SQL Server MCP Server](./SQL_MCP.py) - SQL Server integration