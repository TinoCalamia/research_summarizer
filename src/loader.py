from langchain_community.document_loaders import DirectoryLoader, TextLoader
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_folder_docs(directory="src/documents"):
    """Load documents from a directory with better error handling."""
    docs = []
    directory_path = Path(directory)
    
    if not directory_path.exists():
        logger.error(f"Directory {directory} does not exist")
        return []
    
    # Load each file individually instead of using DirectoryLoader
    for file_path in directory_path.glob("*.txt"):
        try:
            loader = TextLoader(str(file_path), encoding='utf-8')
            file_docs = loader.load()
            docs.extend(file_docs)
            logger.info(f"Successfully loaded {file_path}")
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {str(e)}")
            continue
    
    if not docs:
        logger.warning("No documents were successfully loaded")
    else:
        logger.info(f"Successfully loaded {len(docs)} documents")
    
    return docs