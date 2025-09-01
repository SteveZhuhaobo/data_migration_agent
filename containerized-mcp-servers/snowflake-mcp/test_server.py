#!/usr/bin/env python3
"""
Unit tests for Snowflake MCP Server
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import json
import os
import sys
import tempfile

# Add the server directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the snowflake connector before importing server
sys.modules['snowflake.connector'] = Mock()
sys.modules['snowflake.connector.errors'] = Mock()
sys.modules['cryptography.hazmat.primitives'] = Mock()
sys.modules['cryptography.hazmat.primitives.serialization'] = Mock()

import server

class TestSnowflakeMCPServer(unittest.TestCase):
    """Test cases for Snowflake MCP Server"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock environment variables
        self.env_vars = {
            'SNOWFLAKE_ACCOUNT': 'test_account',
            'SNOWFLAKE_USER': 'test_user',
            'SNOWFLAKE_PASSWORD': 'test_password',
            'SNOWFLAKE_DATABASE': 'test_db',
            'SNOWFLAKE_SCHEMA': 'test_schema',
            'SNOWFLAKE_WAREHOUSE': 'test_warehouse',
            'SNOWFLAKE_ROLE': 'test_role'
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
        server.connection_pool = []
    
    def test_load_config_from_env_vars(self):
        """Test loading configuration from environment variables"""
        server.load_config()
        
        self.assertIsNotNone(server.config)
        self.assertIn('snowflake', server.config)
        
        snowflake_config = server.config['snowflake']
        self.assertEqual(snowflake_config['account'], 'test_account')
        self.assertEqual(snowflake_config['user'], 'test_user')
        self.assertEqual(snowflake_config['password'], 'test_password')
        self.assertEqual(snowflake_config['database'], 'test_db')
        self.assertEqual(snowflake_config['schema'], 'test_schema')
        self.assertEqual(snowflake_config['warehouse'], 'test_warehouse')
        self.assertEqual(snowflake_config['role'], 'test_role')
    
    def test_load_config_missing_required_fields(self):
        """Test configuration loading with missing required fields"""
        # Remove required environment variable
        del os.environ['SNOWFLAKE_ACCOUNT']
        
        with self.assertRaises(Exception) as context:
            server.load_config()
        
        self.assertIn('Missing required Snowflake configuration: account', str(context.exception))
    
    def test_load_config_missing_authentication(self):
        """Test configuration loading with missing authentication"""
        # Remove authentication environment variables
        del os.environ['SNOWFLAKE_PASSWORD']
        
        with self.assertRaises(Exception) as context:
            server.load_config()
        
        self.assertIn('Missing authentication method', str(context.exception))
    
    def test_validate_connection_success(self):
        """Test successful connection validation"""
        server.load_config()
        
        # Should not raise an exception
        result = server.validate_connection()
        self.assertTrue(result)
    
    def test_validate_connection_invalid_account(self):
        """Test connection validation with invalid account"""
        server.load_config()
        server.config['snowflake']['account'] = ''
        
        with self.assertRaises(Exception) as context:
            server.validate_connection()
        
        self.assertIn('Invalid account', str(context.exception))
    
    def test_validate_connection_invalid_user(self):
        """Test connection validation with invalid user"""
        server.load_config()
        server.config['snowflake']['user'] = ''
        
        with self.assertRaises(Exception) as context:
            server.validate_connection()
        
        self.assertIn('Invalid user', str(context.exception))
    
    @patch('server.snowflake.connector.connect')
    def test_create_snowflake_connection_success(self, mock_connect):
        """Test successful Snowflake connection creation"""
        # Setup
        server.load_config()
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = ('8.0.0',)
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        # Test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            connection = loop.run_until_complete(server.create_snowflake_connection())
            self.assertIsNotNone(connection)
            mock_connect.assert_called_once()
        finally:
            loop.close()
    
    @patch('server.snowflake.connector.connect')
    def test_create_snowflake_connection_auth_failure(self, mock_connect):
        """Test Snowflake connection creation with authentication failure"""
        # Setup
        server.load_config()
        mock_connect.side_effect = Exception("authentication failed")
        
        # Test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            with self.assertRaises(Exception) as context:
                loop.run_until_complete(server.create_snowflake_connection())
            
            self.assertIn('Failed to connect to Snowflake', str(context.exception))
        finally:
            loop.close()
    
    def test_connection_manager_initialization(self):
        """Test SnowflakeConnectionManager initialization"""
        manager = server.SnowflakeConnectionManager()
        
        self.assertEqual(manager.connections, [])
        self.assertEqual(manager.max_connections, 5)
        self.assertEqual(manager.connection_timeout, 30)
    
    def test_connection_manager_ensure_config(self):
        """Test SnowflakeConnectionManager config update"""
        server.load_config()
        server.config['snowflake']['pool_size'] = 10
        server.config['snowflake']['pool_timeout'] = 60
        
        manager = server.SnowflakeConnectionManager()
        manager._ensure_config()
        
        self.assertEqual(manager.max_connections, 10)
        self.assertEqual(manager.connection_timeout, 60)
    
    def test_sql_executor_initialization(self):
        """Test SnowflakeSQLExecutor initialization"""
        manager = server.SnowflakeConnectionManager()
        executor = server.SnowflakeSQLExecutor(manager)
        
        self.assertEqual(executor.connection_manager, manager)
    
    def test_sql_executor_is_select_query(self):
        """Test SQL query type detection"""
        manager = server.SnowflakeConnectionManager()
        executor = server.SnowflakeSQLExecutor(manager)
        
        # Test SELECT queries
        self.assertTrue(executor._is_select_query("SELECT * FROM table"))
        self.assertTrue(executor._is_select_query("  select col from table  "))
        self.assertTrue(executor._is_select_query("SHOW TABLES"))
        self.assertTrue(executor._is_select_query("DESCRIBE table"))
        self.assertTrue(executor._is_select_query("WITH cte AS (SELECT 1) SELECT * FROM cte"))
        
        # Test non-SELECT queries
        self.assertFalse(executor._is_select_query("INSERT INTO table VALUES (1)"))
        self.assertFalse(executor._is_select_query("UPDATE table SET col = 1"))
        self.assertFalse(executor._is_select_query("DELETE FROM table"))
        self.assertFalse(executor._is_select_query("CREATE TABLE test (id INT)"))
    
    @patch('server.load_private_key')
    def test_load_private_key_success(self, mock_load_key):
        """Test private key loading"""
        # Create a temporary key file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem') as f:
            f.write("-----BEGIN PRIVATE KEY-----\ntest_key_content\n-----END PRIVATE KEY-----")
            key_path = f.name
        
        try:
            # Setup config with private key path
            server.load_config()
            server.config['snowflake']['private_key_path'] = key_path
            del server.config['snowflake']['password']  # Remove password auth
            
            # Mock the cryptography functions
            mock_private_key = Mock()
            mock_private_key.private_bytes.return_value = b'mock_der_key'
            mock_load_key.return_value = mock_private_key
            
            # Test
            with patch('server.load_pem_private_key', return_value=mock_private_key):
                with patch('builtins.open', unittest.mock.mock_open(read_data=b'mock_key_data')):
                    result = server.load_private_key()
                    self.assertEqual(result, mock_private_key)
        
        finally:
            # Clean up
            os.unlink(key_path)
    
    def test_load_private_key_file_not_found(self):
        """Test private key loading with missing file"""
        server.load_config()
        server.config['snowflake']['private_key_path'] = '/nonexistent/key.pem'
        del server.config['snowflake']['password']  # Remove password auth
        
        with self.assertRaises(Exception) as context:
            server.load_private_key()
        
        self.assertIn('Failed to load private key', str(context.exception))

class TestSnowflakeTools(unittest.TestCase):
    """Test cases for Snowflake MCP tools"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock environment variables
        os.environ.update({
            'SNOWFLAKE_ACCOUNT': 'test_account',
            'SNOWFLAKE_USER': 'test_user',
            'SNOWFLAKE_PASSWORD': 'test_password',
            'SNOWFLAKE_DATABASE': 'test_db',
            'SNOWFLAKE_SCHEMA': 'test_schema'
        })
        
        server.load_config()
    
    def tearDown(self):
        """Clean up test environment"""
        # Remove environment variables
        env_vars = ['SNOWFLAKE_ACCOUNT', 'SNOWFLAKE_USER', 'SNOWFLAKE_PASSWORD', 
                   'SNOWFLAKE_DATABASE', 'SNOWFLAKE_SCHEMA']
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
                'execute_query', 'list_databases', 'list_schemas', 'list_tables',
                'get_table_schema', 'describe_table', 'create_table', 'insert_data'
            ]
            
            for expected_tool in expected_tools:
                self.assertIn(expected_tool, tool_names)
        finally:
            loop.close()
    
    @patch('server.get_connection')
    def test_call_tool_execute_query(self, mock_get_connection):
        """Test execute_query tool call"""
        # Setup mock connection
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

if __name__ == '__main__':
    unittest.main()