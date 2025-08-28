import os 

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_mistralai.chat_models import ChatMistralAI


import numpy as np
if not hasattr(np, 'float_'):
    np.float_ = np.float64
if not hasattr(np, 'int_'):
    np.int_ = np.int64 

def setup_llm(): 
    llm = ChatMistralAI(api_key="lHcwga2vJ6yyjV470WdMIFn5hRgtMbcc")
    return llm

def create_document_chunks(transcript):
    """Split transcript into smaller chunks"""
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.create_documents([transcript])  
    return chunks
