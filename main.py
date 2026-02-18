import os
import logging
from datetime import datetime

start_time = datetime.today()

log_filename = start_time.strftime("Logs\\Main\\main_%Y%m%d_%H%M%S.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_filename), logging.StreamHandler()],
)

logging.info("Starting the Import Portfolio process...")
os.system("python importPortfolio.py")
logging.info("Import Portfolio process completed.\n")

logging.info("Starting the Import Transactions process...")
os.system("python importTransactions.py")
logging.info("Import Transactions process completed.\n")

logging.info("Starting the Import Price History MF process...")
os.system("python importPriceHistoryMF.py")
logging.info("Import Price History MF process completed.\n")

logging.info("Starting the Upsert Price History MF ODS process...")
os.system("python upsertPriceHistoryMFODS.py")
logging.info("Upsert Price History MF ODS process completed.\n")

logging.info("Starting the Import Price History Stocks process...")
os.system("python importPriceHistoryStocks.py")
logging.info("Import Price History Stocks process completed.\n")

logging.info("Starting the Upsert Price History Stocks ODS process...")
os.system("python upsertPriceHistoryStockODS.py")
logging.info("Upsert Price History Stocks ODS process completed.\n")

logging.info("Starting the Import Investment Report process...")
os.system("python importInvestmentReport.py")
logging.info("Import Investment Report process completed.\n")
