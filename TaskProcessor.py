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
import requests
from bs4 import BeautifulSoup

class Processor:
    def __init__(self, queue: LiteQueue):
        load_dotenv()
        self.NOTION_TOKEN = os.getenv('NOTION_TOKEN')
        if not self.NOTION_TOKEN:
            raise ValueError("NOTION_TOKEN environment variable is not set")

        self.queue = queue
        self.notion = None
        self.task_id = None
        page_url = None

        logging.info("Initializing TaskProcessor...")
        
        if ((self.queue.empty()) or (self.queue.qsize() < 1)):
            logging.info("Queue is empty")
            return
            
        try:
            logging.info("Popping a task from the queue...")
            task = queue.pop()
            if task is None:
                raise ValueError("No tasks available in queue")
            
            task_data = json.loads(task.data)
            logging.debug(f"Task data: {task_data}")
            self.task_id = task.message_id
            self.page_id = task_data["id"]
            self.notion = NotionClient.new(self.NOTION_TOKEN, task_data["database_id"])
            logging.info(f"Fetching content for page ID: {self.page_id}")
            self.content = self.notion.get_page(self.page_id)

            # Check if content is empty or None, if so, get the URL and scrape the content.
            if not self.content:
                logging.warning(f"Content for page ID {self.page_id} is empty. Attempting to scrape from URL.")
                page_url = self.notion.get_page_url(self.page_id)
                if page_url:
                    logging.info(f"Scraping content from URL: {page_url}")
                    self.content = self.scrape_content_from_url(page_url)
                    if (self.content == ""):
                        queue.mark_failed(self.task_id)
                        logging.error(f"Failed to fetch content for: {page_url}")
                else:
                    queue.mark_failed(self.task_id)
                    logging.error(f"Failed to fetch content for: {self.page_id}")
                    return

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

    def scrape_content_from_url(self, url):
        """Scrapes text content from a given URL using BeautifulSoup."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        max_retries = 3
        retry_delay = 2  # seconds
    
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                text_content = soup.get_text(separator=' ', strip=True)
                return text_content
            except requests.exceptions.RequestException as e:
                logging.error(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                logging.error(f"Error scraping content from {url}: {e}")
                return ""
            except Exception as e:
                logging.error(f"An unexpected error occurred during scraping from {url}: {e}")
                return ""

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
                self.notion.page_add_summary(self.page_id, summary_result[:2000])
                logging.info(f"Notion page {self.page_id} updated with summary.")
            else:
                logging.warning(f"Notion page {self.page_id} not update with summary, since not result")
            
            if self.task_id is not None:
                logging.info(f"Marking task {self.task_id} as done...")
                self.queue.done(self.task_id)
        except Exception as e:
            logging.error(f"Failed to process task: {str(e)}")
            raise RuntimeError(f"Failed to process task: {str(e)}")
