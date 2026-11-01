import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import logging
from loggingSetup import setup_logging

from config import DATABASE_URL, WALLET_REPORT_FILE


def get_engine():
    try:
        engine = create_engine(DATABASE_URL)
        return engine
    except Exception as e:
        logging.error(f"Error connecting to PostgreSQL: {e}")
        return None


def truncate_table(engine) -> None:
    try:
        with engine.begin() as conn:
            logging.info("Connection established")
            logging.info("Truncating ExpenseManager table")
            conn.execute(text('TRUNCATE ods."ExpenseManager" RESTART IDENTITY'))
    except Exception as e:
        logging.error(f"Error truncating ExpenseManager table: {e}")
        raise


def read_wallet_report() -> pd.DataFrame | None:
    try:
        logging.info(f"Reading Excel file: {WALLET_REPORT_FILE}")
        df = pd.read_excel(WALLET_REPORT_FILE, sheet_name=0, engine="openpyxl")
        logging.info(f"Read {len(df)} rows from Excel file")
        return df
    except FileNotFoundError:
        logging.error(f"Wallet report file not found: {WALLET_REPORT_FILE}")
        return None
    except Exception as e:
        logging.error(f"Error reading Excel file: {e}")
        return None


def transform_data(df: pd.DataFrame, start_time: datetime) -> pd.DataFrame | None:
    column_mapping: dict[str, str] = {
        "account": "Account",
        "category": "Category",
        "currency": "Currency",
        "amount": "Amount",
        "ref_currency_amount": "RefCurrencyAmount",
        "type": "Type",
        "payment_type": "PaymentType",
        "payment_type_local": "PaymentTypeLocal",
        "note": "Note",
        "date": "Date",
        "gps_latitude": "GpsLatitude",
        "gps_longitude": "GpsLongitude",
        "gps_accuracy_in_meters": "GpsAccuracyInMeters",
        "warranty_in_month": "WarrantyInMonth",
        "transfer": "Transfer",
        "payee": "Payee",
        "labels": "Labels",
        "envelope_id": "EnvelopeId",
        "custom_category": "CustomCategory",
    }

    try:
        df = df.rename(columns=column_mapping)
    except Exception as e:
        logging.error(f"Column renaming failed: {e}")
        return None

    expected_columns = list(column_mapping.values())
    missing_columns = [col for col in expected_columns if col not in df.columns]
    if missing_columns:
        logging.error(f"Missing columns in Excel file: {missing_columns}")
        return None

    df = df[expected_columns].copy()

    # Type conversions
    for col in [
        "Amount",
        "RefCurrencyAmount",
        "GpsLatitude",
        "GpsLongitude",
        "GpsAccuracyInMeters",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["WarrantyInMonth"] = pd.to_numeric(
        df["WarrantyInMonth"], errors="coerce"
    ).astype("Int64")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Boolean columns may come in as TRUE/FALSE strings or Python booleans
    for col in ["Transfer", "CustomCategory"]:
        if df[col].dtype == object:
            df[col] = df[col].map(
                {"TRUE": True, "FALSE": False, True: True, False: False}
            )
        df[col] = df[col].astype("boolean")

    df.replace("", pd.NA, inplace=True)

    df["CreateTS"] = pd.to_datetime(start_time)
    df["ModifyTS"] = pd.to_datetime(start_time)

    return df


def write_to_ods_table(engine, df: pd.DataFrame) -> None:
    try:
        logging.info("Writing data to ExpenseManager table")
        df.to_sql(
            "ExpenseManager", con=engine, schema="ods", if_exists="append", index=False
        )
        logging.info(f"Rows inserted: {len(df)}")
    except Exception as e:
        logging.error(f"Error writing data to ExpenseManager table: {e}")
        raise


def main() -> None:
    start_time = datetime.today()

    from pathlib import Path

    Path("Logs\\ImportExpenseManager").mkdir(parents=True, exist_ok=True)

    log_filename = start_time.strftime(
        "Logs\\ImportExpenseManager\\importExpenseManager_%Y%m%d_%H%M%S.log"
    )

    setup_logging(log_filename)

    logging.info("Script started")

    engine = get_engine()
    if not engine:
        return

    df = read_wallet_report()
    if df is None:
        return

    df = transform_data(df, start_time)
    if df is None:
        return

    truncate_table(engine)
    write_to_ods_table(engine, df)

    logging.info("Script finished")


if __name__ == "__main__":
    main()
