import os
import time
import schedule
from datetime import datetime
from dotenv import load_dotenv
from litequeue import LiteQueue
from utils.NotionClient import NotionClient
import TaskProcessor

# Load environment variables
load_dotenv()

# Get schedule configuration from .env
#SCHEDULE_INTERVAL = os.getenv('SCHEDULE_INTERVAL', 'hourly')  # Default to hourly if not set
SCHEDULE_INTERVAL = os.getenv('SCHEDULE_INTERVAL', '5min')  # Default to 5min only to development
LITEQUEUE_DB = os.getenv('LITEQUEUE_DB', 'queue.sqlite3')  # Default to queue if not set
NOTION_TOKEN = os.getenv('NOTION_TOKEN') 
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID') 

QUEUE = LiteQueue(LITEQUEUE_DB)

def task():
    """Main task to be executed on schedule"""
    print(f"Task executed at {datetime.now()}")
    if not NOTION_TOKEN:
        print("Error: NOTION_TOKEN environment variable is not set")
        print("Please set NOTION_TOKEN in your .env file")
        exit(1)
    if not NOTION_DATABASE_ID:
        print("Error: NOTION_DATABASE_ID environment variable is not set")
        print("Please set NOTION_DATABASE_ID in your .env file")
        exit(1)

    notion = NotionClient.new(NOTION_TOKEN, NOTION_DATABASE_ID, QUEUE)
    processor = TaskProcessor.Processor(QUEUE)
    try:
        if not QUEUE.empty():
            processor.run()
        notion.database_queue()
    except Exception as e:
        print(e)
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
    except KeyError:
        raise ValueError(f"Invalid schedule interval: {SCHEDULE_INTERVAL}")

def run_scheduler():
    """Run the scheduler as a daemon"""
    setup_schedule()
    print(f"Scheduler started with {SCHEDULE_INTERVAL} interval")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    try:
        run_scheduler()
    except KeyboardInterrupt:
        print("\nScheduler stopped by user")
    except Exception as e:
        print(f"Error occurred: {e}")
