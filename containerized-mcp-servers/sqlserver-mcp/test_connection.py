#!/usr/bin/env python3
"""
Simple connection test for SQL Server MCP Server
"""

import pyodbc
import os
import sys

def test_connection():
    """Test SQL Server connection with current environment variables"""
    
    # Get environment variables
    server = os.getenv('SQLSERVER_SERVER', 'localhost')
    database = os.getenv('SQLSERVER_DATABASE', 'master')
    username = os.getenv('SQLSERVER_USERNAME', '')
    password = os.getenv('SQLSERVER_PASSWORD', '')
    driver = os.getenv('SQLSERVER_DRIVER', 'ODBC Driver 18 for SQL Server')
    encrypt = os.getenv('SQLSERVER_ENCRYPT', 'yes')
    trust_cert = os.getenv('SQLSERVER_TRUST_CERTIFICATE', 'yes')
    use_windows_auth = os.getenv('SQLSERVER_USE_WINDOWS_AUTH', 'false').lower() == 'true'
    
    print("🔍 SQL Server Connection Test")
    print("=" * 40)
    print(f"Server: {server}")
    print(f"Database: {database}")
    print(f"Driver: {driver}")
    print(f"Encrypt: {encrypt}")
    print(f"Trust Certificate: {trust_cert}")
    
    if use_windows_auth:
        print("Authentication: Windows Authentication")
        conn_str = f"""
        DRIVER={{{driver}}};
        SERVER={server};
        DATABASE={database};
        Trusted_Connection=yes;
        Encrypt={encrypt};
        TrustServerCertificate={trust_cert};
        Connection Timeout=10;
        """
    else:
        print(f"Authentication: SQL Server Authentication (User: {username})")
        conn_str = f"""
        DRIVER={{{driver}}};
        SERVER={server};
        DATABASE={database};
        UID={username};
        PWD={password};
        Encrypt={encrypt};
        TrustServerCertificate={trust_cert};
        Connection Timeout=10;
        """
    
    print("\n🔌 Attempting connection...")
    
    try:
        # Test connection
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Get basic info
        cursor.execute("SELECT @@VERSION, DB_NAME(), USER_NAME()")
        result = cursor.fetchone()
        
        print("✅ Connection successful!")
        print(f"   Database: {result[1]}")
        print(f"   User: {result[2]}")
        print(f"   SQL Server: {result[0].split('-')[0].strip()}")
        
        # Test a simple query
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        table_count = cursor.fetchone()[0]
        print(f"   Tables in database: {table_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Verify SQL Server is running and accessible")
        print("2. Check if SQL Server allows remote connections")
        print("3. Verify username/password are correct")
        print("4. Check if SQL Server Authentication is enabled (mixed mode)")
        print("5. Verify firewall allows connections on SQL Server port (usually 1433)")
        print("6. Try connecting from host machine first using SSMS or sqlcmd")
        
        if "Login failed" in str(e):
            print("   → Authentication issue: Check username/password")
        elif "server was not found" in str(e) or "network-related" in str(e):
            print("   → Network issue: Check server name and network connectivity")
        elif "SSL" in str(e) or "certificate" in str(e):
            print("   → SSL/Certificate issue: Try SQLSERVER_ENCRYPT=no")
        
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)