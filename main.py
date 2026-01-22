import os
import pandas as pd
from utils.excel_reader import read_xlsx_columns_and_get_data
from repositories.securitizacao_repository import SecuritizacaoRepository
from repositories.sqlite_repository import SQLiteRepository
from models.models import init_database
from dotenv import load_dotenv

load_dotenv()

file_path = os.getenv("FILE_PATH")


def main():
    init_database()
    
    df_excel = read_xlsx_columns_and_get_data(file_path)
    
    try:
        securitizacao_repo = SecuritizacaoRepository()
    except Exception as e:
        print(f"Erro ao conectar com o banco de dados SQL Server: {str(e)}")
        print("Verifique as configurações de conexão no arquivo .env")
        return
    
    sqlite_repo = SQLiteRepository()
    
    try:
        df_borderos = securitizacao_repo.get_done_bordero_today()
        
        if df_borderos.empty:
            return
        
        for _, row in df_borderos.iterrows():
            bordero_id = int(row['bordero'])
            
            try:
                df_bordero_info = securitizacao_repo.get_bordero_info(bordero_id)
                
                if df_bordero_info.empty:
                    print(f"Bordero {bordero_id}: Nenhuma informação encontrada.")
                    continue
                
                print(f"Bordero {bordero_id}: {len(df_bordero_info)} título(s) encontrado(s)")
                
                for _, bordero_row in df_bordero_info.iterrows():
                    clifor = int(bordero_row['CLIFOR']) if pd.notna(bordero_row['CLIFOR']) else None
                    sacado_id = int(bordero_row['SACADO']) if pd.notna(bordero_row['SACADO']) else None
                    dcto = bordero_row['DCTO']
                    valor = float(bordero_row['VALOR']) if pd.notna(bordero_row['VALOR']) else None
                    vcto = str(bordero_row['VCTO_']) if pd.notna(bordero_row['VCTO_']) else None
                    
                    print(f"Bordero {bordero_id}: Processando título {dcto} - CLIFOR = {clifor}, SACADO = {sacado_id}")
                    
                    if clifor is None:
                        print(f"Bordero {bordero_id}: CLIFOR não encontrado para título {dcto}.")
                        continue
                    
                    df_match = df_excel[df_excel['CODIGO CEDENTE'] == clifor]
                    
                    if not df_match.empty:
                        print(f"Bordero {bordero_id}: CLIFOR {clifor} encontrado no Excel ({len(df_match)} correspondência(s))")
                    
                    if df_match.empty:
                        print(f"Bordero {bordero_id}: CLIFOR {clifor} não encontrado no Excel para título {dcto}.")
                        continue
                    
                    for _, excel_row in df_match.iterrows():
                        grupo_sacado = excel_row['GRUPO SACADO']
                        cedente = excel_row['CEDENTE']
                        portal_email = excel_row['PORTAL/EMAIL']
                        login = excel_row['LOGIN']
                        senha = excel_row['SENHA']
                        
                        if pd.isna(grupo_sacado):
                            print(f"Bordero {bordero_id}: GRUPO SACADO não encontrado no Excel para título {dcto}.")
                            continue
                        
                        grupo_sacado = int(grupo_sacado)
                        print(f"Bordero {bordero_id}: GRUPO SACADO = {grupo_sacado}")
                        
                        df_group_check = securitizacao_repo.check_sacado_in_group(grupo_sacado, sacado_id)
                        
                        if not df_group_check.empty:
                            print(f"Bordero {bordero_id}: Sacado {sacado_id} confirmado no grupo {grupo_sacado}")
                        
                        if df_group_check.empty:
                            print(f"Bordero {bordero_id}: Sacado {sacado_id} não está no grupo {grupo_sacado}. Transação cancelada para título {dcto}.")
                            continue
                        
                        df_sacado_info = securitizacao_repo.get_sacado_info(sacado_id)
                        
                        if df_sacado_info.empty:
                            print(f"Bordero {bordero_id}: Informações do sacado {sacado_id} não encontradas para título {dcto}.")
                            continue
                        
                        sacado_info_row = df_sacado_info.iloc[0]
                        sacado_nome_db = sacado_info_row['NOME']
                        cnpj_sacado = str(sacado_info_row['CGC']) if pd.notna(sacado_info_row['CGC']) else None
                        
                        antecipacao = sqlite_repo.insert_antecipacao(
                            cedente=cedente,
                            sacado=sacado_nome_db,
                            bordero=bordero_id,
                            cnpj_sacado=cnpj_sacado,
                            titulo=int(dcto) if pd.notna(dcto) else None,
                            valor=valor,
                            vencimento=vcto,
                            portal_email=str(portal_email) if pd.notna(portal_email) else None,
                            login=str(login) if pd.notna(login) else None,
                            senha=str(senha) if pd.notna(senha) else None,
                            is_inserted=False
                        )
                        
                        print(f"Bordero {bordero_id}: Título {dcto} inserido com sucesso (ID: {antecipacao.id})")
            
            except Exception as e:
                print(f"Erro ao processar bordero {bordero_id}: {str(e)}")
                continue
    
    finally:
        securitizacao_repo.close()


if __name__ == "__main__":
    main()