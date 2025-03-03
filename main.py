import os
import time
import schedule
from datetime import datetime
from dotenv import load_dotenv
from litequeue import LiteQueue
from utils.NotionClient import NotionClient
import TaskProcessor
import logging  # Import the logging module

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s [%(levelname)s] %(message)s",  # Define the log message format
    handlers=[
        logging.FileHandler("app.log"),  # Log to a file named 'app.log'
        logging.StreamHandler()  # Log to the console as well
    ]
)

# Get schedule configuration from .env
SCHEDULE_INTERVAL = os.getenv('SCHEDULE_INTERVAL', '10min')  # Default to 10min only to development
LITEQUEUE_DB = os.getenv('LITEQUEUE_DB', 'queue.sqlite3')  # Default to queue if not set
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')

QUEUE = LiteQueue(LITEQUEUE_DB)

def task():
    """Main task to be executed on schedule"""
    logging.info(f"Task started at {datetime.now()}")
    if not NOTION_TOKEN:
        logging.error("Error: NOTION_TOKEN environment variable is not set")
        logging.error("Please set NOTION_TOKEN in your .env file")
        exit(1)
    if not NOTION_DATABASE_ID:
        logging.error("Error: NOTION_DATABASE_ID environment variable is not set")
        logging.error("Please set NOTION_DATABASE_ID in your .env file")
        exit(1)

    notion = NotionClient.new(NOTION_TOKEN, NOTION_DATABASE_ID, QUEUE)
    processor = TaskProcessor.Processor(QUEUE)
    try:
        logging.info("Processing Notion database queue")
        notion.database_queue()
        if not QUEUE.empty():
            logging.info("Queue is not empty, running processor")
            processor.run()
        logging.info("Task finished")
    except Exception as e:
        logging.exception(f"An error occurred during task execution: {e}")
        return None

SCHEDULE_CONFIGS = {
    '5min': lambda: schedule.every(5).minutes.do(task),
    '10min': lambda: schedule.every(10).minutes.do(task),
    '25min': lambda: schedule.every(25).minutes.do(task),
    'hourly': lambda: schedule.every().hour.do(task),
    '2hours': lambda: schedule.every(2).hours.do(task),
    'daily': lambda: schedule.every().day.at("00:00").do(task)
}

def setup_schedule():
    """Configure the schedule based on environment variable"""
    try:
        SCHEDULE_CONFIGS[SCHEDULE_INTERVAL]()
        logging.info(f"Schedule set to: {SCHEDULE_INTERVAL}")
    except KeyError:
        logging.error(f"Invalid schedule interval: {SCHEDULE_INTERVAL}")
        raise ValueError(f"Invalid schedule interval: {SCHEDULE_INTERVAL}")

def run_scheduler():
    """Run the scheduler as a daemon"""
    setup_schedule()
    logging.info(f"Scheduler started with {SCHEDULE_INTERVAL} interval")

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    try:
        run_scheduler()
    except KeyboardInterrupt:
        logging.info("\nScheduler stopped by user")
    except Exception as e:
        logging.critical(f"A critical error occurred: {e}")
