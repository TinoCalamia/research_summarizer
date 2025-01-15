"""
Chain utilities for conversation and document processing.
"""

from langchain.chains import ConversationalRetrievalChain
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS

def create_conversation_chain(vectorstore: FAISS, llm: ChatOpenAI) -> ConversationalRetrievalChain:
    """
    Create a conversational chain for document Q&A.
    
    Args:
        vectorstore: FAISS vector store containing document embeddings
        llm: Language model instance
        
    Returns:
        ConversationalRetrievalChain: Chain for processing conversations
    """
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        return_source_documents=True,
        return_generated_question=True,
        verbose=True,
        max_tokens_limit=4000,
        combine_docs_chain_kwargs={"prompt": None}  # Use default prompt
    ) 