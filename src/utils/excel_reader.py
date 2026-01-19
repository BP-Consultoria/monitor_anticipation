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

