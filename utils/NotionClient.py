import requests
import json
from litequeue import LiteQueue

class NotionClient:
    API_VERSION = "2022-06-28"
    BASE_URL = "https://api.notion.com/v1"
    NEWS_FILTER = {"filter": {"and": [{"property": "Summary",
                        "checkbox": {
                            "equals": True
                        }},{"property": "Read",
                        "checkbox": {
                            "equals": False
                        }}]},
                "sorts": [
                        {
                            "property": "Date",
                            "direction": "ascending"
                        }
                    ]
            }
    
    def __init__(self, token: str, database_id: str, queue: LiteQueue = None):
        """
        Initialize NotionClient.
        
        Args:
            token: Notion API token
            database_id: ID of the target database
            queue: Optional LiteQueue instance for queueing operations
        """
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": self.API_VERSION,
        }
        self.database_id = database_id
        self.url_base = self.BASE_URL
        self.queue = queue

    def _handle_error(self, error: Exception, context: str = "") -> None:
        """
        Private method to handle error messages consistently.
        
        Args:
            error: The exception that was raised
            context: Optional string providing context about where the error occurred
        """
        error_message = f"Error{f' in {context}' if context else ''}: {str(error)}"
        print(error_message)
        return None

    def _get_url(self, endpoint: str) -> str:
        return f"{self.url_base}/{endpoint}/"

    def _get(self, url) -> requests.Response:
        return requests.get(url, headers=self.headers)

    def _post(self, url, payload: dict) -> requests.Response:
        return requests.post(url, headers=self.headers, json=payload)

    def _patch(self, url, payload: dict) -> requests.Response:
        return requests.patch(url, headers=self.headers, json=payload)

    def retrieving_blocks(self, page_id, next_cursor = ""):
        result = []
        if (next_cursor == ""):
            url = f"{self._get_url("blocks")}{page_id}/children?page_size=100" 
        else: 
            url = f"{self._get_url("blocks")}{page_id}/children?page_size=100&start_cursor={next_cursor}"

        response = self._get(url)
        if response.status_code == 200:
            data = response.json()
            result = self.parse_notion_blocks(data)
            if data["has_more"]:
                result.extend(self.retrieving_blocks(page_id, data["next_cursor"]))
        return result

    def parse_notion_blocks(self, notion_api_response):
        # Ensure notion_api_response is a dictionary
        if isinstance(notion_api_response, str):
            notion_api_response = json.loads(notion_api_response)

        # Check if the response has 'results'
        if not isinstance(notion_api_response, dict) or 'results' not in notion_api_response:
            return {"error": "Invalid API response format"}

        blocks = notion_api_response.get("results", [])
        parsed_blocks = []

        text_buffer = []
        list_buffer = []
        list_type = None

        def flush_buffers():
            if text_buffer:
                parsed_blocks.append("\n".join(text_buffer))
                text_buffer.clear()
            if list_buffer:
                if list_type == "bulleted_list_item":
                    formatted_list = "\n".join(f"- {item}" for item in list_buffer)
                elif list_type == "numbered_list_item":
                    formatted_list = "\n".join(f"{i+1}. {item}" for i, item in enumerate(list_buffer))
                parsed_blocks.append(formatted_list)
                list_buffer.clear()

        def extract_text(block):
            if "text" in block:
                text_objects = block.get("text", [])
                return " ".join(text_obj.get("plain_text", "") for text_obj in text_objects if isinstance(text_obj, dict))
            elif "rich_text" in block:
                rich_text = block.get("rich_text", [])
                text_parts = []
                for text_obj in rich_text:
                    if isinstance(text_obj, dict) and "text" in text_obj:
                        text_parts.append(text_obj["text"].get("content", ""))
                return " ".join(text_parts)
            return ""

        for block in blocks:
            if not isinstance(block, dict):
                continue

            block_type = block.get("type")
            content = ""

            if block_type == "paragraph":
                content = extract_text(block[block_type])
                if content:
                    if list_buffer:
                        flush_buffers()
                    text_buffer.append(content)
            elif block_type == "image":
                if "file" in block[block_type] and "url" in block[block_type]["file"]:
                    content = block[block_type]["file"]["url"]
                elif "external" in block[block_type] and "url" in block[block_type]["external"]:
                    content = block[block_type]["external"]["url"]
                if content:
                    flush_buffers()
                    parsed_blocks.append(content)
            elif block_type in ["bulleted_list_item", "numbered_list_item"]:
                content = extract_text(block[block_type])
                if content:
                    if list_type is None:
                        list_type = block_type
                    if block_type != list_type:
                        flush_buffers()
                        list_type = block_type
                    list_buffer.append(content)
            elif block_type in ["heading_1", "heading_2", "heading_3"]:
                content = extract_text(block[block_type])
                if content:
                    flush_buffers()
                    parsed_blocks.append(content)
            else:
                flush_buffers()

        flush_buffers()
        return parsed_blocks

    @classmethod
    def new(cls, token: str, database_id: str, queue: LiteQueue = None):
        return cls(token, database_id, queue)

    def get_page(self, page_id):
        output = " \n ".join(self.retrieving_blocks(page_id))
        return output

    def get_page_url(self, page_id):
        url = f"{self._get_url('pages')}{page_id}"
        try:
            response = self._get(url)
            if response.status_code == 200:
                data = response.json()
                return data["properties"]["URL"]["url"]
        except Exception as e:
            return self._handle_error(e)
        return 

    def get_database(self):
        url = f"{self._get_url("databases")}{self.database_id}"
        try:
            response = self._get(url)
            if response.status_code == 200:
                data = response.json()
                for property_value in data["properties"]:
                    print(data["properties"][property_value])
        except Exception as e:
            return self._handle_error(e)
        return response

    def database_queue(self, filter = None):
        url = f"{self._get_url('databases')}{self.database_id}/query"
        output = {}
        try:
            payload = {"filter": {"and": [{"property": "Summary",
                    "checkbox": {
                        "equals": False
                    }},{"property": "Queued",
                    "checkbox": {
                        "equals": False
                    }}]}}
            if (filter is not None):
                payload = filter
            response = self._post(url, payload)
            if response.status_code == 200:
                data = response.json()
                # Add check for results
                if not data or "results" not in data:
                    print("Warning: No results found in response")
                    return output

                for item in data["results"]:
                    if not item or "properties" not in item:
                        print(f"Warning: Invalid item structure: {item}")
                        continue
                        
                    page = {}
                    page["id"] = item.get("id")
                    page["url"] = item.get("url")
                    page["database_id"] = self.database_id
                    
                    # Safer property access with default values
                    properties = item.get("properties", {})
                    date_prop = properties.get("Date", {})
                    date_value = date_prop.get("date", {})
                    page["date"] = date_value.get("start") if date_value else None
                    
                    page["summary"] = properties.get("Summary", {}).get("checkbox", False)

                    if page["date"] is None and "created_time" in item:
                        self.page_date_update(page["id"], item["created_time"][0:10])

                    if not page["summary"]:
                        page_str = json.dumps(page)
                        if self.queue is not None:
                            self.queue.put(page_str)
                            self.page_queued(page["id"])

                    content = properties.get("Content", {"title": []})
                    page["title"] = ""
                    for txt in content["title"]:
                        if txt["type"] == "text":
                            page["title"] += txt.get("text").get("content")
                    # Safer property access for Read and Abstract
                    read_prop = properties.get("Read", {"checkbox": True})
                    if read_prop is not True:
                        output[page["date"]] = output.get(page["date"], [])
                        description_pop = properties.get("Description", {"rich_text": []}) 
                        description = ""
                        for desc in description_pop["rich_text"]:
                            description += desc.get("plain_text","")
                        page["description"] = description

                        keywords = properties.get("Keywords", {"multi_select": []}) 
                        page["tag"] = ""
                        for keyword in keywords["multi_select"]:
                            page["tag"] += f" {keyword['name']}, "

                        abstract = ""
                        abstract_prop = properties.get("Abstract")
                        if abstract_prop is not None:
                            for chunk in abstract_prop.get("rich_text", []):
                                if isinstance(chunk, dict) and "text" in chunk:
                                    abstract += chunk["text"].get("content", "")
                            page["abstract"] = abstract
                            output[page["date"]].append(page)

            return output
        except Exception as e:
            return self._handle_error(e)
    
    def page_update(self, page_id, properties):
        url = f"{self._get_url("pages")}{page_id}"
        try:
            payload = {"properties": properties}
            response = self._patch(url, payload)
            if response.status_code != 200:
                raise Exception(response.json())
            return response

        except Exception as e:
            return self._handle_error(e)

    def page_date_update(self, page_id, date):
        try:
            payload = {"Date": {"type": "date","date": {"start": date}}}
            self.page_update(page_id, payload)
        except Exception as e:
            return self._handle_error(e)

    def page_queued(self, page_id):
        try:
            payload = {"Queued": {"type": "checkbox","checkbox": True }}
            self.page_update(page_id, payload)
        except Exception as e:
            return self._handle_error(e)

    def page_add_description(self, page_id, description, keywords = []):
        try:
            multi_select = []
            for kywrd in keywords:
                multi_select.append({"name": kywrd})

            payload = {"Keywords": {"type": "multi_select","multi_select": multi_select},
                    "Description": {"type": "rich_text","rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": description[:1990]
                    },
                    "plain_text": description[:1990]
                }
            ]}}
            self.page_update(page_id, payload)
        except Exception as e:
            return self._handle_error(e)

    def page_add_summary(self, page_id, summary):
        try:
            payload = {
                "Abstract": {"type": "rich_text","rich_text": [
                    *[{
                        "type": "text",
                        "text": {
                            "content": chunk
                        }
                    } for chunk in [summary[i:i+2000] for i in range(0, len(summary), 2000)]]
                ]},
                "Summary": {"type": "checkbox","checkbox": True }}
            self.page_update(page_id, payload)
        except Exception as e:
            return self._handle_error(e)