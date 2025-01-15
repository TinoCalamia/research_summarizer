"""
Research Summarizer page functionality.
"""

import streamlit as st
from typing import List, Dict, Any
from src.components.document_selector import DocumentSelector
from src.ui.components.chat_interface import ChatInterface
from src.utils import split_documents, create_vectorstore_from_documents, create_conversation_chain
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_summarizer():
    """Display the research summarizer interface."""
    st.title("Research Summarizer 📚")

    # Initialize session state variables
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = None
    if "previous_selection" not in st.session_state:
        st.session_state.previous_selection = set(st.session_state.document_names)  # Initialize with all documents
    if "document_selection" not in st.session_state:
        st.session_state.document_selection = set(st.session_state.document_names)  # Initialize with all documents
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Document selection with all pre-selected
    selected_docs = DocumentSelector.show_selector(st.session_state.document_names)

    if not selected_docs:
        st.warning("Please select at least one document")
        st.session_state.vector_store = None
        return

    # Handle document selection changes
    if not st.session_state.vector_store or selected_docs != st.session_state.previous_selection:
        # Validate documents exist
        if not st.session_state.all_documents:
            st.error("No documents loaded. Please add documents to the 'docs' folder.")
            return
            
        # Initialize vector store with selected documents
        filtered_docs = [
            doc for doc in st.session_state.all_documents 
            if doc.metadata.get('source', '').split('/')[-1] in selected_docs
        ]
        
        if not filtered_docs:
            st.error("No valid documents found after filtering.")
            return
            
        splitted_docs = split_documents(filtered_docs)
        if not splitted_docs:
            st.error("No content found after splitting documents.")
            return
            
        try:
            st.session_state.vector_store = create_vectorstore_from_documents(splitted_docs)
            st.session_state.previous_selection = selected_docs
        except Exception as e:
            st.error(f"Error creating vector store: {str(e)}")
            return

    # Chat interface
    ChatInterface.show_input_guidelines()
    user_question = ChatInterface.get_user_input()
    
    if user_question and "chat_history" in st.session_state:
        rag_chain = create_conversation_chain(st.session_state.vector_store, st.session_state.llm)
        handle_user_input(user_question, rag_chain)
        
        # Display chat history
        ChatInterface.display_chat_history(st.session_state.chat_history)

def handle_user_input(user_question: str, rag_chain: Any):
    """
    Process user input and generate response using the RAG chain.
    
    Args:
        user_question: User's input question
        rag_chain: Configured RAG chain for generating responses
    """
    try:
        # Log the incoming question
        logger.info(f"Processing question: {user_question}")

        # Check if this question was already asked to prevent duplicates
        if st.session_state.chat_history and st.session_state.chat_history[-1][0] == user_question:
            logger.info("Duplicate question detected, skipping processing")
            return

        # Log chat history state
        logger.info(f"Current chat history length: {len(st.session_state.chat_history)}")

        # Generate response
        logger.info("Generating response from RAG chain")
        response = rag_chain({
            "question": user_question,
            "chat_history": [(q, a) for q, a in st.session_state.chat_history]
        })
        
        # Log the raw response for debugging
        logger.info(f"Raw response from chain: {response}")
        
        # Extract answer from the response
        if isinstance(response, dict):
            logger.info("Response is a dictionary")
            if "answer" in response:
                answer = response["answer"]
                logger.info("Found answer in response dictionary")
            else:
                logger.warning("No 'answer' key in response dictionary")
                answer = str(response)
        else:
            logger.warning(f"Unexpected response type: {type(response)}")
            answer = str(response)
            
        if not answer or answer.strip() == "":
            logger.warning("Empty answer received")
            answer = "I'm sorry, I couldn't generate a response."
        
        # Log the final answer
        logger.info(f"Final processed answer: {answer[:100]}...")  # Log first 100 chars
        
        # Update chat history
        st.session_state.chat_history.append((user_question, answer))
        logger.info("Chat history updated successfully")
        
        # Update memory if it exists
        if hasattr(st.session_state, 'memory'):
            logger.info("Updating memory context")
            st.session_state.memory.save_context(
                {"input": user_question},
                {"output": answer}
            )
            
    except Exception as e:
        error_msg = f"Error processing question: {str(e)}"
        st.error(error_msg)
        # Only append to chat history if it's not already there
        if not st.session_state.chat_history or st.session_state.chat_history[-1][0] != user_question:
            st.session_state.chat_history.append(
                (user_question, f"Sorry, there was an error processing your question. Please try again.")
            )

def process_document_changes(selected_docs: set):
    """
    Process changes in document selection.
    
    Args:
        selected_docs: Currently selected documents
    """
    try:
        filtered_docs = [
            doc for doc in st.session_state.all_documents 
            if doc.metadata.get('source', '').split('/')[-1] in selected_docs
        ]
        
        if filtered_docs:
            splitted_docs = split_documents(filtered_docs)
            st.session_state.vector_store = create_vectorstore_from_documents(splitted_docs)
        else:
            st.session_state.vector_store = None
        
        st.session_state.previous_selection = selected_docs
        
    except Exception as e:
        st.error(f"Error updating document selection: {str(e)}")
        st.session_state.vector_store = None 