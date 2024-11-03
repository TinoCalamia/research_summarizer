import os
import faiss
import streamlit as st
from PIL import Image
import numpy as np

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter

import src.constants as con

# Environment setup for LangChain tracing
os.environ['LANGCHAIN_TRACING_V2'] = "true"
os.environ['LANGCHAIN_ENDPOINT'] = "https://api.smith.langchain.com"

from src.loader import load_folder_docs
import src.prompts as pr
from src.utils import format_docs
from src.vectorstore import create_vectorstore_from_documents, split_documents, add_documents_to_vectorstore

st.set_page_config(page_title="Sales Insights ChatBot", page_icon="💼", layout="centered")

@st.cache_resource()
def prepare_data():
    
    # Define the LLM for generating responses
    llm = ChatOpenAI(model_name=con.MODEL_NAME, temperature=con.MODEL_TEMPERATURE)

    # Load and split user interview documents
    print('---------- Load User Interviews -------------')
    interview_docs = load_folder_docs()
    print('---------- Doc loaded successfully -------------')
    if not interview_docs:
        raise ValueError("No documents found in the specified folder.")
    print('---------- Split documents -------------')
    interview_splits = split_documents(interview_docs)
    print('---------- Documents splitted successfully -------------')

    # Create vector store for interviews and define retriever
    print('---------- Create vector DB -------------')
    vector_db = create_vectorstore_from_documents(interview_splits)   
    retriever = vector_db.as_retriever(search_type="similarity", search_kwargs={"k": 5})

    # Define prompt template for analyzing interviews
    prompt = ChatPromptTemplate.from_template(pr.create_basic_prompt())

    # Define the RAG chain for retrieving and generating responses
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain

rag_chain = prepare_data()

####################SETUP STREAMLIT APP#####################
print('---------- Load Streamlit App -------------')

# Title and Branding
st.markdown("<h1 style='text-align: center; color: #0582BC;'>Sales Insights ChatBot</h1>", unsafe_allow_html=True)
# Load and display company logo
col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.image(Image.open("src/images/company-logo.png"))
    
def run_app():
    # Initialize session state for messages and question tracking
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", 
             "content": "Hello! I'm here to help analyze user interviews for key insights in the sales process. Please enter any questions or areas you'd like me to explore."}
        ]
    if "current_question" not in st.session_state:
        st.session_state.current_question = None

    # Display chat messages
    for message in st.session_state.messages:
        avatar = None if message["role"] == "user" else Image.open("src/images/avatar.png")
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    # Accept user input
    prompt = st.chat_input("Ask me a question about sales insights.")
    
    # Ensure `prompt` is a string and not a repeat question
    if prompt and isinstance(prompt, str) and prompt != st.session_state.current_question:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user", avatar=None):
            st.markdown(prompt)
        
        try:
            # Generate response using the RAG chain - pass prompt directly as string
            response = rag_chain.invoke(prompt)  # Changed this line
            
            # Display chatbot response
            with st.chat_message("assistant", avatar=Image.open("src/images/avatar_2.png")):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Update current question
            st.session_state.current_question = prompt
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
run_app()
