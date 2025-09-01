#!/usr/bin/env python3
"""
Integration tests for Databricks MCP Server container
"""

import unittest
import subprocess
import time
import json
import os
import tempfile
import docker
from typing import Optional

class TestDatabricksIntegration(unittest.TestCase):
    """Integration tests for Databricks MCP Server container"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.docker_client = docker.from_env()
        cls.container_name = "databricks-mcp-test"
        cls.image_name = "databricks-mcp:test"
        cls.container = None
        
        # Test environment variables
        cls.test_env = {
            'DATABRICKS_SERVER_HOSTNAME': 'test-workspace.cloud.databricks.com',
            'DATABRICKS_HTTP_PATH': '/sql/1.0/warehouses/test-warehouse-id',
            'DATABRICKS_ACCESS_TOKEN': 'fake-test-token-not-real',
            'DATABRICKS_CATALOG': 'test_catalog',
            'DATABRICKS_SCHEMA': 'test_schema'
        }
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        if cls.container:
            try:
                cls.container.stop()
                cls.container.remove()
            except:
                pass
    
    def test_container_build(self):
        """Test that the container builds successfully"""
        try:
            # Build the container
            image, build_logs = self.docker_client.images.build(
                path=".",
                tag=self.image_name,
                rm=True
            )
            
            self.assertIsNotNone(image)
            self.assertEqual(image.tags[0], f"{self.image_name}:latest")
            
        except docker.errors.BuildError as e:
            self.fail(f"Container build failed: {e}")
    
    def test_container_startup_with_valid_config(self):
        """Test container startup with valid configuration"""
        try:
            # Start container with test environment
            self.container = self.docker_client.containers.run(
                self.image_name,
                environment=self.test_env,
                detach=True,
                name=self.container_name,
                remove=True
            )
            
            # Wait for container to start
            time.sleep(5)
            
            # Check container status
            self.container.reload()
            self.assertEqual(self.container.status, 'running')
            
        except docker.errors.ContainerError as e:
            self.fail(f"Container startup failed: {e}")
    
    def test_container_startup_with_missing_config(self):
        """Test container startup with missing configuration"""
        try:
            # Start container without required environment variables
            container = self.docker_client.containers.run(
                self.image_name,
                detach=True,
                remove=True
            )
            
            # Wait for container to process
            time.sleep(3)
            
            # Container should exit due to missing config
            container.reload()
            self.assertIn(container.status, ['exited', 'dead'])
            
            # Check logs for error message
            logs = container.logs().decode('utf-8')
            self.assertIn('Environment validation failed', logs)
            
            container.remove()
            
        except docker.errors.ContainerError:
            # Expected behavior - container should fail to start
            pass
    
    def test_container_health_check(self):
        """Test container health check functionality"""
        if not self.container:
            self.test_container_startup_with_valid_config()
        
        # Wait for health check to stabilize
        time.sleep(10)
        
        # Check health status
        self.container.reload()
        health_status = self.container.attrs.get('State', {}).get('Health', {}).get('Status')
        
        # Health check should pass even with mock credentials (server starts successfully)
        self.assertIn(health_status, ['healthy', 'starting'])
    
    def test_environment_variable_validation(self):
        """Test environment variable validation"""
        # Test with invalid hostname (empty)
        invalid_env = self.test_env.copy()
        invalid_env['DATABRICKS_SERVER_HOSTNAME'] = ''
        
        try:
            container = self.docker_client.containers.run(
                self.image_name,
                environment=invalid_env,
                detach=True,
                remove=True
            )
            
            time.sleep(3)
            container.reload()
            
            # Container should exit
            self.assertIn(container.status, ['exited', 'dead'])
            
            # Check logs for validation error
            logs = container.logs().decode('utf-8')
            self.assertIn('Missing required Databricks configuration', logs)
            
            container.remove()
            
        except docker.errors.ContainerError:
            # Expected behavior
            pass
    
    def test_container_logs_structure(self):
        """Test that container produces structured logs"""
        if not self.container:
            self.test_container_startup_with_valid_config()
        
        # Get container logs
        logs = self.container.logs().decode('utf-8')
        
        # Check for expected log messages
        self.assertIn('Validating environment configuration', logs)
        self.assertIn('Configuration loaded successfully', logs)
        self.assertIn('Starting Databricks MCP Server', logs)
    
    def test_container_resource_usage(self):
        """Test container resource usage is reasonable"""
        if not self.container:
            self.test_container_startup_with_valid_config()
        
        # Get container stats
        stats = self.container.stats(stream=False)
        
        # Check memory usage (should be reasonable for a Python app)
        memory_usage = stats['memory_stats']['usage']
        memory_limit = stats['memory_stats']['limit']
        memory_percent = (memory_usage / memory_limit) * 100
        
        # Memory usage should be less than 50% of available memory
        self.assertLess(memory_percent, 50.0)
    
    def test_container_file_permissions(self):
        """Test that container runs with proper file permissions"""
        if not self.container:
            self.test_container_startup_with_valid_config()
        
        # Check that container runs as non-root user
        exec_result = self.container.exec_run("whoami")
        username = exec_result.output.decode('utf-8').strip()
        
        self.assertEqual(username, 'mcpuser')
    
    def test_container_network_isolation(self):
        """Test that container doesn't expose unnecessary ports"""
        if not self.container:
            self.test_container_startup_with_valid_config()
        
        # Check that no ports are exposed (MCP uses stdio)
        self.container.reload()
        ports = self.container.attrs.get('NetworkSettings', {}).get('Ports', {})
        
        # Should have no exposed ports for MCP stdio communication
        self.assertEqual(len(ports), 0)
    
    def test_warehouse_path_validation(self):
        """Test that warehouse HTTP path is validated correctly"""
        # Test with invalid HTTP path format
        invalid_env = self.test_env.copy()
        invalid_env['DATABRICKS_HTTP_PATH'] = 'invalid-path-format'
        
        try:
            container = self.docker_client.containers.run(
                self.image_name,
                environment=invalid_env,
                detach=True,
                remove=True,
                command=["python", "-c", "import server; server.load_config(); server.validate_connection()"]
            )
            
            time.sleep(3)
            result = container.wait()
            logs = container.logs().decode('utf-8')
            
            # Should fail validation
            self.assertNotEqual(result['StatusCode'], 0)
            self.assertIn('Invalid http_path', logs)
            
        except docker.errors.ContainerError:
            # Expected behavior
            pass

class TestDatabricksMockIntegration(unittest.TestCase):
    """Integration tests with mock database connections"""
    
    def setUp(self):
        """Set up mock test environment"""
        self.docker_client = docker.from_env()
        self.image_name = "databricks-mcp:test"
        
        # Mock environment that won't actually connect to Databricks
        self.mock_env = {
            'DATABRICKS_SERVER_HOSTNAME': 'mock-workspace.cloud.databricks.com',
            'DATABRICKS_HTTP_PATH': '/sql/1.0/warehouses/mock-warehouse-id',
            'DATABRICKS_ACCESS_TOKEN': 'dapi_mock_token_1234567890abcdef',
            'DATABRICKS_CATALOG': 'mock_catalog',
            'DATABRICKS_SCHEMA': 'mock_schema'
        }
    
    def test_container_startup_validation_only(self):
        """Test that container starts and validates configuration without connecting"""
        try:
            container = self.docker_client.containers.run(
                self.image_name,
                environment=self.mock_env,
                detach=True,
                remove=True,
                command=["python", "-c", "import server; server.load_config(); print('Config validation passed')"]
            )
            
            # Wait for command to complete
            time.sleep(5)
            
            # Get exit code and logs
            result = container.wait()
            logs = container.logs().decode('utf-8')
            
            # Should exit successfully after config validation
            self.assertEqual(result['StatusCode'], 0)
            self.assertIn('Config validation passed', logs)
            
        except docker.errors.ContainerError as e:
            self.fail(f"Container validation test failed: {e}")
    
    def test_server_module_import(self):
        """Test that server module imports correctly in container"""
        try:
            container = self.docker_client.containers.run(
                self.image_name,
                environment=self.mock_env,
                detach=True,
                remove=True,
                command=["python", "-c", "import server; import env_validator; import health_check; print('All modules imported successfully')"]
            )
            
            time.sleep(3)
            
            result = container.wait()
            logs = container.logs().decode('utf-8')
            
            self.assertEqual(result['StatusCode'], 0)
            self.assertIn('All modules imported successfully', logs)
            
        except docker.errors.ContainerError as e:
            self.fail(f"Module import test failed: {e}")
    
    def test_catalog_schema_defaults(self):
        """Test that catalog and schema defaults are applied correctly"""
        # Test without catalog and schema specified
        minimal_env = {
            'DATABRICKS_SERVER_HOSTNAME': 'mock-workspace.cloud.databricks.com',
            'DATABRICKS_HTTP_PATH': '/sql/1.0/warehouses/mock-warehouse-id',
            'DATABRICKS_ACCESS_TOKEN': 'dapi_mock_token_1234567890abcdef'
        }
        
        try:
            container = self.docker_client.containers.run(
                self.image_name,
                environment=minimal_env,
                detach=True,
                remove=True,
                command=["python", "-c", "import server; server.load_config(); print(f'Catalog: {server.config[\"databricks\"][\"catalog\"]}, Schema: {server.config[\"databricks\"][\"schema\"]}')"]
            )
            
            time.sleep(3)
            
            result = container.wait()
            logs = container.logs().decode('utf-8')
            
            self.assertEqual(result['StatusCode'], 0)
            self.assertIn('Catalog: hive_metastore', logs)
            self.assertIn('Schema: default', logs)
            
        except docker.errors.ContainerError as e:
            self.fail(f"Default values test failed: {e}")

if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)