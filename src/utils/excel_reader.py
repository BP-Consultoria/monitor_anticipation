import os
from typing import Optional, Union
import pandas as pd
from fileserver.connection import get_mounted_path, mount_network


def read_excel(
    file_path: str,
    sheet_name: Optional[Union[str, int]] = 0,
    network_path: Optional[str] = None,
    auto_mount: bool = True
) -> pd.DataFrame:
    if auto_mount:
        try:
            mount_network(network_path)
        except Exception:
            pass
    
    full_path = get_mounted_path(file_path, network_path)
    
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Excel file not found: {full_path}")
    
    df = pd.read_excel(full_path, sheet_name=sheet_name, engine='openpyxl')
    return df


def read_excel_multiple_sheets(
    file_path: str,
    network_path: Optional[str] = None,
    auto_mount: bool = True
) -> dict[str, pd.DataFrame]:
    if auto_mount:
        try:
            mount_network(network_path)
        except Exception:
            pass
    
    full_path = get_mounted_path(file_path, network_path)
    
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Excel file not found: {full_path}")
    
    excel_file = pd.ExcelFile(full_path, engine='openpyxl')
    sheets_dict = {sheet_name: pd.read_excel(excel_file, sheet_name=sheet_name) 
                   for sheet_name in excel_file.sheet_names}
    return sheets_dict


def read_xlsx_columns_and_get_data(
    file_path: str,
    network_path: Optional[str] = None,
    auto_mount: bool = True,
    sheet_name: Optional[Union[str, int]] = 0
) -> pd.DataFrame:
    required_columns = ['CEDENTES', 'SACADO', 'PORTAL/EMAIL', 'LOGIN', 'SENHA']
    
    if auto_mount:
        try:
            mount_network(network_path)
        except Exception:
            pass
    
    full_path = get_mounted_path(file_path, network_path)
    
    if not os.path.exists(full_path):
        base_dir = os.path.dirname(full_path)
        if os.path.exists(base_dir):
            all_items = os.listdir(base_dir)
            files = [f for f in all_items if os.path.isfile(os.path.join(base_dir, f))]
            xlsx_files = [f for f in files if f.lower().endswith('.xlsx')]
            
            if xlsx_files:
                selected_file = None
                for f in xlsx_files:
                    if 'RELAÇÃO PORTAIS' in f.upper() or 'ANTECIPAÇÃO' in f.upper():
                        selected_file = f
                        break
                
                if not selected_file:
                    selected_file = xlsx_files[0]
                
                base_path = os.path.dirname(file_path)
                file_path = os.path.join(base_path, selected_file)
            else:
                raise FileNotFoundError(f"Nenhum arquivo Excel encontrado em: {base_dir}")
        else:
            raise FileNotFoundError(f"Diretório não existe: {base_dir}")
    
    df = read_excel(file_path, sheet_name=sheet_name, network_path=network_path, auto_mount=False)
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Colunas obrigatórias não encontradas no arquivo: {', '.join(missing_columns)}")
    
    df_filtered = df[required_columns].copy()
    
    df_filtered = df_filtered.dropna(subset=['CEDENTES', 'SACADO'], how='all')
    
    return df_filtered