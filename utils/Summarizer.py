import os
from typing import Optional
from dotenv import load_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.docstore.document import Document

load_dotenv()

SUPPORTED_LLMS = {'ollama', 'openai', 'azure_openai'}
LLM = os.getenv('LLM', 'ollama')

if LLM not in SUPPORTED_LLMS:
    raise ValueError(f"Unsupported LLM type. Must be one of {SUPPORTED_LLMS}")

# Import based on LLM type
if (LLM == 'ollama'):
    from langchain_ollama.llms import OllamaLLM
elif (LLM == 'openai'):
    from langchain_openai import ChatOpenAI
elif (LLM == 'azure_openai'):
    from langchain_openai import AzureChatOpenAI

class TextSummarizer:
    def __init__(self):
        self.model_name = os.getenv("LLM_MODEL")
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
        
        # Define default prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an academic research expert. \n"
            "Produce a concise and clear summary that encapsulates the main findings, questions, evidences, methodology, results, and implications of the study. \n"
            "Ensure that the summary is written in a manner that is accessible to a general audience while retaining the core insights and nuances of the original paper. "
            "Include key terms and concepts, and provide any necessary context or background information. "
            "The summary should serve as a standalone piece that gives readers a comprehensive understanding of the text's significance without needing to read the entire document.\n\n{context}")
        ])
        
    def summarize(self, text_string: str) -> str:
        if not isinstance(text_string, str):
            raise TypeError("Input must be a string")
        
        if not text_string.strip():
            raise ValueError("Input text cannot be empty")
        
        try:
            # Split text into chunks and create Document objects
            text_chunks = text_string.split(" \n ")
            docs = [Document(page_content=chunk) for chunk in text_chunks if chunk.strip()]
            
            if not docs:
                raise ValueError("No valid text chunks found after processing")
            
            # Create and invoke chain
            chain = create_stuff_documents_chain(self.llm, self.prompt)
            result = chain.invoke({"context": docs})
            return result
        except Exception as e:
            raise RuntimeError(f"Error during text summarization: {str(e)}")