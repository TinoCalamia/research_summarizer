"""
Vector store utilities for document processing and storage.
"""

from typing import List
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS

def split_documents(documents: List[Document]) -> List[Document]:
    """
    Split documents into smaller chunks for processing.
    
    Args:
        documents: List of documents to split
        
    Returns:
        List[Document]: Split documents
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
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

def merge_vectorstores(vectorstores):
    """
    Merges multiple vector stores into a single FAISS vector store.
    
    Args:
        vectorstores (list): List of FAISS vector stores to merge.
    
    Returns:
        FAISS: A new FAISS vector store containing all documents from the input stores.
    """
    if not vectorstores:
        raise ValueError("No vector stores provided for merging.")

    # Create a new FAISS index
    merged_index = FAISS()

    for vectorstore in vectorstores:
        # Add all documents from the current vector store to the merged index
        merged_index.add_documents(vectorstore.get_documents())

    return merged_index 