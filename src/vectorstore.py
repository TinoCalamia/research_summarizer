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

def create_vectorstore_from_documents(documents, vectorstore=vector_store, embedding=embeddings):
    # Embed and add documents to vector store
    vector_db = vectorstore.from_documents(documents=documents, embedding=embedding)
    return vector_db

def split_documents(documents):
    # Define the text splitter for chunking with constants from `con`
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=con.SPLITTER_CHUNK_SIZE,
        chunk_overlap=con.SPLITTER_CHUNK_OVERLAP
    )
    # Split the documents into chunks
    splitted_documents = text_splitter.split_documents(documents)
    return splitted_documents

def add_documents_to_vectorstore(splitted_documents, vector_db=vector_store):
    # Add split documents to the vector store
    id_list = vector_db.add_documents(splitted_documents)
    return id_list
