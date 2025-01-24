from typing import List, Dict, Tuple
from pathlib import Path
from langchain.docstore.document import Document
from langchain_community.chat_models import ChatOpenAI
from src.utils.chain import create_conversation_chain
from src.utils.vectorstore import create_vectorstore_from_documents

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def call_rag(question: str):
    # Load the interview text from file
    interview_file = Path("src/documents/test_interviews/[☎️ User Interview] - FindVendor __ Christian_otter_ai.txt")
    with open(interview_file, 'r', encoding='utf-8') as f:
        interview_text = f.read()

    logger.info(f"Starting evaluation for question: {question}")
        
    # Initialize RAG
    logger.info("Creating document...")
    doc = Document(page_content=interview_text, metadata={"source": "test_interview.txt"})
    
    logger.info("Initializing LLM...")
    llm = ChatOpenAI(temperature=0, model_name="gpt-4")
    
    logger.info("Creating vectorstore...")
    vectorstore = create_vectorstore_from_documents([doc])
    
    logger.info("Creating conversation chain...")
    chain = create_conversation_chain(vectorstore=vectorstore, llm=llm)
    
    # Get RAG response
    logger.info("Getting response from chain...")
    response = chain({"question": question})
    rag_answer = response["answer"]
    logger.info(f"Received response: {rag_answer[:100]}...")  # Log first 100 chars

    # Get RAG response
    response = chain({"question": question})
    rag_answer = response["answer"]
    print(rag_answer)

    result = {
        "output": rag_answer,
    }

    #     result['tokenUsage'] = {"total": token_count, "prompt": prompt_token_count, "completion": completion_token_count}

    return result
