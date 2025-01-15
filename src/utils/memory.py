"""
Memory utilities for conversation management.
"""

from langchain.memory import ConversationSummaryMemory
from langchain_openai import ChatOpenAI

def create_summary_memory(llm: ChatOpenAI) -> ConversationSummaryMemory:
    """
    Create a conversation summary memory instance.
    
    Args:
        llm: Language model instance
        
    Returns:
        ConversationSummaryMemory: Configured memory instance
    """
    return ConversationSummaryMemory(
        llm=llm,
        memory_key="chat_history",
        return_messages=True
    ) 