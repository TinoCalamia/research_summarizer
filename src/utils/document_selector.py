import os
import logging
from typing import List
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader

logger = logging.getLogger(__name__)

class DocumentSelector:
    def __init__(self):
        # Set the correct base path to src/documents
        self.base_path = Path("src/documents")
        logger.info(f"Initialized DocumentSelector with base path: {self.base_path}")
        
    def get_available_folders(self) -> List[str]:
        """Get list of available folders in the documents directory."""
        try:
            # Ensure base_path exists
            if not self.base_path.exists():
                logger.warning(f"Base path {self.base_path} does not exist")
                return []
                
            # Get all directories in the base path
            folders = [f.name for f in self.base_path.iterdir() if f.is_dir()]
            logger.info(f"Found {len(folders)} available folders: {', '.join(folders)}")
            return folders
        except Exception as e:
            logger.error(f"Error getting available folders: {str(e)}")
            return []
            
    def load_documents_from_folder(self, folder_name: str) -> List:
        """Load all documents from a specific folder."""
        folder_path = self.base_path / folder_name
        logger.info(f"Loading documents from: {folder_path}")
        
        try:
            # Use DirectoryLoader to load all text files in the folder
            loader = DirectoryLoader(
                str(folder_path),
                glob="**/*.txt",  # Load all .txt files
                loader_cls=TextLoader,
                show_progress=True
            )
            documents = loader.load()
            logger.info(f"Successfully loaded {len(documents)} documents from {folder_name}")
            return documents
            
        except Exception as e:
            logger.error(f"Error loading documents from {folder_name}: {str(e)}")
            raise
            
    def get_document_paths(self, folder_name: str) -> List[str]:
        """Get list of document paths in a folder."""
        try:
            folder_path = self.base_path / folder_name
            logger.info(f"Searching for documents in: {folder_path}")
            
            if not folder_path.exists():
                logger.error(f"Folder path does not exist: {folder_path}")
                return []
            
            # Get all .txt files in the folder
            paths = list(folder_path.glob("*.txt"))
            
            # Log found files
            logger.info(f"Found {len(paths)} documents in {folder_name}:")
            for path in paths:
                logger.info(f"- {path.name}")
            
            # Return list of paths as strings
            return [str(path) for path in paths]
            
        except Exception as e:
            logger.error(f"Error getting document paths from {folder_name}: {str(e)}")
            logger.exception("Detailed error:")  # This will log the full traceback
            return []