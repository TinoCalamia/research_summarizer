"""
Problem Framing page functionality.
Handles problem analysis and solution tree generation.
"""

import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
import json
from typing import Dict
from src.utils import create_conversation_chain

def show_problem_framing():
    """Display the problem framing interface"""
    st.title("Problem Framing Analysis 🎯")
    
    if not st.session_state.vector_store:
        st.warning("Please select documents in the Research Summarizer first.")
        return

    # Analysis type selector
    analysis_type = st.selectbox(
        "Select analysis type",
        ["Problem Identification", "Problem Framing", "Opportunity-Solution Tree"]
    )
    
    if analysis_type == "Problem Identification":
        show_problem_identification()
    elif analysis_type == "Problem Framing":
        show_problem_framing_analysis()
    else:
        show_opportunity_solution_tree()

def show_problem_identification():
    """Show the problem identification analysis"""
    st.subheader("Problem Identification")
    
    if st.button("Identify Problems"):
        with st.spinner("Analyzing documents for problems..."):
            prompt = """
            Based on the provided documents, please:
            
            1. Identify and list the key problems or challenges mentioned
            2. For each problem:
               - Provide a clear description
               - Include relevant quotes or evidence from the documents
               - Note how frequently it was mentioned
               - Rate its severity (High/Medium/Low)
               - Identify who is affected by this problem
            
            Format your response as a structured list with clear sections for each problem.
            Focus on concrete issues rather than general observations.
            If multiple stakeholders mentioned the same problem, highlight this pattern.
            
            Example format:
            Problem 1: [Brief title]
            - Description: [Clear explanation]
            - Evidence: [Quotes from documents]
            - Frequency: [Number of mentions]
            - Severity: [High/Medium/Low]
            - Affected Stakeholders: [List of affected parties]
            """
            
            response = get_analysis_response(prompt)
            if response and not response.startswith("I'm sorry"):
                st.markdown("### Identified Problems")
                st.markdown(response)
            else:
                st.error("Could not identify problems. Please ensure documents are loaded and contain relevant information.")

def show_problem_framing_analysis():
    """Show the problem framing analysis"""
    st.subheader("Problem Framing")
    
    framing_perspectives = st.multiselect(
        "Select framing perspectives",
        ["User Need", "Business Impact", "Technical Feasibility", 
         "Market Opportunity", "Social Impact"],
        default=["User Need", "Business Impact"]
    )
    
    if st.button("Frame Problems"):
        with st.spinner("Analyzing problem frames..."):
            prompt = f"""
            Analyze the problems from these perspectives: {', '.join(framing_perspectives)}
            
            For each perspective:
            1. Reframe the core problems
            2. List key considerations
            3. Identify potential stakeholders
            4. Suggest initial directions for solutions
            
            Format as a structured analysis with clear sections for each perspective.
            """
            
            response = get_analysis_response(prompt)
            if response:
                st.markdown(response)

def show_opportunity_solution_tree():
    """Display the opportunity-solution tree visualization."""
    
    # Custom problem input
    custom_problem = st.text_input(
        "Enter your problem statement (optional):",
        help="Leave empty to let the AI identify the core problem from the documents"
    )
    
    # Tree depth control
    depth_options = ["Automatic", "2 levels", "3 levels", "4 levels"]
    depth_selection = st.selectbox(
        "Select tree depth:",
        options=depth_options,
        help="Choose how detailed you want the analysis to be"
    )
    
    if st.button("Generate Opportunity-Solution Tree"):
        with st.spinner("Analyzing documents and generating tree..."):
            # Determine depth parameters
            if depth_selection == "2 levels":
                max_opportunities = 2
                solutions_per_opportunity = 1
            elif depth_selection == "3 levels":
                max_opportunities = 3
                solutions_per_opportunity = 2
            elif depth_selection == "4 levels":
                max_opportunities = 4
                solutions_per_opportunity = 3
            else:  # Automatic
                max_opportunities = "appropriate"
                solutions_per_opportunity = "appropriate"
            
            # Create prompt based on inputs
            prompt = f"""
            Create an opportunity-solution tree based on the documents.
            {f'Use this core problem: "{custom_problem}"' if custom_problem else 'Identify the core problem from the documents.'}
            
            Generate {max_opportunities} opportunities and {solutions_per_opportunity} solutions per opportunity.
            
            Return ONLY the JSON data structure with no additional text or explanation.
            Use exactly this format:
            {{
                "nodes": [
                    {{"id": "problem", "label": "Core Problem", "color": "#FF6B6B"}},
                    {{"id": "opp1", "label": "Opportunity 1", "color": "#4ECDC4"}},
                    {{"id": "sol1", "label": "Solution 1.1", "color": "#95A5A6"}}
                ],
                "edges": [
                    {{"from": "problem", "to": "opp1"}},
                    {{"from": "opp1", "to": "sol1"}}
                ]
            }}
            
            Ensure each opportunity and solution is specific and actionable.
            """
            
            try:
                # Get response from LLM
                response = get_analysis_response(prompt)
                
                # Extract JSON from response (in case there's additional text)
                try:
                    # Find the first '{' and last '}'
                    start_idx = response.find('{')
                    end_idx = response.rfind('}') + 1
                    
                    if start_idx == -1 or end_idx == 0:
                        raise ValueError("No JSON object found in response")
                    
                    json_str = response[start_idx:end_idx]
                    tree_data = json.loads(json_str)
                    
                    # Validate tree data structure
                    if not all(key in tree_data for key in ['nodes', 'edges']):
                        raise ValueError("Missing required keys in tree data")
                    
                    # Create nodes and edges for visualization
                    nodes = [
                        Node(
                            id=node['id'],
                            label=node['label'],
                            color=node.get('color', '#95A5A6')
                        ) for node in tree_data['nodes']
                    ]
                    
                    edges = [
                        Edge(
                            source=edge['from'],
                            target=edge['to']
                        ) for edge in tree_data['edges']
                    ]
                    
                    # Configure visualization
                    config = Config(
                        width=800,
                        height=600,
                        directed=True,
                        physics=True,
                        hierarchical=True
                    )
                    
                    # Display the graph
                    st.markdown("### Opportunity-Solution Tree")
                    agraph(nodes=nodes, edges=edges, config=config)
                    
                except json.JSONDecodeError as e:
                    st.error(f"Error parsing JSON: {str(e)}")
                    st.text("Raw response for debugging:")
                    st.text(response)
                except ValueError as e:
                    st.error(f"Error in response format: {str(e)}")
                    st.text("Raw response for debugging:")
                    st.text(response)
                    
            except Exception as e:
                st.error(f"Error generating tree: {str(e)}")

def get_analysis_response(prompt: str) -> str:
    """
    Get analysis response from the RAG chain.
    
    Args:
        prompt: Analysis prompt
        
    Returns:
        str: Formatted response
    """
    try:
        rag_chain = create_conversation_chain(st.session_state.vector_store, st.session_state.llm)
        response = rag_chain({
            "question": prompt,
            "chat_history": []  # Empty for fresh analysis
        })
        
        return response.get("answer", "")
    except Exception as e:
        st.error(f"Error during analysis: {str(e)}")
        return "" 