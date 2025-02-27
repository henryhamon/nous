
# Nous

Nous is a personal project designed to enhance productivity by leveraging Large Language Models (LLMs) with LangChain to summarize articles on Notion. It extracts key topics, keywords, and main ideas, helping to filter out irrelevant content and build a structured knowledge base—a "second brain."

## Features

- **Automatic Summarization**: Extracts the essence of articles added to Notion.  
- **Topic & Keyword Extraction**: Identifies the main subjects and important terms.  
- **Content Organization**: Categorizes and structures information for easy reference.  
- **Feed Integration**: Allows adding articles directly from your feed for processing.  

## Tech Stack

- **Python 3.9**  
- **LangChain**: LLM orchestration and processing.  
- **Notion API**: Storing and organizing article summaries.  
- **LiteQueue**: Lightweight task queue for managing article processing.
- **python-dotenv**: Manages environment variables.  

## Setup

### 1. Clone the repository:

   ```sh
   git clone https://github.com/henryhamon/nous.git
   cd nous
```

### 2.	Create a virtual environment and install dependencies:

 ```sh
python3.9 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 3.	Set up environment variables:

Create a .env file in the root directory and add your credentials

 ```yaml
NOTION_TOKEN=your_notion_api_key
NOTION_DATABASE_ID=your_notion_database_id
LLM=ollama # or anthropic, google, llama
LLM_MODEL=llama3
LLM_APIKEY=nonononononnonono
 ```

### 3.1. Configure Schedule Interval

Set the `SCHEDULE_INTERVAL` in your `.env` file to control how often the application checks for new articles. Available options are:

| Interval | Value | Description |
|----------|--------|-------------|
| 10 minutes | `10min` | Checks every 10 minutes |
| 25 minutes | `25min` | Checks every 25 minutes |
| Hourly | `hourly` | Checks once every hour (default) |
| Every 2 hours | `2hours` | Checks every 2 hours |
| Daily | `daily` | Checks once per day |

Example:

 ```yaml
SCHEDULE_INTERVAL=10min
 ```

### 4. Create a Notion Database

You must create a database on Notion with the following properties:

| Property Name | Type |
|--------------|------|
| Content | Text |
| Date | Date |
| Keywords | Multi-select |
| Description | Text |
| Summary | Checkbox |
| Abstract | Text |
| URL | URL |
| Read | Checkbox |

	1.	Open Notion and create a new database.
	2.	Add the properties listed above.
	3.	Copy the Database ID from the URL (it appears after notion.so/ and before the question mark).


### 5.	Run the application:

 ```sh

python main.py

 ```

## Roadmap

	•	Implement feed parsing for automated article collection.
	•	Enhance summarization using fine-tuned models.
	•	Improve UI/UX for interacting with collected summaries.
	•	Add support for multiple knowledge bases.
	•	Future Integration: Obsidian – Export summaries and structured data to Obsidian for deeper personal knowledge management.

## Contributing

Feel free to contribute by submitting issues or pull requests. Any suggestions to improve Nous are welcome!

