import os
import pandas as pd
from utils.excel_reader import read_xlsx_columns_and_get_data, export_antecipations_to_excel
from fileserver.connection import move_file_to_network_share
from repositories.securitizacao_repository import SecuritizacaoRepository
from repositories.sqlite_repository import SQLiteRepository
from models.models import init_database
from dotenv import load_dotenv

load_dotenv()

file_path = os.getenv("FILE_PATH")
file_path_output = os.getenv("FILE_PATH_OUTPUT")

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
        df_borderos = securitizacao_repo.get_done_bordero_today()
        df_borderos = pd.DataFrame(df_borderos, columns=['bordero'])
        
        if df_borderos.empty:
            print("Nenhum borderô encontrado para hoje.")
            return
        
        print(f"Borderôs encontrados: {len(df_borderos)}")
        
        for _, row in df_borderos.iterrows():
            bordero_id = int(row['bordero'])
            
            try:
                df_bordero_info = securitizacao_repo.get_bordero_info(bordero_id)
                if df_bordero_info.empty:
                    continue
                
                for _, bordero_row in df_bordero_info.iterrows():
                    clifor = int(bordero_row['CLIFOR']) if pd.notna(bordero_row['CLIFOR']) else None
                    sacado_id = int(bordero_row['SACADO']) if pd.notna(bordero_row['SACADO']) else None
                    dcto = bordero_row['DCTO']
                    valor = float(bordero_row['VALOR']) if pd.notna(bordero_row['VALOR']) else None
                    vcto = str(bordero_row['VCTO_']) if pd.notna(bordero_row['VCTO_']) else None
                    
                    print(f"\n[ANALISANDO] BORDERO: {bordero_id} | TITULO: {dcto} | CEDENTE: {clifor}")
                    
                    if clifor is None:
                        print(f"  [X] Falha: CLIFOR nulo.")
                        continue
                    
                    df_cedente_info = securitizacao_repo.get_cedente_name(clifor)
                    if df_cedente_info.empty:
                        print(f"  [X] Falha: Cedente {clifor} não encontrado no SIGCAD.")
                        continue
                    
                    cedente_nome_db = df_cedente_info.iloc[0]['NOME']
                    
                    # Filtro no Excel DE/PARA
                    df_match = df_excel[df_excel['CODIGO CEDENTE'].astype(int) == int(clifor)]
                    
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

                        grupo_sacado_str = str(int(grupo_sacado))

                        # Lógica de validação de Sacado/Grupo
                        if len(grupo_sacado_str) > 3:
                            sacado_excel_id = int(grupo_sacado_str)
                            if sacado_excel_id != sacado_id:
                                print(f"  [X] Falha: Sacado {sacado_id} não bate com ID do Excel {sacado_excel_id}")
                                continue
                        else:
                            grupo_sacado_int = int(grupo_sacado_str)
                            df_group_check = securitizacao_repo.check_sacado_in_group(grupo_sacado_int, sacado_id)
                            if df_group_check.empty:
                                print(f"  [X] Falha: Sacado {sacado_id} não pertence ao grupo {grupo_sacado_int}")
                                continue

                        # Se passou pelas regras, busca info do Sacado
                        df_sacado_info = securitizacao_repo.get_sacado_info(sacado_id)
                        if df_sacado_info.empty:
                            print(f"  [X] Falha: Sacado {sacado_id} sem cadastro no SIGCAD.")
                            continue
                        
                        sacado_info_row = df_sacado_info.iloc[0]
                        sacado_nome_db = sacado_info_row['NOME']
                        cnpj_sacado = str(sacado_info_row['CGC']) if pd.notna(sacado_info_row['CGC']) else None
                        titulo_int = int(dcto) if pd.notna(dcto) else None
                        
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
            df_antecipations = sqlite_repo.get_all_antecipations_as_dataframe()
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