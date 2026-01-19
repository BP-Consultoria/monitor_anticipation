import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import fileserver.connection

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestFileserverConnection:
    @patch('fileserver.connection.subprocess.run')
    @patch('fileserver.connection.is_windows')
    def test_mount_network_windows_success(self, mock_is_windows, mock_subprocess):
        mock_is_windows.return_value = True
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "The command completed successfully."
        mock_subprocess.return_value = mock_result
        
        result = fileserver.connection.mount_network_windows("\\\\192.168.0.71\\dados")
        
        assert result is True
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert "net" in call_args
        assert "use" in call_args
        assert "192.168.0.71" in str(call_args)
    
    @patch('fileserver.connection.subprocess.run')
    @patch('fileserver.connection.is_windows')
    def test_mount_network_windows_with_credentials(self, mock_is_windows, mock_subprocess):
        mock_is_windows.return_value = True
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "The command completed successfully."
        mock_subprocess.return_value = mock_result
        
        result = fileserver.connection.mount_network_windows(
            "\\\\192.168.0.71\\dados",
            username="test_user",
            password="test_pass"
        )
        
        assert result is True
        call_args = mock_subprocess.call_args[0][0]
        assert "/user:test_user" in str(call_args)
    
    @patch('fileserver.connection.subprocess.run')
    @patch('fileserver.connection.is_windows')
    def test_mount_network_windows_already_connected(self, mock_is_windows, mock_subprocess):
        mock_is_windows.return_value = True
        
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "Local name is already connected"
        mock_subprocess.return_value = mock_result
        
        result = fileserver.connection.mount_network_windows("\\\\192.168.0.71\\dados")
        
        assert result is True
    
    @patch('fileserver.connection.subprocess.run')
    @patch('fileserver.connection.os.path.exists')
    @patch('fileserver.connection.os.path.ismount')
    @patch('fileserver.connection.os.getuid')
    @patch('fileserver.connection.os.getgid')
    def test_mount_network_linux_success(self, mock_getgid, mock_getuid, mock_ismount, mock_exists, mock_subprocess):
        mock_exists.return_value = True
        mock_ismount.return_value = False
        mock_getuid.return_value = 1000
        mock_getgid.return_value = 1000
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_result.stdout = ""
        mock_subprocess.return_value = mock_result
        
        result = fileserver.connection.mount_network_linux(
            "//192.168.0.71/dados",
            mount_point="/mnt/network_share"
        )
        
        assert result is True
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert "sudo" in call_args
        assert "mount" in call_args
        assert "cifs" in call_args
        assert "192.168.0.71" in str(call_args)
    
    @patch('fileserver.connection.subprocess.run')
    @patch('fileserver.connection.os.path.exists')
    @patch('fileserver.connection.os.path.ismount')
    def test_mount_network_linux_already_mounted(self, mock_ismount, mock_exists, mock_subprocess):
        mock_exists.return_value = True
        mock_ismount.return_value = True
        
        result = fileserver.connection.mount_network_linux(
            "//192.168.0.71/dados",
            mount_point="/mnt/network_share"
        )
        
        assert result is True
        mock_subprocess.assert_not_called()
    
    @patch('fileserver.connection.mount_network_windows')
    @patch('fileserver.connection.is_linux')
    @patch('fileserver.connection.is_windows')
    def test_mount_network_windows_integration(self, mock_is_windows, mock_is_linux, mock_mount):
        mock_is_windows.return_value = True
        mock_is_linux.return_value = False
        mock_mount.return_value = True
        
        fileserver.connection.NETWORK_PATH = "\\\\192.168.0.71\\dados"
        
        result = fileserver.connection.mount_network()
        
        assert result == "\\\\192.168.0.71\\dados"
        mock_mount.assert_called_once()
    
    @patch('fileserver.connection.mount_network_linux')
    @patch('fileserver.connection.is_linux')
    @patch('fileserver.connection.is_windows')
    def test_mount_network_linux_integration(self, mock_is_windows, mock_is_linux, mock_mount):
        mock_is_windows.return_value = False
        mock_is_linux.return_value = True
        mock_mount.return_value = True
        
        fileserver.connection.NETWORK_PATH = "//192.168.0.71/dados"
        fileserver.connection.NETWORK_MOUNT_POINT = "/mnt/network_share"
        
        result = fileserver.connection.mount_network()
        
        assert result == "/mnt/network_share"
        mock_mount.assert_called_once()
    
    @patch('fileserver.connection.mount_network_windows')
    @patch('fileserver.connection.is_linux')
    @patch('fileserver.connection.is_windows')
    def test_mount_network_windows_failure(self, mock_is_windows, mock_is_linux, mock_mount):
        mock_is_windows.return_value = True
        mock_is_linux.return_value = False
        mock_mount.return_value = False
        
        fileserver.connection.NETWORK_PATH = "\\\\192.168.0.71\\dados"
        
        with pytest.raises(ConnectionError):
            fileserver.connection.mount_network()
    
    @patch('fileserver.connection.is_linux')
    @patch('fileserver.connection.is_windows')
    def test_mount_network_missing_config(self, mock_is_windows, mock_is_linux):
        mock_is_windows.return_value = False
        mock_is_linux.return_value = True
        fileserver.connection.NETWORK_PATH = None
        
        with pytest.raises(ValueError):
            fileserver.connection.mount_network()
    
    @patch('fileserver.connection.is_linux')
    @patch('fileserver.connection.is_windows')
    def test_get_mounted_path_linux_missing_config(self, mock_is_windows, mock_is_linux):
        mock_is_windows.return_value = False
        mock_is_linux.return_value = True
        fileserver.connection.NETWORK_PATH = None
        
        with pytest.raises(ValueError):
            fileserver.connection.get_mounted_path("relative_path.xlsx")
    
    @patch('fileserver.connection.is_linux')
    @patch('fileserver.connection.is_windows')
    def test_get_mounted_path_windows_absolute(self, mock_is_windows, mock_is_linux):
        mock_is_windows.return_value = True
        mock_is_linux.return_value = False
        
        fileserver.connection.NETWORK_PATH = "\\\\192.168.0.71\\dados"
        
        full_path = "\\\\192.168.0.71\\dados\\FINANCEIRO\\FINANCEIRO\\FINANCEIRO 2026\\CONTAS A RECEBER\\FUNDOS DE ANTECIPAÇÃO\\RELAÇÃO PORTAIS.xlsx"
        result = fileserver.connection.get_mounted_path(full_path)
        
        assert result == full_path
    
    @patch('fileserver.connection.is_linux')
    @patch('fileserver.connection.is_windows')
    def test_get_mounted_path_windows_relative(self, mock_is_windows, mock_is_linux):
        mock_is_windows.return_value = True
        mock_is_linux.return_value = False
        
        fileserver.connection.NETWORK_PATH = "\\\\192.168.0.71\\dados"
        file_path = "FINANCEIRO\\FINANCEIRO\\FINANCEIRO 2026\\CONTAS A RECEBER\\FUNDOS DE ANTECIPAÇÃO\\RELAÇÃO PORTAIS.xlsx"
        
        result = fileserver.connection.get_mounted_path(file_path)
        
        expected = "\\\\192.168.0.71\\dados\\FINANCEIRO\\FINANCEIRO\\FINANCEIRO 2026\\CONTAS A RECEBER\\FUNDOS DE ANTECIPAÇÃO\\RELAÇÃO PORTAIS.xlsx"
        assert result == expected
    
    @patch('fileserver.connection.is_linux')
    @patch('fileserver.connection.is_windows')
    def test_get_mounted_path_windows_without_prefix(self, mock_is_windows, mock_is_linux):
        mock_is_windows.return_value = True
        mock_is_linux.return_value = False
        
        fileserver.connection.NETWORK_PATH = "192.168.0.71\\dados"
        file_path = "test.xlsx"
        
        result = fileserver.connection.get_mounted_path(file_path)
        
        assert result.startswith("\\\\")
        assert "192.168.0.71" in result
    
    @patch('fileserver.connection.is_linux')
    @patch('fileserver.connection.is_windows')
    @patch('fileserver.connection.os.path.ismount')
    @patch('fileserver.connection.mount_network')
    def test_get_mounted_path_linux(self, mock_mount, mock_ismount, mock_is_windows, mock_is_linux):
        mock_is_windows.return_value = False
        mock_is_linux.return_value = True
        mock_ismount.return_value = False
        
        fileserver.connection.NETWORK_PATH = "//192.168.0.71/dados"
        fileserver.connection.NETWORK_MOUNT_POINT = "/mnt/network_share"
        
        file_path = "FINANCEIRO/FINANCEIRO/FINANCEIRO 2026/CONTAS A RECEBER/FUNDOS DE ANTECIPAÇÃO/RELAÇÃO PORTAIS.xlsx"
        result = fileserver.connection.get_mounted_path(file_path)
        
        expected = "/mnt/network_share/FINANCEIRO/FINANCEIRO/FINANCEIRO 2026/CONTAS A RECEBER/FUNDOS DE ANTECIPAÇÃO/RELAÇÃO PORTAIS.xlsx"
        assert result == expected
    
    @patch('fileserver.connection.is_linux')
    @patch('fileserver.connection.is_windows')
    def test_get_mounted_path_linux_absolute(self, mock_is_windows, mock_is_linux):
        mock_is_windows.return_value = False
        mock_is_linux.return_value = True
        
        fileserver.connection.NETWORK_PATH = "//192.168.0.71/dados"
        
        full_path = "/mnt/network_share/FINANCEIRO/FINANCEIRO/FINANCEIRO 2026/CONTAS A RECEBER/FUNDOS DE ANTECIPAÇÃO/RELAÇÃO PORTAIS.xlsx"
        result = fileserver.connection.get_mounted_path(full_path)
        
        assert result == full_path
    
    @patch('fileserver.connection.is_linux')
    @patch('fileserver.connection.is_windows')
    @patch('fileserver.connection.subprocess.run')
    @patch('fileserver.connection.os.path.exists')
    @patch('fileserver.connection.os.path.ismount')
    @patch('fileserver.connection.os.getuid')
    @patch('fileserver.connection.os.getgid')
    def test_mount_network_linux_with_credentials(self, mock_getgid, mock_getuid, mock_ismount, mock_exists, mock_subprocess, mock_is_windows, mock_is_linux):
        mock_is_windows.return_value = False
        mock_is_linux.return_value = True
        mock_exists.return_value = True
        mock_ismount.return_value = False
        mock_getuid.return_value = 1000
        mock_getgid.return_value = 1000
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_result.stdout = ""
        mock_subprocess.return_value = mock_result
        
        result = fileserver.connection.mount_network_linux(
            "//192.168.0.71/dados",
            mount_point="/mnt/network_share",
            username="test_user",
            password="test_pass"
        )
        
        assert result is True
        call_args = mock_subprocess.call_args[0][0]
        assert "username=test_user" in str(call_args)
        assert "password=test_pass" in str(call_args)
    
    @patch('fileserver.connection.is_linux')
    @patch('fileserver.connection.is_windows')
    def test_get_mounted_path_windows_missing_config(self, mock_is_windows, mock_is_linux):
        mock_is_windows.return_value = True
        mock_is_linux.return_value = False
        fileserver.connection.NETWORK_PATH = None
        
        with pytest.raises(ValueError):
            fileserver.connection.get_mounted_path("relative_path.xlsx")
    
    @patch('fileserver.connection.is_linux')
    @patch('fileserver.connection.is_windows')
    def test_get_mounted_path_absolute_path_no_config(self, mock_is_windows, mock_is_linux):
        mock_is_windows.return_value = True
        mock_is_linux.return_value = False
        fileserver.connection.NETWORK_PATH = None
        
        full_path = "\\\\192.168.0.71\\dados\\file.xlsx"
        result = fileserver.connection.get_mounted_path(full_path)
        
        assert result == full_path
    
    @patch('fileserver.connection.is_linux')
    @patch('fileserver.connection.is_windows')
    def test_get_mounted_path_real_windows_path(self, mock_is_windows, mock_is_linux):
        mock_is_windows.return_value = True
        mock_is_linux.return_value = False
        
        fileserver.connection.NETWORK_PATH = "\\\\192.168.0.71\\dados"
        file_path = "FINANCEIRO\\FINANCEIRO\\FINANCEIRO 2026\\CONTAS A RECEBER\\FUNDOS DE ANTECIPAÇÃO\\RELAÇÃO PORTAIS.xlsx"
        
        result = fileserver.connection.get_mounted_path(file_path)
        
        expected = "\\\\192.168.0.71\\dados\\FINANCEIRO\\FINANCEIRO\\FINANCEIRO 2026\\CONTAS A RECEBER\\FUNDOS DE ANTECIPAÇÃO\\RELAÇÃO PORTAIS.xlsx"
        assert result == expected
        assert "192.168.0.71" in result
        assert "RELAÇÃO PORTAIS.xlsx" in result
    
    @patch('fileserver.connection.is_linux')
    @patch('fileserver.connection.is_windows')
    def test_get_mounted_path_real_linux_path(self, mock_is_windows, mock_is_linux):
        mock_is_windows.return_value = False
        mock_is_linux.return_value = True
        
        fileserver.connection.NETWORK_PATH = "//192.168.0.71/dados"
        fileserver.connection.NETWORK_MOUNT_POINT = "/mnt/network_share"
        
        file_path = "FINANCEIRO/FINANCEIRO/FINANCEIRO 2026/CONTAS A RECEBER/FUNDOS DE ANTECIPAÇÃO/RELAÇÃO PORTAIS.xlsx"
        result = fileserver.connection.get_mounted_path(file_path)
        
        expected = "/mnt/network_share/FINANCEIRO/FINANCEIRO/FINANCEIRO 2026/CONTAS A RECEBER/FUNDOS DE ANTECIPAÇÃO/RELAÇÃO PORTAIS.xlsx"
        assert result == expected
        assert "192.168.0.71" in fileserver.connection.NETWORK_PATH
        assert "RELAÇÃO PORTAIS.xlsx" in result
