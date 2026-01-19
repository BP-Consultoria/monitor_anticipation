import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import pyodbc
import database.connection

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestDatabaseConnection:
    @patch('database.connection.pyodbc.connect')
    def test_get_connection_success(self, mock_connect):
        
        # Mocka as variáveis do módulo diretamente
        database.connection.DB_ADRESS = 'test_server'
        database.connection.DB_USER = 'test_user'
        database.connection.DB_PASSWORD = 'test_password'
        database.connection.DB_NAME_SERVER_NAME = 'test_database'
        database.connection.DB_DRIVER = 'ODBC Driver 17 for SQL Server'
        
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection
        
        conn = database.connection.get_connection()
        
        assert conn is not None
        mock_connect.assert_called_once()
        call_args = mock_connect.call_args[0][0]
        assert 'DRIVER={ODBC Driver 17 for SQL Server}' in call_args
        assert 'SERVER=test_server' in call_args
        assert 'DATABASE=test_database' in call_args
        assert 'UID=test_user' in call_args
        assert 'PWD=test_password' in call_args
        assert 'TrustServerCertificate=no' in call_args
    
    @patch('database.connection.pyodbc.connect')
    def test_get_connection_with_different_driver(self, mock_connect):
        
        database.connection.DB_ADRESS = 'localhost'
        database.connection.DB_USER = 'admin'
        database.connection.DB_PASSWORD = 'secret123'
        database.connection.DB_NAME_SERVER_NAME = 'mydb'
        database.connection.DB_DRIVER = 'ODBC Driver 18 for SQL Server'
        
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection
        
        conn = database.connection.get_connection()
        
        assert conn is not None
        call_args = mock_connect.call_args[0][0]
        assert 'DRIVER={ODBC Driver 18 for SQL Server}' in call_args
        assert 'SERVER=localhost' in call_args
        assert 'DATABASE=mydb' in call_args
    
    @patch('database.connection.pyodbc.connect')
    def test_get_connection_missing_env_variables(self, mock_connect):
        import database.connection
        
        database.connection.DB_ADRESS = None
        database.connection.DB_USER = None
        database.connection.DB_PASSWORD = None
        database.connection.DB_NAME_SERVER_NAME = None
        database.connection.DB_DRIVER = None
        
        mock_connect.side_effect = pyodbc.Error("Connection string is invalid")
        
        with pytest.raises(pyodbc.Error):
            database.connection.get_connection()
    
    @patch('database.connection.pyodbc.connect')
    def test_get_connection_connection_error(self, mock_connect):
        database.connection.DB_ADRESS = 'invalid_server'
        database.connection.DB_USER = 'user'
        database.connection.DB_PASSWORD = 'pass'
        database.connection.DB_NAME_SERVER_NAME = 'db'
        database.connection.DB_DRIVER = 'ODBC Driver 17 for SQL Server'
        
        mock_connect.side_effect = pyodbc.OperationalError("Connection failed")
        
        with pytest.raises(pyodbc.OperationalError):
            database.connection.get_connection()
    
    @patch('database.connection.pyodbc.connect')
    def test_connection_string_format(self, mock_connect):
        database.connection.DB_ADRESS = 'test_server'
        database.connection.DB_USER = 'test_user'
        database.connection.DB_PASSWORD = 'test_password'
        database.connection.DB_NAME_SERVER_NAME = 'test_database'
        database.connection.DB_DRIVER = 'ODBC Driver 17 for SQL Server'
        
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection
        
        database.connection.get_connection()
        
        call_args = mock_connect.call_args[0][0]
        
        assert call_args.startswith('DRIVER=')
        assert 'SERVER=' in call_args
        assert 'DATABASE=' in call_args
        assert 'UID=' in call_args
        assert 'PWD=' in call_args
        assert call_args.endswith('TrustServerCertificate=no;')
        
        assert 'test_server' in call_args
        assert 'test_user' in call_args
        assert 'test_password' in call_args
        assert 'test_database' in call_args

