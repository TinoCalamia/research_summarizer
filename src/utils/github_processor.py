"""GitHub repository processing utilities."""

from github import Github
import base64
import streamlit as st
from typing import List, Dict
import tempfile
import os

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define a simple Document class
class Document:
    def __init__(self, content: str, metadata: Dict):
        self.page_content = content
        self.metadata = metadata

def process_github_repos() -> List[Document]:
    """
    Process GitHub repositories and return documents for indexing.
    """
    try:
        # Retrieve the token from secrets
        token = st.secrets["GITHUB_TOKEN"]
        logging.info("Using GitHub token for authentication.")

        # Use the token to authenticate with GitHub
        g = Github(token)
        logging.info("Authenticated with GitHub.")

        # Test authentication
        user = g.get_user()
        st.success(f"Successfully authenticated as {user.login}")
        logging.info(f"Authenticated as user: {user.login}")

        documents = []
        
        # Get user's repositories
        logging.info("Fetching repositories...")
        
        # Limit to specific repositories
        target_repos = ["sales_coach", "delish"]  # Specify the repositories to process
        
        for repo in g.get_user().get_repos():
            if repo.name in target_repos:  # Only process specified repositories
                logging.info(f"Processing repository: {repo.name}")
                try:
                    # Get all files recursively
                    contents = repo.get_contents("")
                    while contents:
                        file_content = contents.pop(0)
                        
                        if file_content.type == "dir":
                            contents.extend(repo.get_contents(file_content.path))
                        else:
                            # Filter for code files
                            if file_content.name.endswith(('.py', '.js', '.java', '.cpp', '.cs', '.go', '.rb', '.php')):
                                try:
                                    # Decode content
                                    content = base64.b64decode(file_content.content).decode('utf-8')
                                    logging.info(f"Processed file: {file_content.path}")

                                    # Create a Document object with metadata
                                    doc = Document(
                                        content=content,
                                        metadata={
                                            'repo': repo.name,
                                            'path': file_content.path,
                                            'language': file_content.name.split('.')[-1],
                                            'url': file_content.html_url
                                        }
                                    )
                                    documents.append(doc)
                                    
                                except Exception as e:
                                    st.warning(f"Could not process file {file_content.path}: {str(e)}")
                                    logging.error(f"Error processing file {file_content.path}: {str(e)}")
                                    continue
                except Exception as e:
                    st.warning(f"Could not process repository {repo.name}: {str(e)}")
                    logging.error(f"Error processing repository {repo.name}: {str(e)}")
                    continue
        
        logging.info(f"Processed {len(documents)} documents from GitHub.")
        return documents
        
    except Exception as e:
        st.error(f"Error accessing GitHub: {str(e)}")
        logging.error(f"Error accessing GitHub: {str(e)}")
        return [] 