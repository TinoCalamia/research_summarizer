from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

def create_conversation_chain(vector_store, llm):
    # Add a check for vector store
    if vector_store is None:
        return None
        
    # Initialize memory
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key='answer'
    )
    
    # Create the conversation chain with memory
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(
            search_kwargs={"k": 3}  # Adjust the number of documents to retrieve
        ),
        memory=memory,
        return_source_documents=True,
        return_generated_question=True
    )
    
    return chain 