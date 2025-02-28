import os
from dotenv import load_dotenv
from litequeue import LiteQueue
import concurrent.futures
from utils.NotionClient import NotionClient
from utils.ThemeExtractor import ThemeExtractor
from utils.Summarizer import TextSummarizer
import json

class Processor:
    def __init__(self, queue: LiteQueue):
        load_dotenv()
        self.NOTION_TOKEN = os.getenv('NOTION_TOKEN')
        if not self.NOTION_TOKEN:
            raise ValueError("NOTION_TOKEN environment variable is not set")

        self.queue = queue
        self.notion = None
        
        if self.queue.empty():
            raise ValueError("Queue is empty")
            
        try:
            task = queue.pop()
            if task is None:
                raise ValueError("No tasks available in queue")
            
            task_data = json.loads(task.data)
            print(task_data)
            self.page_id = task_data["id"]
            self.notion = NotionClient.new(self.NOTION_TOKEN, task_data["database_id"])
            self.content = self.notion.get_page(self.page_id)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize processor: {str(e)}")

    def process_theme(self):
        print("process theme")
        theme_extractor = ThemeExtractor()
        theme_result = theme_extractor.extract_themes(self.content)
        return theme_result

    def process_summary(self):
        print("process summary")
        summarizer = TextSummarizer()
        summary_result = summarizer.summarize(self.content)
        return summary_result

    def run(self):
        if self.notion is None:
            raise RuntimeError("Processor not properly initialized")
        try:
            # Create thread pool executor
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Submit both tasks to run in parallel
                theme_future = executor.submit(self.process_theme)
                summary_future = executor.submit(self.process_summary)

                # Get results from both tasks
                theme_result = theme_future.result()
                summary_result = summary_future.result()

            # Update the Notion page with results
            if theme_result:
                self.notion.page_add_description(self.page_id, theme_result["theme"], theme_result["keywords"])

            if summary_result:
                self.notion.page_add_summary(self.page_id, summary_result)
        except Exception as e:
            raise RuntimeError(f"Failed to process task: {str(e)}")
