import os
from utils.excel_reader import read_xlsx_columns_and_get_data
from dotenv import load_dotenv

load_dotenv()

file_path = os.getenv("FILE_PATH")

def main():
    df = read_xlsx_columns_and_get_data(file_path)
    print(df)


if __name__ == "__main__":
    main()