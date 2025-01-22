"""
Research Summarizer page functionality.
"""

import streamlit as st
from typing import List, Dict, Any
from src.utils.document_selector import DocumentSelector
from src.ui.components.chat_interface import ChatInterface
from src.utils import split_documents, create_vectorstore_from_documents, create_conversation_chain
from langchain_openai import ChatOpenAI
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

NEEDS_ANALYSIS_PROMPT = """Please analyze the provided research documents and identify underserved needs following these steps:

1. Identify pain points and challenges mentioned by users
2. Analyze the frequency and severity of these pain points
3. Highlight needs that are currently not being met or inadequately addressed
4. Consider both explicit needs (directly stated) and implicit needs (implied from behavior or context)
5. Prioritize needs based on:
   - Number of users affected
   - Severity of the problem
   - Current lack of solutions
6. Group related needs into themes or categories
7. Provide specific quotes or evidence from the research to support each identified need

Please present your findings in a clear, structured format with specific examples from the research documents.
In your output, include the following:
- A list of the identified needs, including the number of users affected and the severity of the problem
- A summary of the identified needs, including the number of users affected and the severity of the problem
- A list of opportunities to address the needs.
"""

def format_folder_name(folder_name: str) -> str:
    """Convert folder names from snake_case to Title Case."""
    return folder_name.replace('_', ' ').title()

def show_summarizer():
    """Display the research summarizer interface."""
    st.title("Research Summarizer")

    # Initialize session states
    if "documents" not in st.session_state:
        st.session_state.documents = None
    if "analysis_mode" not in st.session_state:
        st.session_state.analysis_mode = None
    if "chat_started" not in st.session_state:
        st.session_state.chat_started = False

    # Initialize document selector
    doc_selector = DocumentSelector()
    
    try:
        # Get available folders
        available_folders = doc_selector.get_available_folders()
        
        if not available_folders:
            st.warning("No folders found in the data directory.")
            return
            
        # Create formatted folder options for the dropdown with exact mapping
        folder_options = {}
        for folder in available_folders:
            display_name = format_folder_name(folder)
            folder_options[display_name] = folder
            logger.info(f"Mapping display name '{display_name}' to folder '{folder}'")
        
        # Single select dropdown that collapses after selection
        selected_folder = st.selectbox(
            "Select a folder to load documents from:",
            options=sorted(list(folder_options.keys())),
            index=0,
            key="folder_selector"
        )

        # Load documents button
        if st.button("Load Selected Documents"):
            if not selected_folder:
                st.warning("Please select a folder.")
                return
                
            folder = folder_options[selected_folder]
            logger.info(f"Selected folder mapping - Display: '{selected_folder}' -> Folder: '{folder}'")
            
            try:
                logger.info(f"Loading documents from folder: {folder}")
                documents = doc_selector.load_documents_from_folder(folder)
                logger.info(f"Successfully loaded {len(documents)} documents from {folder}")
                    
                st.session_state.documents = documents
                st.session_state.analysis_mode = None  # Reset analysis mode
                st.session_state.chat_started = False  # Reset chat state
                st.success(f"Successfully loaded {len(documents)} documents from folder")
                st.experimental_rerun()  # Rerun to show the buttons
                
            except Exception as e:
                logger.error(f"Error loading documents: {str(e)}")
                st.error(f"Error loading documents: {str(e)}")
                return

        # Show options only if documents are loaded
        if st.session_state.documents:
            st.markdown("---")
            st.markdown("### Choose Your Analysis Option")
            
            # Create two columns for the buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Analyze Underserved Needs", key="analyze_needs"):
                    st.session_state.analysis_mode = "needs"
                    st.session_state.chat_started = True
                    st.experimental_rerun()
                    
            with col2:
                if st.button("Chat with Documents", key="direct_chat"):
                    st.session_state.analysis_mode = "chat"
                    st.session_state.chat_started = True
                    st.experimental_rerun()
            
            # Show the appropriate interface based on selection
            if st.session_state.chat_started:
                st.markdown("---")
                
                # Initialize chat interface and required components
                if 'chat_history' not in st.session_state:
                    st.session_state.chat_history = []
                
                # Create RAG components if not already in session state
                if 'conversation_chain' not in st.session_state:
                    with st.spinner('Setting up chat system...'):
                        try:
                            documents = st.session_state.documents
                            split_docs = split_documents(documents)
                            vectorstore = create_vectorstore_from_documents(split_docs)
                            
                            # Initialize the LLM
                            llm = ChatOpenAI(
                                temperature=0,
                                model="gpt-4o",
                                streaming=True
                            )
                            
                            # Create conversation chain with LLM
                            st.session_state.conversation_chain = create_conversation_chain(vectorstore, llm)
                        except Exception as e:
                            logger.error(f"Error creating conversation chain: {str(e)}")
                            st.error(f"Error setting up chat: {str(e)}")
                            return

                # Initialize chat interface with the conversation chain
                chat_interface = ChatInterface()
                
                if st.session_state.analysis_mode == "needs":
                    st.markdown("#### Analyzing Underserved Needs")
                    # Send the needs analysis prompt if not already sent
                    if not st.session_state.get('needs_analysis_sent'):
                        with st.spinner('Analyzing research documents for underserved needs...'):
                            try:
                                # Process the needs analysis prompt
                                response = st.session_state.conversation_chain({
                                    "question": NEEDS_ANALYSIS_PROMPT,
                                    "chat_history": []
                                })
                                
                                # Extract answer and update chat history
                                answer = response["answer"] if isinstance(response, dict) and "answer" in response else str(response)
                                st.session_state.chat_history.append((NEEDS_ANALYSIS_PROMPT, answer))
                                st.session_state.needs_analysis_sent = True
                                
                            except Exception as e:
                                logger.error(f"Error processing needs analysis: {str(e)}")
                                st.error(f"Error analyzing needs: {str(e)}")
                    
                else:  # Direct chat mode
                    st.markdown("#### Chat with Documents")
                
                # Display chat messages
                for message in st.session_state.chat_history:
                    user_msg, assistant_msg = message
                    with st.chat_message("user"):
                        st.write(user_msg)
                    with st.chat_message("assistant"):
                        st.write(assistant_msg)
                
                # Chat input
                if prompt := st.chat_input("Ask a follow-up question"):
                    with st.chat_message("user"):
                        st.write(prompt)
                    
                    with st.spinner('Processing...'):
                        try:
                            response = st.session_state.conversation_chain({
                                "question": prompt,
                                "chat_history": st.session_state.chat_history
                            })
                            answer = response["answer"] if isinstance(response, dict) and "answer" in response else str(response)
                            
                            with st.chat_message("assistant"):
                                st.write(answer)
                            
                            st.session_state.chat_history.append((prompt, answer))
                            
                        except Exception as e:
                            logger.error(f"Error processing question: {str(e)}")
                            st.error(f"Error processing question: {str(e)}")
                
        elif not st.session_state.documents and st.session_state.get('chat_history'):
            # Clear chat history if no documents are loaded
            st.session_state.chat_history = []
            
    except Exception as e:
        logger.error(f"Error in show_summarizer: {str(e)}")
        st.error(f"An error occurred: {str(e)}")

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