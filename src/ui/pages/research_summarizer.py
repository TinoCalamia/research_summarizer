"""
Research Summarizer page functionality.
"""

import streamlit as st
from typing import List, Dict, Any
from src.utils.document_selector import DocumentSelector
from src.utils.vectorstore import split_documents, create_vectorstore_from_documents
from langchain.chat_models import ChatOpenAI
import logging
from pathlib import Path
from src.utils.chain import create_conversation_chain

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

MEETING_SUMMARY_PROMPT = """Please analyze the interview/meeting documents and provide a structured summary following these categories. For each question, provide the answer if available in the documents, or explicitly state if the question wasn't addressed.

## 0. Interview/ICP Framing
1. Company Information:
   - Number of employees
   - Annual revenue
   - Biggest teams
   - Main geographic markets
2. Role Information:
   - Role responsibilities
   - Team structure/hierarchy
   - Number of direct reports

## 1. Strategic Challenges and Opportunities
- Primary strategic objectives for 2025
- Current organizational challenges
- Time-consuming or cumbersome tasks
- Emerging opportunities
- Balance between short-term and long-term goals
- Priority metrics for strategy evaluation
- Mechanisms for continuous learning and team agility

## 2. Decision-Making and Problem-Solving
- Recent complex decision example
- Success factors
- Insights and potential different approaches

## 3. Future Outlook
- Role of emerging technologies (AI, digital transformation)
- Significant industry trends (3-5 years)
- Organizational preparation for trends

## 4. Innovation and Adaptability
- Organization's innovation culture
- Example of successful adaptability

For each section, please:
1. Provide direct quotes where relevant
2. Clearly indicate if any question wasn't addressed in the interview
3. Highlight particularly insightful or unique responses
4. Note any patterns or themes across different topics
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
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "selected_file_for_summary" not in st.session_state:
        st.session_state.selected_file_for_summary = None
    if "show_file_selector" not in st.session_state:
        st.session_state.show_file_selector = False
    if "current_folder" not in st.session_state:
        st.session_state.current_folder = None
    if "conversation_chain" not in st.session_state:
        st.session_state.conversation_chain = None
    if "vectorstore" not in st.session_state:
        st.session_state.vectorstore = None
    if "unique_files" not in st.session_state:
        st.session_state.unique_files = None

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
            options=[""] + sorted(list(folder_options.keys())),
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
                
                # Create vectorstore using existing function
                vectorstore = create_vectorstore_from_documents(documents)
                
                # Store everything in session state
                st.session_state.documents = documents
                st.session_state.current_folder = folder
                st.session_state.vectorstore = vectorstore
                st.session_state.analysis_mode = None
                st.session_state.chat_started = False
                st.session_state.chat_messages = []
                
                st.success(f"Successfully loaded {len(documents)} documents from folder")
                st.rerun()
                
            except Exception as e:
                logger.error(f"Error loading documents: {str(e)}")
                st.error(f"Error loading documents: {str(e)}")
                return

        # Show options only if documents are loaded
        if st.session_state.documents:
            st.markdown("---")
            st.markdown("### Choose Your Analysis Option")
            
            # Create three columns for the buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Analyze Underserved Needs", key="analyze_needs"):
                    # Initialize conversation chain using existing vectorstore
                    llm = ChatOpenAI(temperature=0, model_name="gpt-4o")
                    st.session_state.conversation_chain = create_conversation_chain(
                        vectorstore=st.session_state.vectorstore,
                        llm=llm,
                    )

                    # Print unique file names from vectorstore
                    print(st.session_state.vectorstore.docstore.__dict__.values())
                    docs = st.session_state.vectorstore.docstore._dict.values()
                    unique_files = set()
                    for doc in docs:
                        source = doc.metadata.get('source', '')
                        if source:
                            unique_files.add(Path(source).name)
                            
                    st.session_state.unique_files = unique_files
                    st.session_state.analysis_mode = "needs"
                    st.session_state.chat_started = True
                    st.session_state.show_file_selector = False
                    st.session_state.chat_messages = [{"role": "user", "content": NEEDS_ANALYSIS_PROMPT}]
                    st.rerun()
                    
            with col2:
                if st.button("Summarize Meeting", key="summarize_meeting"):
                    st.session_state.analysis_mode = "meeting"
                    st.session_state.show_file_selector = True
                    st.session_state.selected_file_for_summary = None
                    st.session_state.chat_started = False
                    st.rerun()
                    
            with col3:
                if st.button("Chat with Documents", key="direct_chat"):
                    # Initialize conversation chain using existing vectorstore
                    llm = ChatOpenAI(temperature=0, model_name="gpt-4o")
                    st.session_state.conversation_chain = create_conversation_chain(
                        vectorstore=st.session_state.vectorstore,
                        llm=llm,
                    )
                    st.session_state.analysis_mode = "chat"
                    st.session_state.chat_started = True
                    st.session_state.show_file_selector = False
                    st.session_state.chat_messages = []
                    st.rerun()
            
            # Show file selector for meeting summary
            if st.session_state.show_file_selector and st.session_state.current_folder:
                st.markdown("---")
                st.markdown("#### Select Meeting to Summarize")
                
                try:
                    # Get files from the current folder
                    file_paths = doc_selector.get_document_paths(st.session_state.current_folder)
                    
                    if not file_paths:
                        st.warning(f"No text files found in folder: {st.session_state.current_folder}")
                        return
                    
                    # Extract file names from paths
                    file_names = [Path(path).name for path in file_paths]
                    logger.info(f"Available files: {file_names}")
                    
                    selected_file = st.selectbox(
                        "Choose a meeting file to summarize:",
                        options=file_names,
                        key="meeting_file_selector"
                    )
                    
                    # Start analysis button
                    if st.button("Start Summary", key="start_summary"):
                        try:
                            logger.info(f"Looking for document with filename: {selected_file}")
                            # Find the selected document
                            selected_doc = None
                            for doc in st.session_state.documents:
                                doc_path = doc.metadata.get('source', '')
                                if not doc_path:
                                    doc_path = doc.metadata.get('path', '')
                                
                                if doc_path and Path(doc_path).name == selected_file:
                                    selected_doc = doc
                                    break
                            
                            if selected_doc is None:
                                raise ValueError(f"Could not find document for file: {selected_file}")
                            
                            logger.info(f"Successfully found document for file: {selected_file}")
                            
                            # Initialize conversation chain using existing vectorstore
                            llm = ChatOpenAI(temperature=0, model_name="gpt-4o")
                            st.session_state.conversation_chain = create_conversation_chain(
                                vectorstore=create_vectorstore_from_documents([selected_doc]),
                                llm=llm,
                            )
                            
                            # Store the selected document and start chat
                            st.session_state.selected_file_for_summary = selected_doc
                            st.session_state.chat_started = True
                            st.session_state.show_file_selector = False
                            st.session_state.chat_messages = [{
                                "role": "user", 
                                "content": f"Please summarize the following meeting: {MEETING_SUMMARY_PROMPT}"
                            }]
                            st.rerun()
                            
                        except Exception as e:
                            logger.error(f"Error processing selected file: {str(e)}")
                            st.error(f"Error processing selected file: {str(e)}")
                            return
                            
                except Exception as e:
                    logger.error(f"Error loading files from folder: {str(e)}")
                    st.error(f"Error loading files from folder: {str(e)}")
                    return
            
            # Show the chat interface if chat is started
            if st.session_state.chat_started:
                st.markdown("---")
                
                if st.session_state.analysis_mode == "needs":
                    st.markdown("#### Analyzing Underserved Needs")
                    st.markdown("**Files being analyzed:**")
                    for file in sorted(st.session_state.unique_files):
                        st.markdown(f"- {file}")
                    # Display chat messages
                    for message in st.session_state.chat_messages:
                        with st.chat_message(message["role"]):
                            st.write(message["content"])
                            
                    # Get response from chain for the needs analysis
                    if len(st.session_state.chat_messages) == 1:  # Only the initial prompt
                        response = st.session_state.conversation_chain({"question": NEEDS_ANALYSIS_PROMPT})
                        st.session_state.chat_messages.append({"role": "assistant", "content": response["answer"]})
                        st.rerun()
                    
                    # Handle follow-up questions
                    if prompt := st.chat_input("Ask a follow-up question about the needs analysis"):
                        st.session_state.chat_messages.append({"role": "user", "content": prompt})
                        response = st.session_state.conversation_chain({"question": prompt})
                        st.session_state.chat_messages.append({"role": "assistant", "content": response["answer"]})
                        st.rerun()
                        
                elif st.session_state.analysis_mode == "meeting":
                    st.markdown("#### Summarizing Meeting")
                    if st.session_state.selected_file_for_summary:
                        st.markdown(f"Analyzing file: {Path(st.session_state.selected_file_for_summary.metadata.get('source', '')).name}")
                        
                        # Display chat messages
                        for message in st.session_state.chat_messages:
                            with st.chat_message(message["role"]):
                                st.write(message["content"])
                                
                        # Get response from chain for the meeting summary
                        if len(st.session_state.chat_messages) == 1:  # Only the initial prompt
                            response = st.session_state.conversation_chain({"question": MEETING_SUMMARY_PROMPT})
                            st.session_state.chat_messages.append({"role": "assistant", "content": response["answer"]})
                            st.rerun()
                        
                        # Handle follow-up questions
                        if prompt := st.chat_input("Ask a follow-up question about the meeting summary"):
                            st.session_state.chat_messages.append({"role": "user", "content": prompt})
                            response = st.session_state.conversation_chain({"question": prompt})
                            st.session_state.chat_messages.append({"role": "assistant", "content": response["answer"]})
                            st.rerun()
                            
                else:  # Direct chat mode
                    st.markdown("#### Chat with Documents")
                    # Display chat messages
                    for message in st.session_state.chat_messages:
                        with st.chat_message(message["role"]):
                            st.write(message["content"])
                            
                    # Handle chat input
                    if prompt := st.chat_input("Ask a question about the documents"):
                        st.session_state.chat_messages.append({"role": "user", "content": prompt})
                        response = st.session_state.conversation_chain({"question": prompt})
                        st.session_state.chat_messages.append({"role": "assistant", "content": response["answer"]})
                        st.rerun()
            
        elif not st.session_state.documents and st.session_state.get('chat_messages'):
            # Clear chat history if no documents are loaded
            st.session_state.chat_messages = []
            
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
        if st.session_state.chat_messages and st.session_state.chat_messages[-1]['role'] == 'user' and st.session_state.chat_messages[-1]['content'] == user_question:
            logger.info("Duplicate question detected, skipping processing")
            return

        # Log chat history state
        logger.info(f"Current chat history length: {len(st.session_state.chat_messages)}")

        # Generate response
        logger.info("Generating response from RAG chain")
        response = rag_chain({
            "question": user_question,
            "chat_history": [(q['content'], a['content']) for q, a in st.session_state.chat_messages if q['role'] == 'user']
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
        st.session_state.chat_messages.append({"role": "assistant", "content": answer})
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
        if not st.session_state.chat_messages or st.session_state.chat_messages[-1]['role'] != 'assistant':
            st.session_state.chat_messages.append(
                {"role": "assistant", "content": f"Sorry, there was an error processing your question. Please try again."}
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