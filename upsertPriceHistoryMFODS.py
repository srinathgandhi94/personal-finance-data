import logging
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
import pandas as pd
from sqlalchemy.sql import text

from config import DATABASE_URL

def get_engine():
    try:
        engine = create_engine(DATABASE_URL)
        logging.info("Successfully connected to PostgreSQL")
        return engine
    except Exception as e:
        logging.error(f"Error connecting to PostgreSQL: {e}")
        return None
    
def get_staging_data(engine):
    try:
        query = '''SELECT * FROM stg."priceHistoryMF"'''   
        logging.info("Fetching data from priceHistoryMF table")
        return pd.read_sql(query, engine)
    except Exception as e:
        logging.error(f"Error fetching data from priceHistoryMF table: {e}")
        return None

def upsert_to_ods_table(engine, df, ods_table, start_time):
    # Counters for tracking inserts and updates
    inserted_count = 0
    updated_count = 0

    df['CreateTS'] = pd.to_datetime(start_time)
    df['ModifyTS'] = pd.to_datetime(start_time)

    records = df.to_dict(orient="records")
    batch_size=5000

    try:
        with engine.begin() as conn:
            for i in range(0, len(records), batch_size):
                batch = records[i : i + batch_size]

                # Create an insert statement with conflict resolution
                insert_stmt = insert(ods_table).values(batch)
                
                # Define the conflict resolution strategy
                upsert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=['Date', 'TickerCode', 'Platform'],  # Conflict target (primary key)
                    set_={
                        "Close": insert_stmt.excluded.Close,
                        "ModifyTS": insert_stmt.excluded.ModifyTS
                    },
                    where=(
                        (ods_table.c.Close != insert_stmt.excluded.Close)
                    ) 
                ).returning(ods_table.c.PriceHistoryMFId, text("xmax::text::bigint"))

                logging.info(f"Processing batch {i // batch_size + 1}")
                result = conn.execute(upsert_stmt)
                returned_rows = result.fetchall()
                insertedList = filter(lambda x: x[1] == 0, returned_rows)
                updatedList = filter(lambda x: x[1] > 0, returned_rows)

                inserted_count = inserted_count + len(list(insertedList))
                updated_count = updated_count + len(list(updatedList))

        logging.info("Upsert completed successfully!")
        logging.info(f"Records Inserted: {inserted_count}")
        logging.info(f"Records Updated: {updated_count}")

    except Exception as e:
        logging.error(f"Error during upsert: {e}")

def main():
    start_time = datetime.today()

    from pathlib import Path
    Path("Logs\\UpsertPriceHistoryMFODS").mkdir(parents=True, exist_ok=True)

    log_filename = start_time.strftime("Logs\\UpsertPriceHistoryMFODS\\upsertPriceHistoryMFODS_%Y%m%d_%H%M%S.log")

    logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_filename),
                        logging.StreamHandler()
                    ])
    
    logging.info("Script started")

    engine = get_engine()
    if not engine:
        return
    
    # Step 2: Reflect Existing Tables from the Database
    metadata = MetaData()
    metadata.reflect(bind=engine)

    # Dynamically load tables
    ods_table = Table('PriceHistoryMF', metadata, schema='ods', autoload_with=engine)
    logging.info("Loaded ODS table schema")

    df_stg = get_staging_data(engine)
    if df_stg is None or df_stg.empty:
        logging.warning("No data found in staging table or error occurred")
        return
    
    upsert_to_ods_table(engine, df_stg, ods_table, start_time)
    logging.info("Script finished")
    
if __name__ == "__main__":
    main()