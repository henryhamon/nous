import os
import re
from dotenv import load_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.docstore.document import Document

load_dotenv()
LLM = os.getenv('LLM', 'ollama') 

if (LLM == 'ollama'):
    from langchain_ollama.llms import OllamaLLM
elif (LLM == 'openai'):
    from langchain_openai import ChatOpenAI
elif (LLM == 'azure_openai'):
    from langchain_openai import AzureChatOpenAI

class ThemeExtractor:
    MAX_THEME_LENGTH = 1981
    
    def __init__(self, model_name=None):
        load_dotenv()
        self.model_name = model_name or os.getenv("LLM_MODEL")
        if not self.model_name:
            raise ValueError("Model name must be provided either directly or through LLM_MODEL environment variable")
        
        # Initialize LLM with error handling
        try:
            if (LLM == 'ollama'):
                self.llm = OllamaLLM(model=self.model_name)
            elif (LLM == 'openai'):
                api_key = os.getenv("LLM_APIKEY")
                if not api_key:
                    raise ValueError("API key not found in environment variables")
                self.llm = ChatOpenAI(model=self.model_name, api_key=api_key)
            elif (LLM == 'azure_openai'):
                api_key = os.getenv("LLM_APIKEY")
                if not api_key:
                    raise ValueError("API key not found in environment variables")
                self.llm = AzureChatOpenAI(model=self.model_name, api_key=api_key)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize LLM: {str(e)}")
        
        # Define theme extraction prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "**You are a text analysis expert.**   \n"
            "Analyze the given text and determine its main theme with a focus on factual content.  \n"
            "Identify the core subject matter, summarize it concisely, and extract key terms that  \n"
            "best represent the text's primary focus. Ignore minor details and peripheral topics.   \n\n"
            "### **Instructions:**   \n"
            "1. Read the given text carefully.   \n"
            "2. Identify the central idea or overarching topic.   \n"
            "3. Summarize the main theme in a **clear and concise phrase or sentence** (maximum **200 characters**).   \n"
            "4. Extract **3-5 important keywords or key phrases** that best represent the text.   \n"
            "   - Keep each keyword between **1-3 words**.   \n"
            "   - Do not rank or categorize them.   \n\n"
            "### **Output Format:**   \n\n"
            "``` \n"
            "**Main Theme:** [Concise theme description]   \n"
            "**Keywords:**   \n"
            "keyword1   \n"
            "keyword2   \n\n"
            "``` \n"
            "**Text:** \n\n{context} \n\n"
            "--- \n"
            " ")
        ])
        
    def extract_themes(self, text_string):
        # Split text into chunks and create Document objects
        text_chunks = text_string.split(" \n ")
        docs = [Document(page_content=chunk) for chunk in text_chunks if chunk.strip()]
        
        # Create and invoke chain
        chain = create_stuff_documents_chain(self.llm, self.prompt)
        result = chain.invoke({"context": docs})
        # Split result into theme and keywords sections
        theme_section = ""
        keywords = ""
        
        # Extract theme and keywords using regex
        match = re.search("\\*\\*Main Theme:\\*\\*(.*?)\\*\\*Keywords:\\*\\*(.*)", result, re.DOTALL)
        
        if match:
            theme_section = match.group(1).strip()
            keywords = match.group(2).strip()
            # Split keywords by comma, newline or bullet points
            keywords = [k.strip('- ') for k in re.split(r',|\n|- ', keywords) if k.strip('- ')]
        else:
            # Fallback if pattern not found
            theme_section = result
            keywords = ""

        
        return {
            "theme": theme_section[:self.MAX_THEME_LENGTH],
            "keywords": keywords
        }