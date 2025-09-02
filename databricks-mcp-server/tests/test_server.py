"""
Unit tests for the Databricks MCP Server core functionality.

Tests the server initialization, lifecycle management, and MCP tool functionality.
"""

import json
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from databricks_mcp_server.server import (
    DatabricksMCPServer, ConnectionManager, QueryExecutor, 
    SchemaManager, TableManager, ClusterManager
)
from databricks_mcp_server.errors import (
    ConfigurationError, ConnectionError, AuthenticationError, 
    WarehouseError, DependencyError
)


class TestConnectionManager:
    """Test cases for ConnectionManager class."""
    
    def test_connection_manager_initialization(self):
        """Test ConnectionManager initialization."""
        config = {
            'server_hostname': 'test.databricks.com',
            'http_path': '/sql/1.0/warehouses/test',
            'access_token': 'test-token'
        }
        manager = ConnectionManager(config)
        assert manager.databricks_config == config
    
    def test_validate_connection_success(self):
        """Test successful connection validation."""
        config = {
            'server_hostname': 'test.databricks.com',
            'http_path': '/sql/1.0/warehouses/test',
            'access_token': 'test-token-1234567890'
        }
        manager = ConnectionManager(config)
        assert manager.validate_connection() is True
    
    def test_validate_connection_missing_hostname(self):
        """Test validation with missing hostname."""
        config = {
            'http_path': '/sql/1.0/warehouses/test',
            'access_token': 'test-token'
        }
        manager = ConnectionManager(config)
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager.validate_connection()
        
        assert "SERVER_HOSTNAME" in str(exc_info.value)
    
    def test_validate_connection_invalid_http_path(self):
        """Test validation with invalid http_path."""
        config = {
            'server_hostname': 'test.databricks.com',
            'http_path': 'invalid-path',  # Should start with /
            'access_token': 'test-token-1234567890'
        }
        manager = ConnectionManager(config)
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager.validate_connection()
        
        assert "http_path" in str(exc_info.value)
    
    def test_validate_connection_short_token(self):
        """Test validation with too short access token."""
        config = {
            'server_hostname': 'test.databricks.com',
            'http_path': '/sql/1.0/warehouses/test',
            'access_token': 'short'  # Too short
        }
        manager = ConnectionManager(config)
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager.validate_connection()
        
        assert "ACCESS_TOKEN" in str(exc_info.value)
    
    @patch('databricks_mcp_server.server.ConnectionManager.validate_connection')
    def test_get_sql_connection_success(self, mock_validate):
        """Test successful SQL connection creation."""
        # Mock validation to pass
        mock_validate.return_value = True
        
        # Mock the databricks sql import and connection
        with patch('builtins.__import__') as mock_import:
            mock_sql_module = Mock()
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.execute.return_value = None
            mock_cursor.fetchone.return_value = (1,)
            mock_cursor.close.return_value = None
            mock_sql_module.connect.return_value = mock_connection
            
            def mock_import_func(name, *args, **kwargs):
                if name == 'databricks':
                    mock_databricks = Mock()
                    mock_databricks.sql = mock_sql_module
                    return mock_databricks
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = mock_import_func
            
            config = {
                'server_hostname': 'test.databricks.com',
                'http_path': '/sql/1.0/warehouses/test',
                'access_token': 'test-token-1234567890'
            }
            manager = ConnectionManager(config)
            
            connection = manager.get_sql_connection()
            
            assert connection == mock_connection
            mock_cursor.execute.assert_called_with("SELECT 1")
    
    @patch('builtins.__import__')
    def test_get_sql_connection_import_error(self, mock_import):
        """Test SQL connection with import error."""
        # Simulate ImportError for databricks module
        def mock_import_func(name, *args, **kwargs):
            if name == 'databricks':
                raise ImportError("No module named 'databricks'")
            return __import__(name, *args, **kwargs)
        
        mock_import.side_effect = mock_import_func
        
        config = {
            'server_hostname': 'test.databricks.com',
            'http_path': '/sql/1.0/warehouses/test',
            'access_token': 'test-token-1234567890'
        }
        manager = ConnectionManager(config)
        
        with pytest.raises(DependencyError) as exc_info:
            manager.get_sql_connection()
        
        assert "databricks-sql-connector" in str(exc_info.value)
    
    @patch('databricks_mcp_server.server.requests.Session')
    def test_get_rest_client_success(self, mock_session_class):
        """Test successful REST client creation."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        config = {
            'server_hostname': 'test.databricks.com',
            'http_path': '/sql/1.0/warehouses/test',
            'access_token': 'test-token-1234567890'
        }
        manager = ConnectionManager(config)
        
        session, base_url = manager.get_rest_client()
        
        assert session == mock_session
        assert base_url == "https://test.databricks.com"
        mock_session.get.assert_called_once()
    
    @patch('databricks_mcp_server.server.requests.Session')
    def test_get_rest_client_auth_error(self, mock_session_class):
        """Test REST client with authentication error."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        config = {
            'server_hostname': 'test.databricks.com',
            'http_path': '/sql/1.0/warehouses/test',
            'access_token': 'invalid-token'
        }
        manager = ConnectionManager(config)
        
        with pytest.raises(AuthenticationError) as exc_info:
            manager.get_rest_client()
        
        assert "Invalid access token" in str(exc_info.value)
    
    def test_check_warehouse_status_success(self):
        """Test successful warehouse status check."""
        config = {
            'server_hostname': 'test.databricks.com',
            'http_path': '/sql/1.0/warehouses/test-warehouse-id',
            'access_token': 'test-token-1234567890'
        }
        manager = ConnectionManager(config)
        
        with patch.object(manager, 'get_rest_client') as mock_get_client:
            mock_session = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'state': 'RUNNING'}
            mock_session.get.return_value = mock_response
            mock_get_client.return_value = (mock_session, 'https://test.databricks.com')
            
            success, message = manager.check_warehouse_status()
            
            assert success is True
            assert "running" in message.lower()


class TestQueryExecutor:
    """Test cases for QueryExecutor class."""
    
    def test_query_executor_initialization(self):
        """Test QueryExecutor initialization."""
        mock_connection_manager = Mock()
        executor = QueryExecutor(mock_connection_manager)
        assert executor.connection_manager == mock_connection_manager
    
    def test_get_full_table_name_with_defaults(self):
        """Test full table name construction with default values."""
        mock_connection_manager = Mock()
        mock_connection_manager.databricks_config = {
            'catalog': 'test_catalog',
            'schema': 'test_schema'
        }
        executor = QueryExecutor(mock_connection_manager)
        
        full_name = executor.get_full_table_name('test_table')
        assert full_name == 'test_catalog.test_schema.test_table'
    
    def test_get_full_table_name_with_overrides(self):
        """Test full table name construction with override values."""
        mock_connection_manager = Mock()
        mock_connection_manager.databricks_config = {
            'catalog': 'default_catalog',
            'schema': 'default_schema'
        }
        executor = QueryExecutor(mock_connection_manager)
        
        full_name = executor.get_full_table_name('test_table', 'custom_catalog', 'custom_schema')
        assert full_name == 'custom_catalog.custom_schema.test_table'
    
    @pytest.mark.asyncio
    async def test_execute_query_select_success(self):
        """Test successful SELECT query execution."""
        mock_connection_manager = Mock()
        mock_connection_manager.check_warehouse_status.return_value = (True, "Warehouse running")
        
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [('value1', 'value2'), ('value3', 'value4')]
        mock_cursor.description = [('col1',), ('col2',)]
        mock_connection.cursor.return_value = mock_cursor
        mock_connection_manager.get_sql_connection.return_value = mock_connection
        
        executor = QueryExecutor(mock_connection_manager)
        
        result = await executor.execute_query("SELECT col1, col2 FROM test_table")
        result_dict = json.loads(result)
        
        assert result_dict['success'] is True
        assert result_dict['columns'] == ['col1', 'col2']
        assert len(result_dict['data']) == 2
        assert result_dict['data'][0] == {'col1': 'value1', 'col2': 'value2'}
        assert result_dict['query_type'] == 'SELECT'
    
    @pytest.mark.asyncio
    async def test_execute_query_insert_success(self):
        """Test successful INSERT query execution."""
        mock_connection_manager = Mock()
        mock_connection_manager.check_warehouse_status.return_value = (True, "Warehouse running")
        
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 5
        mock_connection.cursor.return_value = mock_cursor
        mock_connection_manager.get_sql_connection.return_value = mock_connection
        
        executor = QueryExecutor(mock_connection_manager)
        
        result = await executor.execute_query("INSERT INTO test_table VALUES (1, 'test')")
        result_dict = json.loads(result)
        
        assert result_dict['success'] is True
        assert result_dict['affected_rows'] == 5
        assert result_dict['query_type'] == 'DML/DDL'
    
    @pytest.mark.asyncio
    async def test_execute_query_warehouse_error(self):
        """Test query execution with warehouse error."""
        mock_connection_manager = Mock()
        mock_connection_manager.check_warehouse_status.return_value = (False, "Warehouse stopped")
        
        executor = QueryExecutor(mock_connection_manager)
        
        result = await executor.execute_query("SELECT 1")
        result_dict = json.loads(result)
        
        assert result_dict['error'] is True
        assert result_dict['category'] == 'warehouse'
        assert "Warehouse stopped" in result_dict['message']


class TestSchemaManager:
    """Test cases for SchemaManager class."""
    
    def test_schema_manager_initialization(self):
        """Test SchemaManager initialization."""
        mock_connection_manager = Mock()
        mock_query_executor = Mock()
        manager = SchemaManager(mock_connection_manager, mock_query_executor)
        assert manager.connection_manager == mock_connection_manager
        assert manager.query_executor == mock_query_executor
    
    @pytest.mark.asyncio
    async def test_list_catalogs_success(self):
        """Test successful catalog listing."""
        mock_connection_manager = Mock()
        mock_query_executor = Mock()
        
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [('catalog1',), ('catalog2',)]
        mock_connection.cursor.return_value = mock_cursor
        mock_connection_manager.get_sql_connection.return_value = mock_connection
        
        manager = SchemaManager(mock_connection_manager, mock_query_executor)
        
        result = await manager.list_catalogs()
        result_dict = json.loads(result)
        
        assert result_dict['success'] is True
        assert len(result_dict['catalogs']) == 2
        assert result_dict['catalogs'][0]['catalog_name'] == 'catalog1'
        assert result_dict['count'] == 2
    
    @pytest.mark.asyncio
    async def test_list_schemas_success(self):
        """Test successful schema listing."""
        mock_connection_manager = Mock()
        mock_connection_manager.databricks_config = {'catalog': 'test_catalog'}
        mock_query_executor = Mock()
        
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [('schema1',), ('schema2',)]
        mock_connection.cursor.return_value = mock_cursor
        mock_connection_manager.get_sql_connection.return_value = mock_connection
        
        manager = SchemaManager(mock_connection_manager, mock_query_executor)
        
        result = await manager.list_schemas()
        result_dict = json.loads(result)
        
        assert result_dict['success'] is True
        assert result_dict['catalog'] == 'test_catalog'
        assert len(result_dict['schemas']) == 2
        assert result_dict['schemas'][0]['schema_name'] == 'schema1'
    
    @pytest.mark.asyncio
    async def test_list_tables_success(self):
        """Test successful table listing."""
        mock_connection_manager = Mock()
        mock_connection_manager.databricks_config = {
            'catalog': 'test_catalog',
            'schema': 'test_schema'
        }
        mock_query_executor = Mock()
        
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('test_schema', 'table1', False),
            ('test_schema', 'table2', True)
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_connection_manager.get_sql_connection.return_value = mock_connection
        
        manager = SchemaManager(mock_connection_manager, mock_query_executor)
        
        result = await manager.list_tables()
        result_dict = json.loads(result)
        
        assert result_dict['success'] is True
        assert result_dict['catalog'] == 'test_catalog'
        assert result_dict['schema'] == 'test_schema'
        assert len(result_dict['tables']) == 2
        assert result_dict['tables'][0]['table_name'] == 'table1'
        assert result_dict['tables'][1]['is_temporary'] is True
    
    @pytest.mark.asyncio
    async def test_get_table_schema_success(self):
        """Test successful table schema retrieval."""
        mock_connection_manager = Mock()
        mock_query_executor = Mock()
        mock_query_executor.get_full_table_name.return_value = 'catalog.schema.test_table'
        
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('col1', 'string', 'First column'),
            ('col2', 'int', 'Second column'),
            ('# Detailed Table Information', '', ''),
            ('Location:', '/path/to/table', ''),
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_connection_manager.get_sql_connection.return_value = mock_connection
        
        manager = SchemaManager(mock_connection_manager, mock_query_executor)
        
        result = await manager.get_table_schema('test_table')
        result_dict = json.loads(result)
        
        assert result_dict['success'] is True
        assert result_dict['table_name'] == 'catalog.schema.test_table'
        assert len(result_dict['columns']) == 2
        assert result_dict['columns'][0]['column_name'] == 'col1'
        assert result_dict['columns'][0]['data_type'] == 'string'
        assert 'Location' in result_dict['table_info']


class TestTableManager:
    """Test cases for TableManager class."""
    
    def test_table_manager_initialization(self):
        """Test TableManager initialization."""
        mock_connection_manager = Mock()
        mock_query_executor = Mock()
        manager = TableManager(mock_connection_manager, mock_query_executor)
        assert manager.connection_manager == mock_connection_manager
        assert manager.query_executor == mock_query_executor
    
    @pytest.mark.asyncio
    async def test_create_table_success(self):
        """Test successful table creation."""
        mock_connection_manager = Mock()
        mock_query_executor = Mock()
        mock_query_executor.get_full_table_name.return_value = 'catalog.schema.test_table'
        
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connection_manager.get_sql_connection.return_value = mock_connection
        
        manager = TableManager(mock_connection_manager, mock_query_executor)
        
        columns = ['id INT', 'name STRING', 'created_at TIMESTAMP']
        result = await manager.create_table('test_table', columns)
        result_dict = json.loads(result)
        
        assert result_dict['success'] is True
        assert result_dict['table_name'] == 'catalog.schema.test_table'
        assert 'CREATE TABLE' in result_dict['sql']
        mock_cursor.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_insert_data_success(self):
        """Test successful data insertion."""
        mock_connection_manager = Mock()
        mock_query_executor = Mock()
        mock_query_executor.get_full_table_name.return_value = 'catalog.schema.test_table'
        
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connection_manager.get_sql_connection.return_value = mock_connection
        
        manager = TableManager(mock_connection_manager, mock_query_executor)
        
        data = [
            {'id': 1, 'name': 'Alice'},
            {'id': 2, 'name': 'Bob'}
        ]
        result = await manager.insert_data('test_table', data)
        result_dict = json.loads(result)
        
        assert result_dict['success'] is True
        assert result_dict['rows_inserted'] == 2
        assert result_dict['table_name'] == 'catalog.schema.test_table'
        mock_cursor.executemany.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_insert_data_empty(self):
        """Test data insertion with empty data."""
        mock_connection_manager = Mock()
        mock_query_executor = Mock()
        
        manager = TableManager(mock_connection_manager, mock_query_executor)
        
        result = await manager.insert_data('test_table', [])
        result_dict = json.loads(result)
        
        assert result_dict['success'] is False
        assert 'No data provided' in result_dict['error']


class TestClusterManager:
    """Test cases for ClusterManager class."""
    
    def test_cluster_manager_initialization(self):
        """Test ClusterManager initialization."""
        mock_connection_manager = Mock()
        manager = ClusterManager(mock_connection_manager)
        assert manager.connection_manager == mock_connection_manager
    
    @pytest.mark.asyncio
    async def test_list_clusters_success(self):
        """Test successful cluster listing."""
        mock_connection_manager = Mock()
        
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'clusters': [
                {
                    'cluster_id': 'cluster-1',
                    'cluster_name': 'Test Cluster 1',
                    'state': 'RUNNING',
                    'node_type_id': 'i3.xlarge',
                    'num_workers': 2,
                    'spark_version': '11.3.x-scala2.12',
                    'runtime_engine': 'STANDARD',
                    'creator_user_name': 'test@example.com'
                }
            ]
        }
        mock_session.get.return_value = mock_response
        mock_connection_manager.get_rest_client.return_value = (mock_session, 'https://test.databricks.com')
        
        manager = ClusterManager(mock_connection_manager)
        
        result = await manager.list_clusters()
        result_dict = json.loads(result)
        
        assert result_dict['success'] is True
        assert len(result_dict['clusters']) == 1
        assert result_dict['clusters'][0]['cluster_id'] == 'cluster-1'
        assert result_dict['clusters'][0]['state'] == 'RUNNING'
        assert result_dict['count'] == 1
    
    @pytest.mark.asyncio
    async def test_get_cluster_status_success(self):
        """Test successful cluster status retrieval."""
        mock_connection_manager = Mock()
        
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'cluster_name': 'Test Cluster',
            'state': 'RUNNING',
            'state_message': 'Cluster is running',
            'node_type_id': 'i3.xlarge',
            'num_workers': 2,
            'spark_version': '11.3.x-scala2.12'
        }
        mock_session.get.return_value = mock_response
        mock_connection_manager.get_rest_client.return_value = (mock_session, 'https://test.databricks.com')
        
        manager = ClusterManager(mock_connection_manager)
        
        result = await manager.get_cluster_status('cluster-1')
        result_dict = json.loads(result)
        
        assert result_dict['success'] is True
        assert result_dict['cluster_id'] == 'cluster-1'
        assert result_dict['cluster_info']['state'] == 'RUNNING'


class TestDatabricksMCPServer:
    """Test cases for DatabricksMCPServer class."""
    
    def test_server_initialization(self):
        """Test server initialization with configuration."""
        config = {
            'server_hostname': 'test.databricks.com',
            'http_path': '/sql/1.0/warehouses/test',
            'access_token': 'test-token-1234567890'
        }
        server = DatabricksMCPServer(config)
        assert server.databricks_config == config
        assert server.connection_manager is not None
        assert server.query_executor is not None
        assert server.schema_manager is not None
        assert server.table_manager is not None
        assert server.cluster_manager is not None
    
    def test_server_initialization_complete(self):
        """Test complete server initialization with all components."""
        config = {
            'server_hostname': 'test.databricks.com',
            'http_path': '/sql/1.0/warehouses/test',
            'access_token': 'test-token-1234567890',
            'catalog': 'test_catalog',
            'schema': 'test_schema',
            'timeout': 300
        }
        
        server = DatabricksMCPServer(config)
        
        # Verify all components are initialized
        assert server.databricks_config == config
        assert server.connection_manager is not None
        assert server.query_executor is not None
        assert server.schema_manager is not None
        assert server.table_manager is not None
        assert server.cluster_manager is not None
        assert server.server is not None
        
        # Verify component relationships
        assert server.query_executor.connection_manager == server.connection_manager
        assert server.schema_manager.connection_manager == server.connection_manager
        assert server.schema_manager.query_executor == server.query_executor
        assert server.table_manager.connection_manager == server.connection_manager
        assert server.table_manager.query_executor == server.query_executor
        assert server.cluster_manager.connection_manager == server.connection_manager