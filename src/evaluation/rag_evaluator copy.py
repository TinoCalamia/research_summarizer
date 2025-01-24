from typing import List, Dict, Tuple
from pathlib import Path
import Levenshtein
from langchain_community.document_loaders import TextLoader
from langchain.docstore.document import Document
from langchain.chat_models import ChatOpenAI
from src.utils.chain import create_conversation_chain
from src.utils.vectorstore import create_vectorstore_from_documents

def evaluate_single_question(interview_text: str, question: str, expected_answer: str) -> Dict:
    """
    Evaluate RAG performance for a single question using Levenshtein distance.
    
    Args:
        interview_text: The interview transcript
        question: The question to evaluate
        expected_answer: The expected answer
    
    Returns:
        Dictionary containing evaluation metrics
    """
    # Initialize RAG
    doc = Document(page_content=interview_text, metadata={"source": "test_interview.txt"})
    llm = ChatOpenAI(temperature=0, model_name="gpt-4")
    vectorstore = create_vectorstore_from_documents([doc])
    chain = create_conversation_chain(vectorstore=vectorstore, llm=llm)
    
    # Get RAG response
    response = chain({"question": question})
    rag_answer = response["answer"]
    
    # Calculate Levenshtein distance
    distance = Levenshtein.distance(rag_answer.lower(), expected_answer.lower())
    
    # Calculate similarity score (0 to 1, where 1 is perfect match)
    max_length = max(len(rag_answer), len(expected_answer))
    similarity = 1 - (distance / max_length) if max_length > 0 else 1
    
    return {
        "rag_output": rag_answer,
        "expected_output": expected_answer,
        "levenshtein_distance": distance,
        "similarity_score": similarity
    }

def main():
    # Load the interview text from file
    interview_file = Path("src/documents/test_interviews/[☎️ User Interview] - FindVendor __ Christian_otter_ai.txt")
    with open(interview_file, 'r', encoding='utf-8') as f:
        interview_text = f.read()
    
    # Test questions and expected answers
    test_cases = [
        {
            "question": "Can you describe your role and responsibilities?",
            "expected_answer": "Director of Data Science and AI at N26 with a background in research and business in Deep Tech"
        },
        {
            "question": "How is your Tech organization structured?",
            "expected_answer": "1.500 total at N26, tech in general 700, data not that many"
        },
        {
            "question": "What were the biggest challenges your team faced this year?",
            "expected_answer": "Certain models are only available through certain providers. If you want to have the best GenAI models you have to collaborate with everyone. You have to look into all solutions because there is so much happening and the market is changing so quickly."
        }
    ]
    
    # Run evaluation for each test case
    for test_case in test_cases:
        result = evaluate_single_question(
            interview_text=interview_text,
            question=test_case["question"],
            expected_answer=test_case["expected_answer"]
        )
        
        # Print results
        print(f"\nQuestion: {test_case['question']}")
        print(f"RAG Output: {result['rag_output']}")
        print(f"Expected: {result['expected_output']}")
        print(f"Similarity Score: {result['similarity_score']:.2f}")
        print(f"Levenshtein Distance: {result['levenshtein_distance']}")
        print("-" * 80)

if __name__ == "__main__":
    main() 