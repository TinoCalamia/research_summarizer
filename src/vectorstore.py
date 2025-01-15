import os
import faiss
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter  # for efficient splitting

import src.constants as con


# Initialize embeddings and FAISS index
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
embedding_dim = len(embeddings.embed_query("hello world"))

index = faiss.IndexFlatL2(embedding_dim)  # FAISS index
vector_store = FAISS(
    embedding_function=embeddings,
    index=index,
    docstore=InMemoryDocstore(),
    index_to_docstore_id={},
)

def create_vectorstore_from_documents(documents, vectorstore=vector_store, embedding=embeddings, batch_size=3):
    # Process documents in batches to prevent memory issues
    vector_db = None
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        print(batch)
        try:
            if vector_db is None:
                vector_db = vectorstore.from_documents(documents=batch, embedding=embedding)
            else:
                vector_db.add_documents(batch)
        except Exception as e:
            print(f"Error processing batch {i//batch_size}: {str(e)}")
            continue
    
    return vector_db

def split_documents(documents, batch_size=100):
    # Define the text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=con.SPLITTER_CHUNK_SIZE,
        chunk_overlap=con.SPLITTER_CHUNK_OVERLAP
    )
    
    # Process documents in batches
    all_splits = []
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        try:
            splits = text_splitter.split_documents(batch)
            all_splits.extend(splits)
        except Exception as e:
            print(f"Error splitting batch {i//batch_size}: {str(e)}")
            continue
    
    return all_splits

def add_documents_to_vectorstore(splitted_documents, vector_db=vector_store, batch_size=50):
    id_lists = []
    
    # Add documents in batches
    for i in range(0, len(splitted_documents), batch_size):
        batch = splitted_documents[i:i + batch_size]
        try:
            ids = vector_db.add_documents(batch)
            id_lists.extend(ids)
        except Exception as e:
            print(f"Error adding batch {i//batch_size}: {str(e)}")
            continue
    
    return id_lists