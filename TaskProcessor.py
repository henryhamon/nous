import os
import time
from dotenv import load_dotenv
from litequeue import LiteQueue
import concurrent.futures
from utils.NotionClient import NotionClient
from utils.ThemeExtractor import ThemeExtractor
from utils.Summarizer import TextSummarizer
import json
import logging

class Processor:
    def __init__(self, queue: LiteQueue):
        load_dotenv()
        self.NOTION_TOKEN = os.getenv('NOTION_TOKEN')
        if not self.NOTION_TOKEN:
            raise ValueError("NOTION_TOKEN environment variable is not set")

        self.queue = queue
        self.notion = None

        logging.info("Initializing TaskProcessor...")
        
        if self.queue.empty():
            raise ValueError("Queue is empty")
            
        try:
            logging.info("Popping a task from the queue...")
            task = queue.pop()
            if task is None:
                raise ValueError("No tasks available in queue")
            
            task_data = json.loads(task.data)
            logging.debug(f"Task data: {task_data}")
            self.page_id = task_data["id"]
            self.notion = NotionClient.new(self.NOTION_TOKEN, task_data["database_id"])
            logging.info(f"Fetching content for page ID: {self.page_id}")
            self.content = self.notion.get_page(self.page_id)
            logging.info(f"Content fetched successfully for page ID: {self.page_id}")
        except Exception as e:
            logging.error(f"Failed to initialize processor: {str(e)}")
            raise RuntimeError(f"Failed to initialize processor: {str(e)}")

        logging.info("TaskProcessor initialized successfully.")

    def process_theme(self):
        logging.info("Starting theme processing...")
        start_time = time.time()
        theme_extractor = ThemeExtractor()
        theme_result = theme_extractor.extract_themes(self.content)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.info(f"Theme processing completed in {elapsed_time:.2f} seconds.")
        if theme_result:
            logging.debug(f"Theme processing result: {theme_result}")
        return theme_result

    def process_summary(self):
        logging.info("Starting summary processing...")
        start_time = time.time()
        summarizer = TextSummarizer()
        summary_result = summarizer.summarize(self.content)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.info(f"Summary processing completed in {elapsed_time:.2f} seconds.")
        if summary_result:
            logging.debug(f"Summary processing result: {summary_result}")
        return summary_result

    def run(self):
        if self.notion is None:
            logging.error("Processor not properly initialized")
            raise RuntimeError("Processor not properly initialized")
        try:
            logging.info("Starting concurrent processing of theme and summary...")
            # Create thread pool executor
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Submit both tasks to run in parallel
                theme_future = executor.submit(self.process_theme)
                summary_future = executor.submit(self.process_summary)

                # Get results from both tasks
                theme_result = theme_future.result()
                summary_result = summary_future.result()
            logging.info("Concurrent processing completed.")
            # Update the Notion page with results
            if theme_result:
                logging.info(f"Updating Notion page {self.page_id} with theme and keywords...")
                self.notion.page_add_description(self.page_id, theme_result["theme"], theme_result["keywords"])
                logging.info(f"Notion page {self.page_id} updated with theme and keywords.")
            else:
                logging.warning(f"Notion page {self.page_id} not update with theme and keywords, since not result")

            if summary_result:
                logging.info(f"Updating Notion page {self.page_id} with summary...")
                self.notion.page_add_summary(self.page_id, summary_result)
                logging.info(f"Notion page {self.page_id} updated with summary.")
            else:
                logging.warning(f"Notion page {self.page_id} not update with summary, since not result")
        except Exception as e:
            logging.error(f"Failed to process task: {str(e)}")
            raise RuntimeError(f"Failed to process task: {str(e)}")
