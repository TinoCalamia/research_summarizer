"""
Document loader utilities for handling file imports.
"""

import os
import time
from typing import List
import streamlit as st
from langchain.docstore.document import Document
from langchain_community.document_loaders import (
    TextLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader
)
from langchain_community.document_loaders.pdf import PyPDFLoader

def load_folder_docs(folder_path: str = "src/documents") -> List[Document]:
    """
    Load all supported documents from a folder.
    
    Args:
        folder_path: Path to the documents folder
        
    Returns:
        List[Document]: List of loaded documents
    """
    documents = []
    
    # Create docs directory if it doesn't exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        st.warning(f"Created empty {folder_path} directory. Please add your documents.")
        return documents

    # Map file extensions to appropriate loaders
    LOADER_MAPPING = {
        ".txt": TextLoader,
        ".pdf": PyPDFLoader,
        ".docx": Docx2txtLoader,
        ".doc": Docx2txtLoader,
        ".md": UnstructuredMarkdownLoader
    }

    # Count total files
    supported_files = [f for f in os.listdir(folder_path) 
                      if os.path.splitext(f)[1].lower() in LOADER_MAPPING]
    
    if not supported_files:
        st.warning(f"No supported documents found in {folder_path}. "
                  f"Supported formats: {', '.join(LOADER_MAPPING.keys())}")
        return documents

    # Show loading progress
    with st.spinner(f"Loading {len(supported_files)} documents..."):
        for file in supported_files:
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path):
                file_extension = os.path.splitext(file)[1].lower()
                
                try:
                    loader = LOADER_MAPPING[file_extension](file_path)
                    loaded_docs = loader.load()
                    
                    # Validate loaded documents
                    if not loaded_docs:
                        st.warning(f"No content found in {file}")
                        continue
                        
                    # Validate document content
                    for doc in loaded_docs:
                        if not doc.page_content or len(doc.page_content.strip()) == 0:
                            st.warning(f"Empty content in {file}")
                            continue
                        documents.append(doc)
                                            
                except Exception as e:
                    st.error(f"Error loading {file}: {str(e)}")
                    continue

    # Final validation
    if not documents:
        st.error("No valid documents were loaded. Please check your files and try again.")
    else:
        with st.empty():
            success = st.success(f"Successfully loaded {len(documents)} documents")
            time.sleep(2)
            success.empty()

    return documents 