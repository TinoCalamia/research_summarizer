from typing import List
from langchain.vectorstores import FAISS
import logging

logger = logging.getLogger(__name__)

def merge_vectorstores(vectorstores: List[FAISS]) -> FAISS:
    """
    Merges multiple FAISS vector stores into a single one.
    
    Args:
        vectorstores (List[FAISS]): List of FAISS vector stores to merge
        
    Returns:
        FAISS: A merged vector store containing all documents
    """
    if not vectorstores:
        logger.warning("No vector stores provided for merging")
        return None
        
    if len(vectorstores) == 1:
        return vectorstores[0]
        
    try:
        # Get the embedding function from the first vector store
        embeddings = vectorstores[0]._embedding_function
        
        # Combine all documents
        all_docs = []
        for store in vectorstores:
            all_docs.extend(store.docstore._dict.values())
            
        # Create new vector store with all documents
        merged_store = FAISS.from_documents(all_docs, embeddings)
        
        logger.info(f"Successfully merged {len(vectorstores)} vector stores with {len(all_docs)} total documents")
        return merged_store
        
    except Exception as e:
        logger.error(f"Error merging vector stores: {str(e)}")
        raise 