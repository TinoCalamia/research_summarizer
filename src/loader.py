import os
from langchain_community.document_loaders import DirectoryLoader, UnstructuredFileLoader

import src.constants as con

def load_folder_docs(path=os.path.join(os.getcwd(), 'src', 'documents')):
    # Use UnstructuredFileLoader for .txt files
    loader = DirectoryLoader(path, glob="*.txt", use_multithreading=True, loader_cls=UnstructuredFileLoader)

    docs = loader.load()

    return docs
