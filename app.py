import streamlit as st
from langchain_openai import ChatOpenAI
from src.loader import load_folder_docs
from src.chain import create_conversation_chain
from src.memory_types import create_summary_memory
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from src.vectorstore import split_documents, create_vectorstore_from_documents

# Initialize LLM
llm = ChatOpenAI(
    model_name="gpt-4o",
    temperature=0,
    max_tokens=4000
)

# Initialize session states
if "all_documents" not in st.session_state:
    st.session_state.all_documents = load_folder_docs()
    st.session_state.document_names = [
        doc.metadata.get('source', '').split('/')[-1] 
        for doc in st.session_state.all_documents
    ]

if "memory" not in st.session_state:
    st.session_state.memory = create_summary_memory(llm)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

@st.cache_data
def load_initial_data():
    """Load initial documents"""
    return load_folder_docs()

def prepare_vector_store(docs):
    """Prepare vector store from documents"""
    if not docs:
        return None
    splitted_docs = split_documents(docs)
    return create_vectorstore_from_documents(splitted_docs)

def handle_user_input(user_question, rag_chain):
    """Handle user input and display response"""
    if not rag_chain:
        st.error("Please select at least one document first.")
        return

    response = rag_chain({
        "question": user_question,
        "chat_history": st.session_state.chat_history
    })
    
    st.session_state.chat_history.append((user_question, response["answer"]))
    
    # Display chat history
    display_chat_history()

def display_chat_history():
    """Display the chat history"""
    for question, answer in st.session_state.chat_history:
        with st.container():
            st.write("Human: " + question)
            st.write("Assistant: " + answer)
            st.markdown("---")

def initialize_page():
    """Initialize the Streamlit page"""
    st.set_page_config(
        page_title="Research Tools",
        page_icon="🔬",
        layout="wide"
    )

def sidebar_content():
    """Create sidebar content with navigation"""
    with st.sidebar:
        st.title("Navigation 🧭")
        
        # Add radio buttons for navigation
        app_mode = st.radio(
            "Choose the app",
            ["Research Summarizer", "Topic Analyzer"]  # Add more options as needed
        )
        
        st.markdown("---")
        st.header("Settings")
        if st.button("Clear Conversation"):
            st.session_state.memory.clear()
            st.session_state.chat_history = []
            st.experimental_rerun()
            
        return app_mode

def show_summarizer():
    """Display the research summarizer interface"""
    st.title("Research Summarizer 📚")

    # Document selector
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_docs = set(st.multiselect(
            "Select documents to include in the analysis:",
            st.session_state.document_names,
            default=st.session_state.document_names
        ))
    
    with col2:
        st.write(f"Selected: {len(selected_docs)}/{len(st.session_state.document_names)} documents")

    if not selected_docs:
        st.warning("Please select at least one document")
        return

    # Track changes in document selection
    if "previous_selection" not in st.session_state:
        st.session_state.previous_selection = selected_docs
        filtered_docs = [
            doc for doc in st.session_state.all_documents 
            if doc.metadata.get('source', '').split('/')[-1] in selected_docs
        ]
        st.session_state.vector_store = prepare_vector_store(filtered_docs)
    else:
        added_docs = selected_docs - st.session_state.previous_selection
        removed_docs = st.session_state.previous_selection - selected_docs

        if added_docs or removed_docs:
            docs_to_add = [
                doc for doc in st.session_state.all_documents 
                if doc.metadata.get('source', '').split('/')[-1] in added_docs
            ]
            docs_to_remove = [
                doc for doc in st.session_state.all_documents 
                if doc.metadata.get('source', '').split('/')[-1] in removed_docs
            ]
            
            update_vector_store(docs_to_add, docs_to_remove)
            st.session_state.previous_selection = selected_docs

    # Create chain using the stored vector store
    rag_chain = create_conversation_chain(st.session_state.vector_store, llm)

    # Chat interface
    st.markdown("### Chat Interface")
    user_question = st.text_input("Ask a question about the interviews:", key="user_input")
    
    if user_question:
        handle_user_input(user_question, rag_chain)

    # Display existing chat history
    if st.session_state.chat_history:
        display_chat_history()

def show_topic_analyzer():
    """Display the topic analyzer interface"""
    st.title("Topic Analyzer 📊")
    
    # Dummy content for now
    st.markdown("""
    ### Topic Analysis Tool
    This tool will help analyze topics across your research documents.
    
    Features coming soon:
    - Topic modeling
    - Keyword extraction
    - Trend analysis
    - Visualization of topic distribution
    """)
    
    # Dummy interface elements
    st.selectbox("Select analysis method", ["LDA", "NMF", "BERTopic"])
    st.slider("Number of topics", 1, 20, 5)
    if st.button("Analyze Topics"):
        st.info("This feature is coming soon!")
        
    # Dummy visualization
    st.markdown("### Sample Visualization")
    st.bar_chart({"Topic 1": 20, "Topic 2": 15, "Topic 3": 30, "Topic 4": 10, "Topic 5": 25})

def update_vector_store(docs_to_add=None, docs_to_remove=None):
    """Incrementally update the vector store"""
    if not st.session_state.vector_store:
        # Initial creation if vector store doesn't exist
        if docs_to_add:
            st.session_state.vector_store = prepare_vector_store(docs_to_add)
        return

    try:
        if docs_to_remove:
            # Get document IDs to remove
            for doc in docs_to_remove:
                doc_id = doc.metadata.get('source', '').split('/')[-1]
                # Find and remove matching documents from vector store
                matches = st.session_state.vector_store.similarity_search_with_score(doc.page_content, k=1)
                if matches:
                    st.session_state.vector_store.delete([matches[0][0].metadata['doc_id']])

        if docs_to_add:
            # Add new documents
            splitted_docs = split_documents(docs_to_add)
            st.session_state.vector_store.add_documents(splitted_docs)
            
    except Exception as e:
        st.error(f"Error updating vector store: {str(e)}")

def main():
    initialize_page()
    
    # Get the selected app mode from sidebar
    app_mode = sidebar_content()
    
    # Display the selected app
    if app_mode == "Research Summarizer":
        show_summarizer()
    elif app_mode == "Topic Analyzer":
        show_topic_analyzer()

if __name__ == "__main__":
    main()
