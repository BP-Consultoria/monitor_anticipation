import os
import pandas as pd
from utils.excel_reader import read_xlsx_columns_and_get_data, export_antecipations_to_excel, format_date_to_br
from fileserver.connection import move_file_to_network_share
from repositories.securitizacao_repository import SecuritizacaoRepository
from repositories.sqlite_repository import SQLiteRepository
from models.models import init_database
from dotenv import load_dotenv

load_dotenv()

file_path = os.getenv("FILE_PATH")
file_path_output = os.getenv("FILE_PATH_OUTPUT")


def _ensure_dataframe(obj):
    """Converte retorno do repositório (lista de dicts no Windows) em DataFrame."""
    if obj is None:
        return pd.DataFrame()
    if isinstance(obj, list):
        return pd.DataFrame(obj) if obj else pd.DataFrame()
    return obj


def _get_bordero_value(bordero_row, *keys):
    """Obtém valor da linha tentando várias chaves (ex: EMISSAO/emissao no Windows)."""
    for key in keys:
        if key in bordero_row.index:
            val = bordero_row[key]
            return None if pd.isna(val) else val
    return None


def _safe_int(val, default=None):
    """Converte para int sem falhar com pd.NA/NAType/NaN."""
    if val is None:
        return default
    if pd.isna(val):
        return default
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def main():
    init_database()
    
    df_excel = read_xlsx_columns_and_get_data(file_path)
    
    try:
        securitizacao_repo = SecuritizacaoRepository()
    except Exception as e:
        print(f"Erro ao conectar com o banco de dados SQL Server: {str(e)}")
        return
    
    sqlite_repo = SQLiteRepository()
    
    try:
        df_borderos = _ensure_dataframe(securitizacao_repo.get_done_bordero_today())
        if not df_borderos.empty and 'bordero' not in df_borderos.columns:
            df_borderos = df_borderos.rename(columns={c: c.lower() for c in df_borderos.columns})
        
        if df_borderos.empty:
            print("Nenhum borderô encontrado para hoje.")
            return
        
        print(f"Borderôs encontrados: {len(df_borderos)}")
        
        for _, row in df_borderos.iterrows():
            bordero_id = _safe_int(row['bordero'])
            if bordero_id is None:
                continue
            
            try:
                df_bordero_info = _ensure_dataframe(securitizacao_repo.get_bordero_info(bordero_id))
                if df_bordero_info.empty:
                    continue
                
                for _, bordero_row in df_bordero_info.iterrows():
                    clifor = _safe_int(bordero_row['CLIFOR'])
                    sacado_id = _safe_int(bordero_row['SACADO'])
                    dcto = bordero_row['DCTO']
                    valor = float(bordero_row['VALOR']) if pd.notna(bordero_row['VALOR']) else None
                    vcto_raw = _get_bordero_value(bordero_row, 'VCTO_', 'vcto_')
                    emissao_raw = _get_bordero_value(bordero_row, 'EMISSAO', 'emissao')
                    vcto = format_date_to_br(vcto_raw)
                    emissao = format_date_to_br(emissao_raw)
                    
                    print(f"\n[ANALISANDO] BORDERO: {bordero_id} | TITULO: {dcto} | CEDENTE: {clifor}")
                    
                    if clifor is None:
                        print(f"  [X] Falha: CLIFOR nulo.")
                        continue
                    
                    df_cedente_info = _ensure_dataframe(securitizacao_repo.get_cedente_name(clifor))
                    if df_cedente_info.empty:
                        print(f"  [X] Falha: Cedente {clifor} não encontrado no SIGCAD.")
                        continue
                    
                    cedente_nome_db = df_cedente_info.iloc[0]['NOME']
                    
                    # Filtro no Excel DE/PARA (evita NAType em colunas com NA)
                    codigo_cedente = pd.to_numeric(df_excel['CODIGO CEDENTE'], errors='coerce')
                    df_match = df_excel[codigo_cedente == clifor]
                    
                    if df_match.empty:
                        print(f"  [X] Falha: Cedente {clifor} não cadastrado na planilha Excel.")
                        continue
                    
                    print(f"  [OK] Cedente encontrado na planilha. Verificando regras de Sacado...")

                    for _, excel_row in df_match.iterrows():
                        grupo_sacado = excel_row['GRUPO SACADO']
                        portal_email = excel_row['PORTAL/EMAIL']
                        login = excel_row['LOGIN']
                        senha = excel_row['SENHA']
                        
                        if pd.isna(grupo_sacado):
                            print("  [X] Falha: GRUPO SACADO vazio no Excel.")
                            continue

                        grupo_sacado_int_safe = _safe_int(grupo_sacado)
                        if grupo_sacado_int_safe is None:
                            print("  [X] Falha: GRUPO SACADO inválido no Excel.")
                            continue
                        grupo_sacado_str = str(grupo_sacado_int_safe)

                        # Lógica de validação de Sacado/Grupo
                        if len(grupo_sacado_str) > 3:
                            sacado_excel_id = _safe_int(grupo_sacado_str)
                            if sacado_excel_id is None or sacado_excel_id != sacado_id:
                                print(f"  [X] Falha: Sacado {sacado_id} não bate com ID do Excel {sacado_excel_id}")
                                continue
                        else:
                            grupo_sacado_int = grupo_sacado_int_safe
                            df_group_check = _ensure_dataframe(
                                securitizacao_repo.check_sacado_in_group(grupo_sacado_int, sacado_id)
                            )
                            if df_group_check.empty:
                                print(f"  [X] Falha: Sacado {sacado_id} não pertence ao grupo {grupo_sacado_int}")
                                continue

                        # Se passou pelas regras, busca info do Sacado
                        df_sacado_info = _ensure_dataframe(securitizacao_repo.get_sacado_info(sacado_id))
                        if df_sacado_info.empty:
                            print(f"  [X] Falha: Sacado {sacado_id} sem cadastro no SIGCAD.")
                            continue
                        
                        sacado_info_row = df_sacado_info.iloc[0]
                        sacado_nome_db = sacado_info_row['NOME']
                        cnpj_sacado = str(sacado_info_row['CGC']) if pd.notna(sacado_info_row['CGC']) else None
                        titulo_int = _safe_int(dcto)
                        
                        if titulo_int is None:
                            continue
                        
                        # Verifica duplicidade no SQLite
                        if sqlite_repo.antecipations_exists(bordero_id, titulo_int, cnpj_sacado):
                            print(f"  [!] Ignorado: Título {titulo_int} já processado anteriormente.")
                            continue
                        
                        # TENTA INSERIR
                        print(f"  [>>>] TENTANDO INSERIR NO SQLITE: {cedente_nome_db} -> {sacado_nome_db}")
                        sqlite_repo.insert_antecipacao(
                            cedente=cedente_nome_db,
                            sacado=sacado_nome_db,
                            bordero=bordero_id,
                            cnpj_sacado=cnpj_sacado,
                            titulo=titulo_int,
                            valor=valor,
                            emissao=emissao,
                            vencimento=vcto,
                            portal_email=str(portal_email) if pd.notna(portal_email) else None,
                            login=str(login) if pd.notna(login) else None,
                            senha=str(senha) if pd.notna(senha) else None,
                            is_inserted=False
                        )
                        print(f"  [SUCESSO] Título {titulo_int} registrado!")

            except Exception as e:
                print(f"Erro ao processar bordero {bordero_id}: {str(e)}")
                continue

        # Exportação Final
        print("\n--- Finalizando Processamento ---")
        try:
            df_antecipations = _ensure_dataframe(sqlite_repo.get_all_antecipations_as_dataframe())
            if not df_antecipations.empty:
                print(f"Exportando {len(df_antecipations)} registros para Excel...")
                output_path = export_antecipations_to_excel(df_antecipations)
                move_file_to_network_share(output_path, file_path_output)
                print(f"Arquivo movido para: {file_path_output}")
            else:
                print("Nenhum registro NOVO foi inserido no banco local nesta execução.")
        except Exception as e:
            print(f"Erro ao exportar: {str(e)}")
            
    finally:
        securitizacao_repo.close()


if __name__ == "__main__":
    main()