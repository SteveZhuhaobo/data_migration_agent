#!/usr/bin/env python3
"""
Unit tests for SQL Server MCP Server
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import asyncio
import json
import os
import sys

# Add the server directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock pyodbc before importing server
sys.modules['pyodbc'] = Mock()

import server

class TestSQLServerMCPServer(unittest.TestCase):
    """Test cases for SQL Server MCP Server"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock environment variables
        self.env_vars = {
            'SQLSERVER_SERVER': 'localhost',
            'SQLSERVER_DATABASE': 'test_db',
            'SQLSERVER_USERNAME': 'test_user',
            'SQLSERVER_PASSWORD': 'test_password',
            'SQLSERVER_DRIVER': 'ODBC Driver 17 for SQL Server',
            'SQLSERVER_ENCRYPT': 'yes',
            'SQLSERVER_TRUST_CERTIFICATE': 'yes',
            'SQLSERVER_USE_WINDOWS_AUTH': 'false'
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
        self.assertIn('sql_server', server.config)
        
        sql_config = server.config['sql_server']
        self.assertEqual(sql_config['server'], 'localhost')
        self.assertEqual(sql_config['database'], 'test_db')
        self.assertEqual(sql_config['username'], 'test_user')
        self.assertEqual(sql_config['password'], 'test_password')
        self.assertEqual(sql_config['driver'], 'ODBC Driver 17 for SQL Server')
        self.assertEqual(sql_config['encrypt'], 'yes')
        self.assertEqual(sql_config['trust_server_certificate'], 'yes')
        self.assertFalse(sql_config['use_windows_auth'])
    
    def test_load_config_defaults(self):
        """Test configuration loading with default values"""
        # Remove optional environment variables
        del os.environ['SQLSERVER_DRIVER']
        del os.environ['SQLSERVER_DATABASE']
        del os.environ['SQLSERVER_ENCRYPT']
        del os.environ['SQLSERVER_TRUST_CERTIFICATE']
        del os.environ['SQLSERVER_USE_WINDOWS_AUTH']
        
        server.load_config()
        
        sql_config = server.config['sql_server']
        self.assertEqual(sql_config['driver'], 'ODBC Driver 17 for SQL Server')
        self.assertEqual(sql_config['database'], 'master')
        self.assertEqual(sql_config['encrypt'], 'yes')
        self.assertEqual(sql_config['trust_server_certificate'], 'yes')
        self.assertFalse(sql_config['use_windows_auth'])
    
    def test_load_config_missing_server(self):
        """Test configuration loading with missing server"""
        del os.environ['SQLSERVER_SERVER']
        
        with self.assertRaises(ValueError) as context:
            server.load_config()
        
        self.assertIn('SQLSERVER_SERVER environment variable is required', str(context.exception))
    
    def test_load_config_missing_credentials_sql_auth(self):
        """Test configuration loading with missing credentials for SQL auth"""
        del os.environ['SQLSERVER_USERNAME']
        
        with self.assertRaises(ValueError) as context:
            server.load_config()
        
        self.assertIn('SQLSERVER_USERNAME and SQLSERVER_PASSWORD are required', str(context.exception))
    
    def test_load_config_windows_auth(self):
        """Test configuration loading with Windows authentication"""
        os.environ['SQLSERVER_USE_WINDOWS_AUTH'] = 'true'
        del os.environ['SQLSERVER_USERNAME']
        del os.environ['SQLSERVER_PASSWORD']
        
        server.load_config()
        
        sql_config = server.config['sql_server']
        self.assertTrue(sql_config['use_windows_auth'])
    
    @patch('server.pyodbc.connect')
    def test_get_connection_sql_auth(self, mock_connect):
        """Test database connection with SQL Server authentication"""
        server.load_config()
        mock_connection = Mock()
        mock_connect.return_value = mock_connection
        
        connection = server.get_connection()
        
        self.assertEqual(connection, mock_connection)
        mock_connect.assert_called_once()
        
        # Verify connection string contains SQL auth parameters
        call_args = mock_connect.call_args[0][0]
        self.assertIn('UID=test_user', call_args)
        self.assertIn('PWD=test_password', call_args)
        self.assertNotIn('Trusted_Connection=yes', call_args)
    
    @patch('server.pyodbc.connect')
    def test_get_connection_windows_auth(self, mock_connect):
        """Test database connection with Windows authentication"""
        os.environ['SQLSERVER_USE_WINDOWS_AUTH'] = 'true'
        del os.environ['SQLSERVER_USERNAME']
        del os.environ['SQLSERVER_PASSWORD']
        
        server.load_config()
        mock_connection = Mock()
        mock_connect.return_value = mock_connection
        
        connection = server.get_connection()
        
        self.assertEqual(connection, mock_connection)
        mock_connect.assert_called_once()
        
        # Verify connection string contains Windows auth parameters
        call_args = mock_connect.call_args[0][0]
        self.assertIn('Trusted_Connection=yes', call_args)
        self.assertNotIn('UID=', call_args)
        self.assertNotIn('PWD=', call_args)
    
    @patch('server.pyodbc.connect')
    def test_get_connection_failure(self, mock_connect):
        """Test database connection failure"""
        server.load_config()
        mock_connect.side_effect = Exception("Connection failed")
        
        with self.assertRaises(Exception):
            server.get_connection()

class TestSQLServerTools(unittest.TestCase):
    """Test cases for SQL Server MCP tools"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock environment variables
        os.environ.update({
            'SQLSERVER_SERVER': 'localhost',
            'SQLSERVER_DATABASE': 'test_db',
            'SQLSERVER_USERNAME': 'test_user',
            'SQLSERVER_PASSWORD': 'test_password'
        })
        
        server.load_config()
    
    def tearDown(self):
        """Clean up test environment"""
        # Remove environment variables
        env_vars = ['SQLSERVER_SERVER', 'SQLSERVER_DATABASE', 'SQLSERVER_USERNAME', 'SQLSERVER_PASSWORD']
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
                'execute_query', 'get_table_schema', 'list_tables',
                'create_table', 'insert_data', 'test_connection', 'health_check'
            ]
            
            for expected_tool in expected_tools:
                self.assertIn(expected_tool, tool_names)
        finally:
            loop.close()
    
    @patch('server.get_connection')
    def test_call_tool_execute_query_select(self, mock_get_connection):
        """Test execute_query tool call with SELECT query"""
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
            self.assertEqual(response_data['row_count'], 1)
        finally:
            loop.close()
    
    @patch('server.get_connection')
    def test_call_tool_execute_query_insert(self, mock_get_connection):
        """Test execute_query tool call with INSERT query"""
        # Setup mock connection
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 1
        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection
        
        # Test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                server.call_tool("execute_query", {"query": "INSERT INTO test VALUES (1)"})
            )
            
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            
            # Parse the JSON response
            response_text = result[0].text
            response_data = json.loads(response_text)
            
            self.assertTrue(response_data.get('success'))
            self.assertIn('message', response_data)
            mock_connection.commit.assert_called_once()
        finally:
            loop.close()
    
    @patch('server.get_connection')
    def test_call_tool_list_tables(self, mock_get_connection):
        """Test list_tables tool call"""
        # Setup mock connection
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = ('test_db',)
        mock_cursor.fetchall.return_value = [
            ('dbo', 'table1', 'BASE TABLE'),
            ('dbo', 'table2', 'BASE TABLE')
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection
        
        # Test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                server.call_tool("list_tables", {})
            )
            
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            
            # Parse the JSON response
            response_text = result[0].text
            response_data = json.loads(response_text)
            
            self.assertTrue(response_data.get('success'))
            self.assertIn('tables', response_data)
            self.assertEqual(len(response_data['tables']), 2)
            self.assertEqual(response_data['current_database'], 'test_db')
        finally:
            loop.close()
    
    @patch('server.get_connection')
    def test_call_tool_get_table_schema(self, mock_get_connection):
        """Test get_table_schema tool call"""
        # Setup mock connection
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('id', 'int', 'NO', None, None, 10, 0),
            ('name', 'varchar', 'YES', None, 50, None, None)
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection
        
        # Test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                server.call_tool("get_table_schema", {"table_name": "test_table"})
            )
            
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            
            # Parse the JSON response
            response_text = result[0].text
            response_data = json.loads(response_text)
            
            self.assertEqual(response_data['table_name'], 'test_table')
            self.assertIn('columns', response_data)
            self.assertEqual(len(response_data['columns']), 2)
            
            # Check column details
            columns = response_data['columns']
            self.assertEqual(columns[0]['column_name'], 'id')
            self.assertEqual(columns[0]['data_type'], 'int')
            self.assertFalse(columns[0]['is_nullable'])
        finally:
            loop.close()
    
    @patch('server.get_connection')
    def test_call_tool_create_table(self, mock_get_connection):
        """Test create_table tool call"""
        # Setup mock connection
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection
        
        # Test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                server.call_tool("create_table", {
                    "table_name": "test_table",
                    "columns": ["id INT PRIMARY KEY", "name VARCHAR(50)"]
                })
            )
            
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            
            # Parse the JSON response
            response_text = result[0].text
            response_data = json.loads(response_text)
            
            self.assertTrue(response_data.get('success'))
            self.assertIn('message', response_data)
            self.assertIn('sql', response_data)
            mock_connection.commit.assert_called_once()
        finally:
            loop.close()
    
    @patch('server.get_connection')
    def test_call_tool_insert_data(self, mock_get_connection):
        """Test insert_data tool call"""
        # Setup mock connection
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection
        
        # Test data
        test_data = [
            {"id": 1, "name": "John"},
            {"id": 2, "name": "Jane"}
        ]
        
        # Test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                server.call_tool("insert_data", {
                    "table_name": "test_table",
                    "data": test_data
                })
            )
            
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            
            # Parse the JSON response
            response_text = result[0].text
            response_data = json.loads(response_text)
            
            self.assertTrue(response_data.get('success'))
            self.assertEqual(response_data['rows_inserted'], 2)
            mock_connection.commit.assert_called_once()
            
            # Verify cursor.execute was called for each row
            self.assertEqual(mock_cursor.execute.call_count, 2)
        finally:
            loop.close()
    
    @patch('server.get_connection')
    def test_call_tool_test_connection(self, mock_get_connection):
        """Test test_connection tool call"""
        # Setup mock connection
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = ('test_db', 'test_user', 'Microsoft SQL Server 2019')
        mock_cursor.fetchall.return_value = [('dbo',), ('guest',)]
        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection
        
        # Test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                server.call_tool("test_connection", {})
            )
            
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            
            # Parse the JSON response
            response_text = result[0].text
            response_data = json.loads(response_text)
            
            self.assertTrue(response_data.get('success'))
            self.assertEqual(response_data['current_database'], 'test_db')
            self.assertEqual(response_data['database_user'], 'test_user')
            self.assertIn('available_schemas', response_data)
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