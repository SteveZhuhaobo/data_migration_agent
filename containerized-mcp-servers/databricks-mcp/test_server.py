#!/usr/bin/env python3
"""
Unit tests for Databricks MCP Server
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import asyncio
import json
import os
import sys

# Add the server directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the databricks connector before importing server
sys.modules['databricks'] = Mock()
sys.modules['databricks.sql'] = Mock()

import server

class TestDatabricksMCPServer(unittest.TestCase):
    """Test cases for Databricks MCP Server"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock environment variables
        self.env_vars = {
            'DATABRICKS_SERVER_HOSTNAME': 'test-workspace.cloud.databricks.com',
            'DATABRICKS_HTTP_PATH': '/sql/1.0/warehouses/test-warehouse-id',
            'DATABRICKS_ACCESS_TOKEN': 'fake-test-token-not-real',
            'DATABRICKS_CATALOG': 'test_catalog',
            'DATABRICKS_SCHEMA': 'test_schema'
        }
        
        # Apply environment variables
        for key, value in self.env_vars.items():
            os.environ[key] = value
    
    def tearDown(self):
        """Clean up test environment"""
        # Remove environment variables
        for key in self.env_vars.keys():
            if key in os.environ:
                del os.environ[key]
        
        # Reset global config
        server.config = None
    
    def test_load_config_from_env_vars(self):
        """Test loading configuration from environment variables"""
        server.load_config()
        
        self.assertIsNotNone(server.config)
        self.assertIn('databricks', server.config)
        
        databricks_config = server.config['databricks']
        self.assertEqual(databricks_config['server_hostname'], 'test-workspace.cloud.databricks.com')
        self.assertEqual(databricks_config['http_path'], '/sql/1.0/warehouses/test-warehouse-id')
        self.assertEqual(databricks_config['access_token'], 'fake-test-token-not-real')
        self.assertEqual(databricks_config['catalog'], 'test_catalog')
        self.assertEqual(databricks_config['schema'], 'test_schema')
    
    def test_load_config_missing_required_fields(self):
        """Test configuration loading with missing required fields"""
        # Remove required environment variable
        del os.environ['DATABRICKS_SERVER_HOSTNAME']
        
        with self.assertRaises(Exception) as context:
            server.load_config()
        
        self.assertIn('Missing required Databricks configuration field: server_hostname', str(context.exception))
    
    def test_load_config_defaults(self):
        """Test configuration loading with default values"""
        # Remove optional environment variables
        del os.environ['DATABRICKS_CATALOG']
        del os.environ['DATABRICKS_SCHEMA']
        
        server.load_config()
        
        databricks_config = server.config['databricks']
        self.assertEqual(databricks_config['catalog'], 'hive_metastore')
        self.assertEqual(databricks_config['schema'], 'default')
    
    def test_validate_connection_success(self):
        """Test successful connection validation"""
        server.load_config()
        
        # Should not raise an exception
        result = server.validate_connection()
        self.assertTrue(result)
    
    def test_validate_connection_invalid_hostname(self):
        """Test connection validation with invalid hostname"""
        server.load_config()
        server.config['databricks']['server_hostname'] = ''
        
        with self.assertRaises(Exception) as context:
            server.validate_connection()
        
        self.assertIn('Invalid server_hostname', str(context.exception))
    
    def test_validate_connection_invalid_http_path(self):
        """Test connection validation with invalid http_path"""
        server.load_config()
        server.config['databricks']['http_path'] = 'invalid-path'
        
        with self.assertRaises(Exception) as context:
            server.validate_connection()
        
        self.assertIn('Invalid http_path', str(context.exception))
    
    def test_validate_connection_invalid_token(self):
        """Test connection validation with invalid access token"""
        server.load_config()
        server.config['databricks']['access_token'] = 'short'
        
        with self.assertRaises(Exception) as context:
            server.validate_connection()
        
        self.assertIn('Invalid access_token', str(context.exception))
    
    @patch('server.sql.connect')
    def test_get_sql_connection_success(self, mock_connect):
        """Test successful SQL connection creation"""
        # Setup
        server.load_config()
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        # Test
        connection = server.get_sql_connection()
        self.assertIsNotNone(connection)
        mock_connect.assert_called_once()
    
    @patch('server.sql.connect')
    def test_get_sql_connection_auth_failure(self, mock_connect):
        """Test SQL connection creation with authentication failure"""
        # Setup
        server.load_config()
        mock_connect.side_effect = Exception("unauthorized")
        
        # Test
        with self.assertRaises(Exception) as context:
            server.get_sql_connection()
        
        self.assertIn('Authentication failed', str(context.exception))
    
    @patch('server.sql.connect')
    def test_get_sql_connection_timeout(self, mock_connect):
        """Test SQL connection creation with timeout"""
        # Setup
        server.load_config()
        mock_connect.side_effect = Exception("timeout")
        
        # Test
        with self.assertRaises(Exception) as context:
            server.get_sql_connection()
        
        self.assertIn('Connection timeout', str(context.exception))
    
    @patch('requests.Session')
    def test_get_rest_client_success(self, mock_session_class):
        """Test successful REST client creation"""
        # Setup
        server.load_config()
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        # Test
        session, base_url = server.get_rest_client()
        
        self.assertIsNotNone(session)
        self.assertEqual(base_url, 'https://test-workspace.cloud.databricks.com')
        mock_session.get.assert_called_once()
    
    @patch('requests.Session')
    def test_get_rest_client_auth_failure(self, mock_session_class):
        """Test REST client creation with authentication failure"""
        # Setup
        server.load_config()
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        # Test
        with self.assertRaises(Exception) as context:
            server.get_rest_client()
        
        self.assertIn('Authentication failed', str(context.exception))
    
    def test_get_full_table_name(self):
        """Test full table name construction"""
        server.load_config()
        
        # Test with provided catalog and schema
        result = server.get_full_table_name('test_table', 'custom_catalog', 'custom_schema')
        self.assertEqual(result, 'custom_catalog.custom_schema.test_table')
        
        # Test with defaults from config
        result = server.get_full_table_name('test_table')
        self.assertEqual(result, 'test_catalog.test_schema.test_table')
        
        # Test with partial overrides
        result = server.get_full_table_name('test_table', catalog='custom_catalog')
        self.assertEqual(result, 'custom_catalog.test_schema.test_table')
    
    @patch('requests.Session')
    def test_check_warehouse_status_running(self, mock_session_class):
        """Test warehouse status check when warehouse is running"""
        # Setup
        server.load_config()
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'state': 'RUNNING'}
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        # Test
        success, message = server.check_warehouse_status()
        
        self.assertTrue(success)
        self.assertEqual(message, 'Warehouse is running')
    
    @patch('requests.Session')
    def test_check_warehouse_status_stopped(self, mock_session_class):
        """Test warehouse status check when warehouse is stopped"""
        # Setup
        server.load_config()
        mock_session = Mock()
        
        # Mock the GET response (warehouse status)
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {'state': 'STOPPED'}
        
        # Mock the POST response (start warehouse)
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        
        mock_session.get.return_value = mock_get_response
        mock_session.post.return_value = mock_post_response
        mock_session_class.return_value = mock_session
        
        # Test
        success, message = server.check_warehouse_status()
        
        self.assertTrue(success)
        self.assertEqual(message, 'Warehouse starting')
        mock_session.post.assert_called_once()

class TestDatabricksTools(unittest.TestCase):
    """Test cases for Databricks MCP tools"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock environment variables
        os.environ.update({
            'DATABRICKS_SERVER_HOSTNAME': 'test-workspace.cloud.databricks.com',
            'DATABRICKS_HTTP_PATH': '/sql/1.0/warehouses/test-warehouse-id',
            'DATABRICKS_ACCESS_TOKEN': 'fake-test-token-not-real',
            'DATABRICKS_CATALOG': 'test_catalog',
            'DATABRICKS_SCHEMA': 'test_schema'
        })
        
        server.load_config()
    
    def tearDown(self):
        """Clean up test environment"""
        # Remove environment variables
        env_vars = ['DATABRICKS_SERVER_HOSTNAME', 'DATABRICKS_HTTP_PATH', 'DATABRICKS_ACCESS_TOKEN',
                   'DATABRICKS_CATALOG', 'DATABRICKS_SCHEMA']
        for key in env_vars:
            if key in os.environ:
                del os.environ[key]
        
        server.config = None
    
    def test_list_tools(self):
        """Test tool listing"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            tools = loop.run_until_complete(server.list_tools())
            
            self.assertIsInstance(tools, list)
            self.assertGreater(len(tools), 0)
            
            # Check for expected tools
            tool_names = [tool.name for tool in tools]
            expected_tools = [
                'execute_query', 'list_catalogs', 'list_schemas', 'list_tables',
                'get_table_schema', 'describe_table', 'create_table', 'insert_data',
                'list_clusters', 'get_cluster_status', 'list_jobs', 'run_job',
                'get_job_run_status', 'check_warehouse_status', 'ping', 'health_check'
            ]
            
            for expected_tool in expected_tools:
                self.assertIn(expected_tool, tool_names)
        finally:
            loop.close()
    
    @patch('server.get_sql_connection')
    @patch('server.check_warehouse_status')
    def test_call_tool_execute_query(self, mock_check_warehouse, mock_get_connection):
        """Test execute_query tool call"""
        # Setup mocks
        mock_check_warehouse.return_value = (True, "Warehouse is running")
        
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [('test_value',)]
        mock_cursor.description = [('test_column',)]
        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection
        
        # Test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                server.call_tool("execute_query", {"query": "SELECT 1"})
            )
            
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            
            # Parse the JSON response
            response_text = result[0].text
            response_data = json.loads(response_text)
            
            self.assertTrue(response_data.get('success'))
            self.assertIn('columns', response_data)
            self.assertIn('data', response_data)
        finally:
            loop.close()
    
    @patch('server.get_sql_connection')
    def test_call_tool_list_catalogs(self, mock_get_connection):
        """Test list_catalogs tool call"""
        # Setup mock connection
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [('catalog1',), ('catalog2',)]
        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection
        
        # Test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                server.call_tool("list_catalogs", {})
            )
            
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            
            # Parse the JSON response
            response_text = result[0].text
            response_data = json.loads(response_text)
            
            self.assertTrue(response_data.get('success'))
            self.assertIn('catalogs', response_data)
            self.assertEqual(len(response_data['catalogs']), 2)
        finally:
            loop.close()
    
    def test_call_tool_unknown_tool(self):
        """Test calling unknown tool"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                server.call_tool("unknown_tool", {})
            )
            
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            self.assertIn("Unknown tool", result[0].text)
        finally:
            loop.close()
    
    @patch('server.get_rest_client')
    def test_call_tool_ping(self, mock_get_rest_client):
        """Test ping tool call"""
        # Setup mock REST client
        mock_session = Mock()
        mock_get_rest_client.return_value = (mock_session, 'https://test.databricks.com')
        
        # Test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                server.call_tool("ping", {})
            )
            
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            
            # Parse the JSON response
            response_text = result[0].text
            response_data = json.loads(response_text)
            
            self.assertTrue(response_data.get('success'))
            self.assertIn('message', response_data)
        finally:
            loop.close()

if __name__ == '__main__':
    unittest.main()