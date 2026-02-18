import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
from google.oauth2.service_account import Credentials
import gspread
from gspread.exceptions import SpreadsheetNotFound
import threading
import time
import logging

from config import GOOGLE_CREDENTIALS_PATH, GOOGLE_SHEET_ID_PORTFOLIO, DATABASE_URL

def get_credentials(creds_file, scopes):
    try:
        return Credentials.from_service_account_file(creds_file, scopes=scopes)
    except Exception as e:
        logging.error(f"Error loading credentials: {e}")
        return None

def get_worksheet(creds, sheet_id):
    try:
        logging.info("Connecting to Google Sheets")
        client = gspread.authorize(creds)
        logging.info("Connected to Google Sheets")
        return client.open_by_key(sheet_id).worksheet("PriceHistory")
    except SpreadsheetNotFound:
        logging.error("Spreadsheet not found.")
        return None
    except Exception as e:
        logging.error(f"Error accessing spreadsheet: {e}")
        return None
    
def get_engine():
    try:
        # Connect to PostgreSQL
        engine = create_engine(DATABASE_URL)
        return engine
    except Exception as e:
        logging.error(f"Error connecting to Postgresql: {e}")
        return None

def truncate_table(engine):
    try:
        with engine.begin() as conn:
            logging.info("Connection Established")
            logging.info("Truncating priceHistoryMF table")
            conn.execute(text('''TRUNCATE stg."priceHistoryMF" RESTART IDENTITY'''))
            
    except Exception as e:
        logging.error(f"Error truncating priceHistoryMF table: {e}")
        return None
    
def verify_formula_loaded(worksheet):
    try:
        # Verify if formula loaded correctly
        logging.info("--Verify if formula loaded correctly")
        thread = threading.Thread(target=background_formula_load_check, args=(worksheet,))
        thread.start()
    
        # wait here for the result to be available before continuing
        thread.join()
        logging.info("--Formula loaded successfully")
        
    except Exception as e:
        logging.error(f"Error checking formula load: {e}")

def background_formula_load_check(worksheet, max_retries=3, sleep_interval=5):
    retries = 0
    while retries < max_retries:
        try:
            if worksheet.acell('B1').value == "Close":
                logging.info("--Formula loaded successfully in background check")
                return
            else:
                logging.info(f"--Formula not loaded yet, retrying... ({retries + 1}/{max_retries})")
                time.sleep(sleep_interval)
                retries += 1
        except Exception as e:
            logging.error(f"Error checking formula load: {e}")
            time.sleep(sleep_interval)
            retries += 1

def get_ticker_list(engine):
    try:
        query = '''SELECT tr."TickerCode"
				, tr."Platform"
                , GREATEST(MIN(tr."Date"), CAST(MAX(phm."Date") - INTERVAL ' 2 months' AS DATE)) "Date"
				FROM ods."Transactions" tr
                INNER JOIN ods."Portfolio" pf
                ON tr."TickerCode" = pf."TickerCode"
                LEFT JOIN ods."PriceHistoryMF" phm
                ON phm."TickerCode" = pf."TickerCode"
                WHERE pf."Category" = 'Mutual Fund'
                GROUP BY tr."TickerCode", tr."Platform"'''
        
        return pd.read_sql(query, engine)
            
    except Exception as e:
        logging.error(f"Error fetching ticker list: {e}")
        return None

def get_sheet_data(worksheet, ticker_code):
    try:
        df = pd.DataFrame(worksheet.get_all_records())
        df["Date"] = pd.to_datetime(df["Date"]).dt.date
        df['TickerCode'] = ticker_code
        df.replace("", pd.NA, inplace=True)

        return df
    
    except Exception as e:
        logging.error(f"Error reading data from Google Sheets: {e}")
        return None

def write_to_staging_table(engine, df):
    try:
        # Write data to staging table
        logging.info("--Writing data to priceHistoryMF table")
        df.to_sql('priceHistoryMF', con=engine, schema='stg', if_exists='append', index=False)
        row_count = df.shape[0]
        logging.info(f"--Rows inserted: {row_count}")
        return row_count

    except Exception as e:
        logging.error(f"Error writing data to priceHistoryMF table: {e}")
        return None
    

def main():
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    sheet_id = GOOGLE_SHEET_ID_PORTFOLIO
    creds_file = GOOGLE_CREDENTIALS_PATH

    start_date = "1900-01-01"
    end_date = datetime.today().strftime('%Y-%m-%d')
    ticker_code = ""
    finance_query = f""""""
    total_row_count = 0
    total_scrip_count = 0

    start_time = datetime.today()

    log_filename = start_time.strftime("Logs\\ImportPriceHistoryMF\\importPriceHistoryMF_%Y%m%d_%H%M%S.log")

    logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_filename),
                        logging.StreamHandler()
                    ])
    
    logging.info("Script started")

    creds = get_credentials(creds_file, scopes)
    if not creds:
        logging.error("Error loading credentials")
        return
    
    worksheet = get_worksheet(creds, sheet_id)
    if not worksheet:
        logging.error("Error accessing worksheet")
        return

    engine = get_engine()
    if not engine:
        logging.error("Error connecting to Postgresql")
        return

    # Truncate table
    truncate_table(engine)

    # Get ticker list
    ticker_list_df = get_ticker_list(engine)
    if ticker_list_df is None or ticker_list_df.empty:
        logging.info("No data found in ticker list")
        return
    
    for index, row in ticker_list_df.iterrows():
        logging.info(f"Processing ticker: {row['TickerCode']}")
        ticker_code = row["TickerCode"]
        start_date = row["Date"].strftime('%Y-%m-%d')
        finance_query = f"""=GOOGLEFINANCE("{ticker_code}", "price", "{start_date}", "{end_date}")"""
        worksheet.update_acell("A1", finance_query)
        verify_formula_loaded(worksheet)
        df = get_sheet_data(worksheet, ticker_code)
        df["Platform"] = row["Platform"]
        total_row_count = total_row_count + write_to_staging_table(engine, df)
        total_scrip_count = total_scrip_count + 1
        time.sleep(5)

    logging.info(f"Total scrips processed: {total_scrip_count}")
    logging.info(f"Total rows inserted: {total_row_count}")
    logging.info("Script finished")

if __name__ == "__main__":
    main()