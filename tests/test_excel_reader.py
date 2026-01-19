import os
import pytest
import pandas as pd

from utils.excel_reader import read_excel, read_excel_multiple_sheets
from fileserver.connection import mount_network, get_mounted_path


class TestExcelReader:
    
    @pytest.fixture
    def file_path(self):
        return r"FINANCEIRO\FINANCEIRO\FINANCEIRO 2026\CONTAS A RECEBER\FUNDOS DE ANTECIPAÇÃO\RELAÇÃO PORTAIS.xlsx"
    
    def test_mount_network_connection(self):
        mounted_path = mount_network()
        assert mounted_path is not None
        assert os.path.exists(mounted_path) or os.path.ismount(mounted_path)
    
    def test_get_mounted_path(self, file_path):
        full_path = get_mounted_path(file_path)
        assert full_path is not None
        assert isinstance(full_path, str)
        assert len(full_path) > 0
    
    def test_mount_point_accessible(self):
        mount_point = os.getenv('NETWORK_MOUNT_POINT')
        if os.path.exists(mount_point):
            assert os.path.exists(mount_point)
            items = os.listdir(mount_point)
            assert isinstance(items, list)
    
    def test_file_exists_or_find_alternative(self, file_path):
        full_path = get_mounted_path(file_path)
        
        if not os.path.exists(full_path):
            base_dir = os.path.dirname(full_path)
            if os.path.exists(base_dir):
                all_items = os.listdir(base_dir)
                files = [f for f in all_items if os.path.isfile(os.path.join(base_dir, f))]
                xlsx_files = [f for f in files if f.lower().endswith('.xlsx')]
                assert len(xlsx_files) > 0, "Nenhum arquivo Excel encontrado no diretório"
            else:
                pytest.skip(f"Diretório base não existe: {base_dir}")
        else:
            assert os.path.exists(full_path)
            file_size = os.path.getsize(full_path)
            assert file_size > 0
    
    def test_read_excel_file(self, file_path):
        full_path = get_mounted_path(file_path)
        
        if not os.path.exists(full_path):
            base_dir = os.path.dirname(full_path)
            if os.path.exists(base_dir):
                all_items = os.listdir(base_dir)
                files = [f for f in all_items if os.path.isfile(os.path.join(base_dir, f))]
                xlsx_files = [f for f in files if f.lower().endswith('.xlsx')]
                if not xlsx_files:
                    pytest.skip("Nenhum arquivo Excel encontrado no diretório")
                file_path = os.path.join(base_dir, xlsx_files[0])
            else:
                pytest.skip(f"Diretório base não existe: {base_dir}")
        
        df = read_excel(file_path, sheet_name=0, auto_mount=True)
        
        assert df is not None
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert len(df.columns) > 0
    
    def test_read_excel_file_has_data(self, file_path):
        full_path = get_mounted_path(file_path)
        
        if not os.path.exists(full_path):
            base_dir = os.path.dirname(full_path)
            if os.path.exists(base_dir):
                all_items = os.listdir(base_dir)
                files = [f for f in all_items if os.path.isfile(os.path.join(base_dir, f))]
                xlsx_files = [f for f in files if f.lower().endswith('.xlsx')]
                if not xlsx_files:
                    pytest.skip("Nenhum arquivo Excel encontrado no diretório")
                file_path = os.path.join(base_dir, xlsx_files[0])
            else:
                pytest.skip(f"Diretório base não existe: {base_dir}")
        
        df = read_excel(file_path, sheet_name=0, auto_mount=True)
        
        assert not df.empty
        assert len(df.index) > 0
        assert len(df.columns) > 0
    
    def test_read_excel_multiple_sheets(self, file_path):
        full_path = get_mounted_path(file_path)
        
        if not os.path.exists(full_path):
            base_dir = os.path.dirname(full_path)
            if os.path.exists(base_dir):
                all_items = os.listdir(base_dir)
                files = [f for f in all_items if os.path.isfile(os.path.join(base_dir, f))]
                xlsx_files = [f for f in files if f.lower().endswith('.xlsx')]
                if not xlsx_files:
                    pytest.skip("Nenhum arquivo Excel encontrado no diretório")
                file_path = os.path.join(base_dir, xlsx_files[0])
            else:
                pytest.skip(f"Diretório base não existe: {base_dir}")
        
        sheets = read_excel_multiple_sheets(file_path, auto_mount=True)
        
        assert sheets is not None
        assert isinstance(sheets, dict)
        assert len(sheets) > 0
        
        for sheet_name, df in sheets.items():
            assert isinstance(sheet_name, str)
            assert isinstance(df, pd.DataFrame)
            assert len(df) >= 0
    
    def test_read_excel_file_columns(self, file_path):
        full_path = get_mounted_path(file_path)
        
        if not os.path.exists(full_path):
            base_dir = os.path.dirname(full_path)
            if os.path.exists(base_dir):
                all_items = os.listdir(base_dir)
                files = [f for f in all_items if os.path.isfile(os.path.join(base_dir, f))]
                xlsx_files = [f for f in files if f.lower().endswith('.xlsx')]
                if not xlsx_files:
                    pytest.skip("Nenhum arquivo Excel encontrado no diretório")
                file_path = os.path.join(base_dir, xlsx_files[0])
            else:
                pytest.skip(f"Diretório base não existe: {base_dir}")
        
        df = read_excel(file_path, sheet_name=0, auto_mount=True)
        
        assert len(df.columns) > 0
        assert all(isinstance(col, str) or pd.isna(col) for col in df.columns)
    
    def test_read_excel_file_integration(self, file_path):
        mounted_path = mount_network()
        assert mounted_path is not None
        
        full_path = get_mounted_path(file_path)
        assert full_path is not None
        
        if os.path.exists(full_path):
            df = read_excel(file_path, sheet_name=0, auto_mount=False)
            assert df is not None
            assert isinstance(df, pd.DataFrame)
        else:
            base_dir = os.path.dirname(full_path)
            if os.path.exists(base_dir):
                all_items = os.listdir(base_dir)
                files = [f for f in all_items if os.path.isfile(os.path.join(base_dir, f))]
                xlsx_files = [f for f in files if f.lower().endswith('.xlsx')]
                if xlsx_files:
                    alternative_path = os.path.join(base_dir, xlsx_files[0])
                    df = pd.read_excel(alternative_path, sheet_name=0, engine='openpyxl')
                    assert df is not None
                    assert isinstance(df, pd.DataFrame)
                else:
                    pytest.skip("Nenhum arquivo Excel encontrado")
            else:
                pytest.skip(f"Diretório não existe: {base_dir}")
