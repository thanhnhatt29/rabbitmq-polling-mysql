# xlsx_to_mysql.py
import pandas as pd
from sqlalchemy import create_engine, text
import sys

# --- Configuration - PLEASE UPDATE THESE VALUES ---
# XLSX File Details
xlsx_file_path = 'mock_data/TPHHLC1.xlsx'  # Replace with the path to your XLSX file
sheet_name = 'Table1'             # Replace with the name of the sheet containing your data
                                  # If None, pandas reads the first sheet by default.

# MySQL Connection Details
db_host = 'localhost'  # Or '127.0.0.1' since you mapped the port
db_port = 3307
db_user = 'root'
db_password = 'rootpassword'  # Replace with the password you set in the docker run command
db_name = 'productiondb'      # Replace with your database name (e.g., 'excel_data')
                                    # This database MUST exist. Create it if you haven't (see Step 1.4).

# Table Details
table_name = 'steel_production_logs'      # Replace with your desired table name in MySQL
                                    # The script will attempt to create this table if it doesn't exist.
if_exists_action = 'replace'        # What to do if the table already exists:
                                    # 'fail': Raise a ValueError.
                                    # 'replace': Drop the table before inserting new values.
                                    # 'append': Insert new values to the existing table.

# --- End of Configuration ---

def main():
    """
    Main function to read data from an XLSX file and write it to a MySQL database.
    """
    print(f"Starting data migration from '{xlsx_file_path}' (Sheet: '{sheet_name}') to MySQL table '{table_name}' in database '{db_name}'.")

    # 1. Read data from XLSX file
    try:
        print(f"Reading data from '{xlsx_file_path}'...")
        if sheet_name:
            df = pd.read_excel(xlsx_file_path, sheet_name=sheet_name)
        else:
            df = pd.read_excel(xlsx_file_path) # Reads the first sheet
        
        if df.empty:
            print("The Excel sheet is empty. No data to migrate.")
            sys.exit(0)
            
        print(f"Successfully read {len(df)} rows and {len(df.columns)} columns from Excel.")
        # print("First 5 rows of data:\n", df.head()) # Uncomment to preview data

        # Sanitize column names for SQL compatibility (optional, but good practice)
        # Example: replace spaces with underscores, convert to lowercase
        original_columns = df.columns.tolist()
        df.columns = [col.replace(' ', '_').replace('-', '_').replace('.', '').lower() for col in df.columns]
        print(f"Sanitized column names: {df.columns.tolist()}")
        if original_columns != df.columns.tolist():
            print(f"Original column names: {original_columns}")


    except FileNotFoundError:
        print(f"Error: The file '{xlsx_file_path}' was not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        sys.exit(1)

    # 2. Create SQLAlchemy engine to connect to MySQL
    # The connection string format is: 'mysql+pymysql://user:password@host:port/database'
    try:
        print(f"Connecting to MySQL database '{db_name}' on {db_host}:{db_port}...")
        engine_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        engine = create_engine(engine_url)

        # Test connection
        with engine.connect() as connection:
            connection.execute(text("SELECT 1")) # Simple query to test connection
        print("Successfully connected to MySQL database.")

    except Exception as e:
        print(f"Error connecting to MySQL database: {e}")
        print("Please check your database credentials, ensure the MySQL server is running,")
        print("and that the database specified ('db_name') exists.")
        sys.exit(1)

    # 3. Write data to MySQL table
    try:
        print(f"Writing data to table '{table_name}' (if_exists='{if_exists_action}')...")
        # Using pandas to_sql method
        # This will create the table based on the DataFrame's structure if it doesn't exist (and if_exists is not 'fail')
        df.to_sql(name=table_name, con=engine, if_exists=if_exists_action, index=False)
        print(f"Data successfully written to MySQL table '{table_name}'.")

    except ValueError as ve:
        if 'already exists' in str(ve).lower() and if_exists_action == 'fail':
            print(f"Error: Table '{table_name}' already exists and 'if_exists_action' is set to 'fail'.")
            print("Change 'if_exists_action' to 'replace' or 'append' if you want to overwrite or add to the table.")
        else:
            print(f"ValueError during data writing: {ve}")
        sys.exit(1)
    except Exception as e:
        print(f"Error writing data to MySQL: {e}")
        sys.exit(1)

    print("Data migration process completed.")

if __name__ == '__main__':
    main()
