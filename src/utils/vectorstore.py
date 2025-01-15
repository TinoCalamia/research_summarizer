"""
Vector store utilities for document processing and storage.
"""

from typing import List
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document

def split_documents(documents: List[Document]) -> List[Document]:
    """
    Split documents into smaller chunks for processing.
    
    Args:
        documents: List of documents to split
        
    Returns:
        List[Document]: Split documents
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    
    return splitter.split_documents(documents)

def create_vectorstore_from_documents(documents: List[Document]) -> FAISS:
    """
    Create a FAISS vector store from documents.
    
    Args:
        documents: List of documents to process
        
    Returns:
        FAISS: Vector store containing document embeddings
    """
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(documents, embeddings)
    
    return vectorstore 