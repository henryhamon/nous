
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

 ```sh
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_notion_database_id
 ```

### 4.	Run the application:

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

