import sys
import subprocess
import logging
from loggingSetup import setup_logging
from datetime import datetime
from calendar import monthrange
from pathlib import Path

start_time = datetime.today()


def get_six_months_ago(reference_date: datetime) -> datetime:
    target_month = reference_date.month - 6
    target_year = reference_date.year

    while target_month <= 0:
        target_month += 12
        target_year -= 1

    last_day_of_target_month = monthrange(target_year, target_month)[1]
    target_day = min(reference_date.day, last_day_of_target_month)

    return reference_date.replace(
        year=target_year,
        month=target_month,
        day=target_day,
    )


def delete_old_logs(log_directory: Path, cutoff_date: datetime) -> None:
    try:
        if not log_directory.exists():
            return

        for log_file_path in log_directory.rglob("*"):
            if not log_file_path.is_file():
                continue
            try:
                modified_time = datetime.fromtimestamp(log_file_path.stat().st_mtime)
                if modified_time < cutoff_date:
                    log_file_path.unlink()
            except OSError as error:
                logging.error(f"Failed to process log file {log_file_path}: {error}")
    except OSError as error:
        logging.error(f"Failed to clean up old logs in {log_directory}: {error}")


log_directory = Path("Logs")
log_directory.mkdir(parents=True, exist_ok=True)
Path("Logs\\Main").mkdir(parents=True, exist_ok=True)
# NOTE: "6 months" is treated as 6 calendar months from today's date.
delete_old_logs(log_directory, get_six_months_ago(start_time))

log_filename = start_time.strftime("Logs\\Main\\main_%Y%m%d_%H%M%S.log")

setup_logging(log_filename)

logging.info("Starting the Import Portfolio process...")
subprocess.run([sys.executable, "importPortfolio.py"], check=True)
logging.info("Import Portfolio process completed.\n")

logging.info("Starting the Import Transactions process...")
subprocess.run([sys.executable, "importTransactions.py"], check=True)
logging.info("Import Transactions process completed.\n")

logging.info("Starting the Import Price History MF process...")
subprocess.run([sys.executable, "importPriceHistoryMF.py"], check=True)
logging.info("Import Price History MF process completed.\n")

logging.info("Starting the Upsert Price History MF ODS process...")
subprocess.run([sys.executable, "upsertPriceHistoryMFODS.py"], check=True)
logging.info("Upsert Price History MF ODS process completed.\n")

logging.info("Starting the Import Price History Stocks process...")
subprocess.run([sys.executable, "importPriceHistoryStocks.py"], check=True)
logging.info("Import Price History Stocks process completed.\n")

logging.info("Starting the Upsert Price History Stocks ODS process...")
subprocess.run([sys.executable, "upsertPriceHistoryStockODS.py"], check=True)
logging.info("Upsert Price History Stocks ODS process completed.\n")

logging.info("Starting the Import Investment Report process...")
subprocess.run([sys.executable, "importInvestmentReport.py"], check=True)
logging.info("Import Investment Report process completed.\n")

logging.info("Starting the Import Expense Manager process...")
subprocess.run([sys.executable, "importExpenseManager.py"], check=True)
logging.info("Import Expense Manager process completed.\n")
