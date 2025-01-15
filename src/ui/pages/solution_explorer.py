"""
Solution Explorer page functionality.
Guides users through a structured problem-solving workflow.
"""

import streamlit as st
from typing import List, Dict, Any
import json
from src.ui.components.chat_interface import ChatInterface
from datetime import datetime
from src.utils.pdf_generator import generate_solution_pdf
from src.utils import (
    load_folder_docs, 
    split_documents, 
    create_vectorstore_from_documents,
    create_conversation_chain
)
import os
import shutil
import time

def get_analysis_response(prompt: str) -> str:
    """
    Get analysis response from the LLM.
    
    Args:
        prompt: The prompt to send to the LLM
        
    Returns:
        str: The LLM's response
    """
    try:
        # Create conversation chain for analysis
        if not hasattr(st.session_state, 'llm'):
            st.error("LLM not initialized. Please check your configuration.")
            return ""
        
        # Use vector store if available
        vectorstore = getattr(st.session_state, 'solution_vector_store', None)
        
        chain = create_conversation_chain(
            vectorstore=vectorstore,
            llm=st.session_state.llm
        )
        
        # Adjust prompt if using vectorstore
        if vectorstore:
            prompt += "\n\nPlease incorporate relevant information from the uploaded documents in your response."
        
        # Get response with empty chat history
        response = chain.invoke({
            "question": prompt,
            "chat_history": []  # Add empty chat history
        })
        
        # Extract answer from response
        if isinstance(response, dict) and 'answer' in response:
            return response['answer']
        elif isinstance(response, str):
            return response
        else:
            return str(response)
            
    except Exception as e:
        st.error(f"Error getting analysis: {str(e)}")
        return "I apologize, but I encountered an error while analyzing your request. Please try again."

def show_solution_explorer():
    """Display the solution explorer interface with step-by-step workflow."""
    st.title("Solution Explorer 🎯")
    
    # Initialize session state for workflow
    if "solution_step" not in st.session_state:
        st.session_state.solution_step = 1
    if "workflow_data" not in st.session_state:
        st.session_state.workflow_data = {}
    if "analysis_complete" not in st.session_state:
        st.session_state.analysis_complete = False
    
    # Progress bar
    total_steps = 8
    st.progress(st.session_state.solution_step / total_steps)
    
    # Step navigation
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.session_state.solution_step > 1:
            if st.button("← Back"):
                st.session_state.solution_step -= 1
                st.rerun()
    
    # Display current step
    show_current_step()

def show_current_step():
    """Display the current step in the workflow."""
    
    if st.session_state.solution_step == 1:
        show_problem_definition()
    elif st.session_state.solution_step == 2:
        show_requirements_collection()
    elif st.session_state.solution_step == 3:
        show_company_parameters()
    elif st.session_state.solution_step == 4:
        show_tool_selection()
    elif st.session_state.solution_step == 5:
        show_tool_connection()
    elif st.session_state.solution_step == 6:
        show_document_upload()
    elif st.session_state.solution_step == 7:
        show_output_selection()
    elif st.session_state.solution_step == 8:
        show_analysis_chat()

def show_problem_definition():
    """Step 1: Problem/Goal Definition"""
    st.header("Step 1: Define Your Problem or Goal")
    
    # Get existing value or empty string
    current_problem = st.session_state.workflow_data.get('problem', '')
    
    problem = st.text_area(
        "Describe the problem you are solving or the goal you want to achieve:",
        value=current_problem,
        height=150,
        help="Be as specific as possible to get better recommendations"
    )
    
    if st.button("Next →", disabled=not problem):
        st.session_state.workflow_data['problem'] = problem
        st.session_state.solution_step += 1
        st.rerun()

def show_requirements_collection():
    """Step 2: Requirements Collection"""
    st.header("Step 2: Requirements Collection")
    
    # Initialize requirements in session state if not exists
    if 'requirements' not in st.session_state:
        st.session_state.requirements = []

        # Display summary of inputs
    with st.expander("Examples", expanded=False):
        st.markdown("""
        Add requirements from different departments. For example:
        - IT: System must support SSO
        - Legal: Data must be stored in EU
        - Operations: Process 1000 requests per hour
        """)
    
    # st.markdown("""
    # Add requirements from different departments. For example:
    # - IT: System must support SSO
    # - Legal: Data must be stored in EU
    # - Operations: Process 1000 requests per hour
    # """)
    
    # Display existing requirements
    for i, req in enumerate(st.session_state.requirements):
        col1, col2, col3 = st.columns([2, 3, 1])
        
        with col1:
            department = st.text_input(
                "Department",
                value=req['department'],
                key=f"dept_{i}"
            )
        
        with col2:
            requirement = st.text_input(
                "Requirement",
                value=req['requirement'],
                key=f"req_{i}"
            )
        
        with col3:
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.requirements.pop(i)
                st.rerun()
        
        # Update the requirement if changed
        st.session_state.requirements[i] = {
            'department': department,
            'requirement': requirement
        }
    
    # Add new requirement button
    if st.button("➕ Add Requirement"):
        st.session_state.requirements.append({
            'department': '',
            'requirement': ''
        })
        st.rerun()
    
    # Validation and navigation
    if st.session_state.requirements:
        # Check if all fields are filled
        all_filled = all(
            req['department'].strip() and req['requirement'].strip() 
            for req in st.session_state.requirements
        )
        
        if not all_filled:
            st.warning("Please fill in all requirement fields or remove empty ones.")
    
    # Save requirements to workflow data
    st.session_state.workflow_data['requirements'] = st.session_state.requirements
    
    # Navigation
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Next →"):
            st.session_state.solution_step += 1
            st.rerun()

def show_company_parameters():
    """Step 2: Company Parameters"""
    st.header("Step 2: Company Parameters")
    
    # Get existing values or defaults
    params = st.session_state.workflow_data.get('company_params', {})
    
    col1, col2 = st.columns(2)
    with col1:
        industry = st.selectbox(
            "Industry",
            ["Technology", "Healthcare", "Finance", "Retail", "Manufacturing", "Other"],
            index=["Technology", "Healthcare", "Finance", "Retail", "Manufacturing", "Other"].index(params.get('industry', 'Technology'))
        )
        company_size = st.selectbox(
            "Company Size",
            ["1-50", "51-200", "201-1000", "1000+"],
            index=["1-50", "51-200", "201-1000", "1000+"].index(params.get('company_size', '1-50'))
        )
        
    with col2:
        budget = st.selectbox(
            "Budget Range",
            ["< $10k", "$10k - $50k", "$50k - $200k", "$200k+"],
            index=["< $10k", "$10k - $50k", "$50k - $200k", "$200k+"].index(params.get('budget', '< $10k'))
        )
        success_metric = st.text_input(
            "Success Metric",
            value=params.get('success_metric', ''),
            help="e.g., Reduce processing time by 50%, Increase conversion by 25%"
        )
    
    if st.button("Next →", disabled=not all([industry, company_size, budget, success_metric])):
        st.session_state.workflow_data['company_params'] = {
            'industry': industry,
            'company_size': company_size,
            'budget': budget,
            'success_metric': success_metric
        }
        st.session_state.solution_step += 1
        st.rerun()

def show_tool_selection():
    """Step 3: Tool Selection"""
    st.header("Step 3: Current Tools")
    
    # Predefined tool categories and options
    tool_options = {
        "Version Control": ["GitHub", "GitLab", "Bitbucket", "Azure DevOps"],
        "CRM": ["Salesforce", "HubSpot", "Microsoft Dynamics", "Zoho"],
        "Project Management": ["Jira", "Trello", "Asana", "Monday.com"],
        "Communication": ["Slack", "Microsoft Teams", "Discord"],
        "Documentation": ["Confluence", "Notion", "SharePoint"]
    }
    
    # Get existing selections or empty dict
    selected_tools = st.session_state.workflow_data.get('tools', {})
    
    # Show tool selection for each category
    for category, tools in tool_options.items():
        st.subheader(category)
        selected = st.multiselect(
            f"Select {category} tools in use:",
            tools,
            default=selected_tools.get(category, [])
        )
        selected_tools[category] = selected
    
    if st.button("Next →"):
        st.session_state.workflow_data['tools'] = selected_tools
        st.session_state.solution_step += 1
        st.rerun()

def show_tool_connection():
    """Step 4: Tool Connection"""
    st.header("Step 4: Connect Your Tools")
    
    # Initialize tool connection state if not exists
    if 'connected_tools' not in st.session_state:
        st.session_state.connected_tools = set()
    
    # Get selected tools from previous step
    selected_tools = st.session_state.workflow_data.get('tools', {})
    
    if not any(tools for tools in selected_tools.values()):
        st.warning("No tools were selected in the previous step.")
        if st.button("Next →"):
            st.session_state.solution_step += 1
            st.rerun()
        return
    
    st.markdown("Connect to your selected tools to enable automated solution implementation.")
    st.info("🔒 This is a demo - no actual connections will be made.")
    
    # Display tools by category with connection status
    for category, tools in selected_tools.items():
        if tools:  # Only show categories with selected tools
            st.subheader(f"📁 {category}")
            
            for tool in tools:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{tool}**")
                
                with col2:
                    is_connected = tool in st.session_state.connected_tools
                    status = "🟢 Connected" if is_connected else "⚪ Not Connected"
                    st.markdown(status)
                
                with col3:
                    button_label = "Disconnect" if is_connected else "Connect"
                    if st.button(button_label, key=f"btn_{tool}"):
                        if is_connected:
                            st.session_state.connected_tools.remove(tool)
                        else:
                            # Simulate connection process
                            with st.spinner(f"Connecting to {tool}..."):
                                time.sleep(1)  # Simulate connection delay
                                st.session_state.connected_tools.add(tool)
                                st.success(f"Successfully connected to {tool}")
                                st.rerun()
    
    # Show connection summary
    if st.session_state.connected_tools:
        st.markdown("---")
        st.markdown("### Connected Tools")
        for tool in st.session_state.connected_tools:
            st.markdown(f"✅ {tool}")
    
    # Update workflow data with connection status
    st.session_state.workflow_data['connected_tools'] = list(st.session_state.connected_tools)
    
    # Navigation
    if st.button("Next →"):
        st.session_state.solution_step += 1
        st.rerun()

def show_document_upload():
    """Step 5: Document Upload"""
    st.header("Step 5: Additional Context")
    
    st.info("Upload any relevant company documents for more personalized recommendations")
    
    uploaded_files = st.file_uploader(
        "Upload documents (optional)",
        accept_multiple_files=True,
        type=['pdf', 'docx', 'txt']
    )
    
    if uploaded_files:
        # Create a temporary directory for uploads if it doesn't exist
        temp_dir = "temp_uploads"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        try:
            # Save uploaded files temporarily
            saved_files = []
            for file in uploaded_files:
                file_path = os.path.join(temp_dir, file.name)
                with open(file_path, "wb") as f:
                    f.write(file.getvalue())
                saved_files.append(file_path)
            
            # Load and process documents
            with st.spinner("Processing uploaded documents..."):
                # Load documents
                documents = load_folder_docs(temp_dir)
                
                if documents:
                    # Split documents into chunks
                    splitted_docs = split_documents(documents)
                    
                    # Create vector store
                    vector_store = create_vectorstore_from_documents(splitted_docs)
                    
                    # Save to session state
                    st.session_state.workflow_data['documents'] = [file.name for file in uploaded_files]
                    st.session_state.solution_vector_store = vector_store
                    
                    st.success(f"Successfully processed {len(uploaded_files)} documents")
                else:
                    st.warning("No content could be extracted from the uploaded documents")
            
            # Cleanup temporary files
            for file_path in saved_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
        except Exception as e:
            st.error(f"Error processing documents: {str(e)}")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return
        
        finally:
            # Ensure cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    if st.button("Next →"):
        st.session_state.solution_step += 1
        st.rerun()

def show_output_selection():
    """Step 6: Output Selection"""
    st.header("Step 6: Expected Outputs")
    
    output_options = [
        "Design Document",
        "Business Case",
        "Project Plan",
        "Technical Requirements",
        "Implementation Timeline",
        "Cost-Benefit Analysis",
        "Risk Assessment"
    ]
    
    selected_outputs = st.multiselect(
        "Select desired outputs:",
        output_options,
        default=st.session_state.workflow_data.get('outputs', [])
    )
    
    if st.button("Start Analysis →", disabled=not selected_outputs):
        st.session_state.workflow_data['outputs'] = selected_outputs
        st.session_state.solution_step += 1
        st.rerun()

def show_analysis_chat():
    """Step 8: Analysis and Chat"""
    st.header("Step 8: Solution Analysis")
    
    # Initialize chat history if not exists
    if "solution_chat_history" not in st.session_state:
        st.session_state.solution_chat_history = []
        
    # Generate initial analysis if not done
    if not st.session_state.analysis_complete:
        with st.spinner("Analyzing inputs and generating initial recommendations..."):
            # Format requirements section
            requirements_section = ""
            if st.session_state.workflow_data.get('requirements'):
                requirements_section = ""
                for req in st.session_state.workflow_data['requirements']:
                    requirements_section += f"\n- {req['department']}: {req['requirement']}"
            
            initial_prompt = f"""
            Based on the following information, provide a comprehensive solution analysis:
            
            Problem/Goal: {st.session_state.workflow_data.get('problem')}
            Business Requirements: {requirements_section}
            
            Company Context:
            - Industry: {st.session_state.workflow_data.get('company_params', {}).get('industry')}
            - Size: {st.session_state.workflow_data.get('company_params', {}).get('company_size')}
            - Budget: {st.session_state.workflow_data.get('company_params', {}).get('budget')}
            - Success Metric: {st.session_state.workflow_data.get('company_params', {}).get('success_metric')}
            
            Current Tools: {json.dumps(st.session_state.workflow_data.get('tools', {}), indent=2)}
            Connected Tools: {', '.join(st.session_state.workflow_data.get('connected_tools', []))}
            
            Requested Outputs: {', '.join(st.session_state.workflow_data.get('outputs', []))}
            
            Please provide:
            1. Initial solution recommendation that addresses all departmental requirements
            2. Implementation approach considering existing tools and infrastructure
            3. Key considerations and risks for each department's requirements
            4. Specific next steps for each department
            5. How the solution meets the success metrics while staying within budget
            """
            
            # Get initial analysis from LLM
            initial_response = get_analysis_response(initial_prompt)
            
            # Add to chat history
            st.session_state.solution_chat_history.append(
                ("System", "Here's my initial analysis based on your inputs:")
            )
            st.session_state.solution_chat_history.append(
                ("Assistant", initial_response)
            )
            st.session_state.analysis_complete = True
    
    # Display summary of inputs
    with st.expander("Review Inputs", expanded=False):
        st.json(st.session_state.workflow_data)
    
    # Chat interface for solution refinement
    st.markdown("### Solution Refinement")
    st.markdown("""
    Provide feedback or ask questions to refine the solution. Consider:
    - Specific concerns about the proposed solution
    - Areas that need more detail
    - Implementation challenges
    - Additional requirements
    - Department-specific questions
    """)
    
    # Get user input
    user_question = st.chat_input("Your feedback or question:")
    
    if user_question:
        # Add user message to history
        st.session_state.solution_chat_history.append(("User", user_question))
        
        # Generate context-aware prompt
        refinement_prompt = f"""
        Previous conversation: {str(st.session_state.solution_chat_history)}
        
        User feedback: {user_question}
        
        Original requirements:
        {requirements_section if 'requirements_section' in locals() else 'No specific requirements provided'}
        
        Based on this feedback and the original context:
        {json.dumps(st.session_state.workflow_data, indent=2)}
        
        Please provide an updated and refined solution that:
        1. Addresses the user's feedback
        2. Maintains compliance with all departmental requirements
        3. Stays within the defined constraints
        4. Builds upon previous recommendations
        """
        
        # Get refined response
        with st.spinner("Analyzing feedback and updating recommendation..."):
            refined_response = get_analysis_response(refinement_prompt)
            st.session_state.solution_chat_history.append(("Assistant", refined_response))
    
    # Display chat history
    for role, message in st.session_state.solution_chat_history:
        if role == "User":
            st.chat_message("user").write(message)
        elif role == "Assistant":
            st.chat_message("assistant").write(message)
        elif role == "System":
            st.chat_message("assistant").write(f"🔄 {message}")
    
    # Export options
    if st.session_state.solution_chat_history:
        st.divider()
        st.subheader("Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Export to Jira"):
                st.info("Preparing Jira export...")
        with col2:
            if st.button("Export to GitHub"):
                st.info("Preparing GitHub export...")
        with col3:
            if st.button("Save as Final Solution"):
                st.session_state.final_solution = {
                    'inputs': st.session_state.workflow_data,
                    'conversation': st.session_state.solution_chat_history,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.success("Solution saved! You can now download it as PDF.")
        
        # Separate PDF download button
        if hasattr(st.session_state, 'final_solution'):
            try:
                pdf_content = generate_solution_pdf(st.session_state.final_solution)
                st.download_button(
                    label="📥 Download Solution PDF",
                    data=pdf_content,
                    file_name=f"solution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    key="pdf_download"  # Added unique key
                )
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")
                st.error("Please try saving the solution again.") 