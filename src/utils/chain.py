"""
Chain utilities for conversation and document processing.
"""

from langchain.chains import ConversationalRetrievalChain
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

def create_conversation_chain(
    vectorstore,
    llm,
    k: int = 10
) -> ConversationalRetrievalChain:
    """
    Create a conversational chain for document Q&A.
    
    Args:
        vectorstore: FAISS vector store containing document embeddings
        llm: Language model instance
        k: Number of documents to retrieve
        
    Returns:
        ConversationalRetrievalChain: Chain for processing conversations
    """
    # Create retriever with specified k
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )

    # Create prompt template
    template = """You are a helpful AI assistant. Use the following conversation history and context to answer the question at the end.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    
    Chat History:
    {chat_history}
    
    Context:
    {context}
    
    Question: {question}
    
    Answer: Let me help you with that.
    """

    # Create prompt from template
    prompt = PromptTemplate(
        template=template,
        input_variables=["context", "chat_history", "question"]
    )

    # Create chain
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        combine_docs_chain_kwargs={"prompt": prompt},
        return_source_documents=True,
        verbose=True,
        memory=ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
    )

    return chain 