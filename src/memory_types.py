from langchain.memory import (
    ConversationBufferWindowMemory,  # Keeps last K interactions
    ConversationSummaryMemory,       # Maintains a summary of the conversation
    ConversationTokenBufferMemory    # Keeps conversation within token limit
)

def create_summary_memory(llm):
    return ConversationSummaryMemory(
        llm=llm,
        memory_key="chat_history",
        return_messages=True,
        output_key='answer'
    )

def create_window_memory(k=5):
    return ConversationBufferWindowMemory(
        k=k,
        memory_key="chat_history",
        return_messages=True,
        output_key='answer'
    )