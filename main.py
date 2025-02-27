import os
import time
import schedule
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get schedule configuration from .env
#SCHEDULE_INTERVAL = os.getenv('SCHEDULE_INTERVAL', 'hourly')  # Default to hourly if not set
SCHEDULE_INTERVAL = os.getenv('SCHEDULE_INTERVAL', '5min')  # Default to 5min only to development

def task():
    """Main task to be executed on schedule"""
    print(f"Task executed at {datetime.now()}")
    pass

def setup_schedule():
    """Configure the schedule based on environment variable"""
    if SCHEDULE_INTERVAL == '5min':
        schedule.every(5).minutes.do(task)
    elif SCHEDULE_INTERVAL == '10min':
        schedule.every(10).minutes.do(task)
    elif SCHEDULE_INTERVAL == '25min':
        schedule.every(25).minutes.do(task)
    elif SCHEDULE_INTERVAL == 'hourly':
        schedule.every().hour.do(task)
    elif SCHEDULE_INTERVAL == '2hours':
        schedule.every(2).hours.do(task)
    elif SCHEDULE_INTERVAL == 'daily':
        schedule.every().day.at("00:00").do(task)
    else:
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
