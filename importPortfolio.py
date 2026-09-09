import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
from google.oauth2.service_account import Credentials
import gspread
from gspread.exceptions import SpreadsheetNotFound
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
        return client.open_by_key(sheet_id).worksheet("Portfolio")
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
            logging.info("Truncating Portfolio table")
            conn.execute(text("""TRUNCATE ods."Portfolio" RESTART IDENTITY"""))

    except Exception as e:
        logging.error(f"Error truncating Portfolio table: {e}")
        return None


def get_sheet_data(worksheet, start_time):
    try:
        df = pd.DataFrame(worksheet.get_all_records())
        df.rename(
            columns={
                "Ticker": "TickerCode",
                "Name": "ScripName",
                "Category": "Category",
                "Sub Category": "SubCategory",
                "InvestmentType": "InvestmentType",
                "InvestmentMethod": "InvestmentMethod",
            },
            inplace=True,
        )
        df["CreateTS"] = pd.to_datetime(start_time)
        df["ModifyTS"] = pd.to_datetime(start_time)
        df.replace("", pd.NA, inplace=True)

        return df

    except Exception as e:
        logging.error(f"Error reading data from Google Sheets: {e}")
        return None


def write_to_ods_table(engine, df):
    try:
        logging.info("Writing data to Portfolio table")
        df.to_sql(
            "Portfolio", con=engine, schema="ods", if_exists="append", index=False
        )
        row_count = df.shape[0]
        logging.info(f"Rows inserted: {row_count}")

    except Exception as e:
        logging.error(f"Error writing data to Portfolio table: {e}")
        return None


def main():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    sheet_id = GOOGLE_SHEET_ID_PORTFOLIO
    creds_file = GOOGLE_CREDENTIALS_PATH

    start_time = datetime.today()

    from pathlib import Path
    Path("Logs\\ImportPortfolio").mkdir(parents=True, exist_ok=True)

    log_filename = start_time.strftime(
        "Logs\\ImportPortfolio\\importPorfolio_%Y%m%d_%H%M%S.log"
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_filename), logging.StreamHandler()],
    )

    logging.info("Script started")

    creds = get_credentials(creds_file, scopes)
    if not creds:
        return

    worksheet = get_worksheet(creds, sheet_id)
    if not worksheet:
        return

    engine = get_engine()
    if not engine:
        return

    truncate_table(engine)
    df = get_sheet_data(worksheet, start_time)
    write_to_ods_table(engine, df)
    logging.info("Script finished")


if __name__ == "__main__":
    main()
