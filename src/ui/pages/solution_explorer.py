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
import random

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
        
        # Create chain based on whether we have a vector store
        if vectorstore:
            # RAG chain with vector store
            chain = create_conversation_chain(
                vectorstore=vectorstore,
                llm=st.session_state.llm
            )
            # Add context about documents
            prompt += "\n\nPlease incorporate relevant information from the uploaded documents in your response."
        else:
            # Simple chain for direct LLM interaction without RAG
            from langchain.chains import LLMChain
            from langchain.prompts import PromptTemplate
            
            template = """
            Based on the following context and question, provide a detailed response:
            
            Context:
            {context}
            
            Question:
            {question}
            
            Please provide a comprehensive and well-structured response.
            """
            
            prompt_template = PromptTemplate(
                input_variables=["context", "question"],
                template=template
            )
            
            chain = LLMChain(
                llm=st.session_state.llm,
                prompt=prompt_template
            )
            
            # Get response without RAG
            response = chain.invoke({
                "context": "You are a solution architect helping to design a comprehensive solution.",
                "question": prompt
            })
            
            return response.get("text", str(response))
        
        # If using RAG chain, get response with empty chat history
        if vectorstore:
            response = chain.invoke({
                "question": prompt,
                "chat_history": []
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
    st.title("Business Consultant Agent 🎯")
    
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
    
    # Initialize email request state
    if 'show_email_form' not in st.session_state:
        st.session_state.show_email_form = False
    if 'email_sent' not in st.session_state:
        st.session_state.email_sent = set()
    
    # Main requirements input section
    st.markdown("""
    Add requirements from different departments. For example:
    - IT: System must support SSO
    - Legal: Data must be stored in EU
    - Operations: Process 1000 requests per hour
    """)
    
    # Display existing requirements
    for i, req in enumerate(st.session_state.requirements):
        with st.container():
            col1, col2, col3 = st.columns([2, 3, 1])
            
            with col1:
                department = st.text_input(
                    "Department",
                    value=req['department'],
                    key=f"dept_{i}",
                    label_visibility="visible"
                )
            
            with col2:
                requirement = st.text_input(
                    "Requirement",
                    value=req['requirement'],
                    key=f"req_{i}",
                    label_visibility="visible"
                )
            
            with col3:
                st.markdown("####")  # Even finer spacing control
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
    
    # Optional: Request requirements from colleagues
    st.markdown("---")
    with st.expander("🤝 Need input from colleagues?"):
        st.markdown("Request requirements from your team members via email.")
        
        # Toggle email form
        if not st.session_state.show_email_form:
            if st.button("Request Requirements via Email"):
                st.session_state.show_email_form = True
                st.rerun()
        
        # Show email form if toggled
        if st.session_state.show_email_form:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 2])
                
                with col1:
                    email = st.text_input(
                        "Colleague's Email",
                        key="req_email",
                        label_visibility="visible"
                    )
                
                with col2:
                    department = st.selectbox(
                        "Department",
                        ["IT", "Legal", "Finance", "Operations", "Marketing", "HR", "Other"],
                        key="req_dept",
                        label_visibility="visible"
                    )
                
                with col3:
                    st.markdown("####")  # Even finer spacing control
                    if st.button("Send Request"):
                        if email and "@" in email:  # Basic email validation
                            # Simulate sending email
                            with st.spinner(f"Sending request to {email}..."):
                                time.sleep(1.5)  # Simulate network delay
                                st.session_state.email_sent.add(email)
                                st.success(f"✉️ Request sent to {email}")
                                # Clear the form
                                st.session_state.show_email_form = False
                                st.rerun()
                        else:
                            st.error("Please enter a valid email address")
            
            # Cancel button on new line
            if st.button("Cancel"):
                st.session_state.show_email_form = False
                st.rerun()
        
        # Show sent requests
        if st.session_state.email_sent:
            st.markdown("### Pending Requests")
            for email in st.session_state.email_sent:
                st.info(f"Waiting for response from: {email}")
                # Add a simulate response button (for demo purposes)
                if st.button(f"Simulate Response from {email}", key=f"sim_{email}"):
                    # Add a simulated requirement
                    dummy_requirements = [
                        "Must have 24/7 support",
                        "Need real-time reporting",
                        "Require multi-factor authentication",
                        "Must integrate with existing systems",
                        "Should support multiple languages"
                    ]
                    new_req = {
                        'department': department,
                        'requirement': random.choice(dummy_requirements)
                    }
                    st.session_state.requirements.append(new_req)
                    st.session_state.email_sent.remove(email)
                    st.success(f"Received response from {email}!")
                    st.rerun()
    
    # Save requirements to workflow data
    st.session_state.workflow_data['requirements'] = st.session_state.requirements
    
    # Navigation
    st.markdown("---")
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
        "Documentation": ["Confluence", "Notion", "SharePoint"],
        "Other": ['Zendesk', "Intercom"]
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
    """Step 6: Document Upload"""
    st.header("Step 6: Additional Context")
    
    st.info("Upload any relevant company documents for more personalized recommendations (optional)")
    
    # Store uploaded files in session state to persist between reruns
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    
    # Create a wider container for the upload section
    with st.container():
        uploaded_files = st.file_uploader(
            "Upload documents",
            accept_multiple_files=True,
            type=['pdf', 'docx', 'txt']
        )
    
    # Update session state when new files are uploaded
    if uploaded_files:
        st.session_state.uploaded_files = uploaded_files
    
    # Display uploaded files in a wider format
    if st.session_state.uploaded_files:
        st.write("📎 Uploaded files:")
        for file in st.session_state.uploaded_files:
            st.write(f"- {file.name}")
    
    st.markdown("---")
    
    # Navigation with processing
    col1, col2 = st.columns([1, 5])
    with col1:
        next_button = st.button("Next →")
    
    # Process documents in the wider column
    with col2:
        if next_button:
            # Process documents only when clicking Next
            if st.session_state.uploaded_files:
                # Create a temporary directory for uploads
                temp_dir = "temp_uploads"
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)
                
                try:
                    # Save uploaded files temporarily
                    saved_files = []
                    for file in st.session_state.uploaded_files:
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
                            st.session_state.workflow_data['documents'] = [file.name for file in st.session_state.uploaded_files]
                            st.session_state.solution_vector_store = vector_store
                            
                            # Success message in full width
                            st.success(f"Successfully processed {len(st.session_state.uploaded_files)} documents")
                            
                            # Progress to next step
                            st.session_state.solution_step += 1
                            st.rerun()
                        else:
                            st.error("No content could be extracted from the uploaded documents")
                    
                except Exception as e:
                    st.error(f"Error processing documents: {str(e)}")
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
                    return
                
                finally:
                    # Cleanup temporary files
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
            else:
                # Clear vector store if no documents are uploaded
                if 'solution_vector_store' in st.session_state:
                    del st.session_state.solution_vector_store
                st.session_state.workflow_data['documents'] = []
                
                # Progress to next step
                st.session_state.solution_step += 1
                st.rerun()

def show_output_selection():
    """Step 7: Output Selection"""
    st.header("Step 7: Expected Outputs")
    
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

def format_assistant_message(message: str) -> str:
    """Format assistant message with HTML styling for better readability."""
    
    # Split message into lines
    lines = message.split('\n')
    formatted_lines = []
    
    for line in lines:
        # Check if it's a main section (numbered)
        if line.strip() and line.strip()[0].isdigit() and '. ' in line:
            # Make numbered sections bold and larger
            section_title = line.split('. ')[0] + '.'
            section_content = '. '.join(line.split('. ')[1:])
            formatted_lines.append(
                f"<div style='margin-top: 20px; margin-bottom: 10px;'>"
                f"<span style='font-size: 18px; font-weight: bold;'>{section_title}</span> "
                f"<span style='font-size: 18px; font-weight: bold;'>{section_content}</span>"
                f"</div>"
            )
        # Check if it's a subsection (starts with -)
        elif line.strip().startswith('-'):
            # Add proper indentation and styling for subsections
            formatted_lines.append(
                f"<div style='margin-left: 20px; margin-top: 5px;'>{line}</div>"
            )
        # Regular text
        else:
            formatted_lines.append(f"<div style='margin-top: 5px;'>{line}</div>")
    
    return ''.join(formatted_lines)

def show_analysis_chat():
    """Step 8: Analysis and Chat"""
    st.header("Step 8: Solution Analysis")
    
    # Initialize or reset chat history if outputs have changed
    if "previous_outputs" not in st.session_state:
        st.session_state.previous_outputs = None
    
    current_outputs = st.session_state.workflow_data.get('outputs', [])
    
    # Check if outputs have changed
    if st.session_state.previous_outputs != current_outputs:
        st.session_state.solution_chat_history = []
        st.session_state.analysis_complete = False
        st.session_state.previous_outputs = current_outputs
    
    # Initialize chat history if not exists
    if "solution_chat_history" not in st.session_state:
        st.session_state.solution_chat_history = []
        
    # Generate initial analysis if not done
    if not st.session_state.analysis_complete:
        with st.spinner("Analyzing inputs and generating initial recommendations..."):
            # Format requirements section
            requirements_section = ""
            if st.session_state.workflow_data.get('requirements'):
                requirements_section = "\nDepartmental Requirements:"
                for req in st.session_state.workflow_data['requirements']:
                    requirements_section += f"\n- {req['department']}: {req['requirement']}"
            
            # Add document context if available
            document_context = ""
            if st.session_state.workflow_data.get('documents'):
                document_context = "\n\nAnalysis includes information from uploaded documents: " + \
                                 ", ".join(st.session_state.workflow_data['documents'])
            
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

            {document_context}

            Please provide:
            1. Initial solution recommendation that addresses all departmental requirements. Also if you identify two or more tools that do the same job, think about consolidating them if this would make sense.
            2. Calcualte the ROI based on estimates and the chosen solution. Be specific and explain every step in detail. Describe why each step makes sense, how you came up with the value and how it contributes to the overall goal. If you refer to monetary values, mention in brackets if you got it from the web, your own knowledge or uploaded documents. Consider that the budget does not have to be spent and is only generally available.
            3. Implementation approach considering existing tools and infrastructure. For various stages create individual tasks which have to be done to achieve this phase. Also design an exit criteria of each phase which allows the next one to start.
            4. Key considerations and risks for each department's requirements. Also make one suggestion of how the risk could be mitigated and add it as sub-point of each risk with one hierachy level lower and one tab more inside.
            5. Specific next steps for each department
            6. How the solution meets the success metrics while staying within budget
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
            st.chat_message("assistant").write(
                format_assistant_message(message),
                unsafe_allow_html=True
            )
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
            if st.button("Accept as Final Solution"):
                st.session_state.final_solution = {
                    'inputs': st.session_state.workflow_data,
                    'conversation': st.session_state.solution_chat_history,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.success("Solution accepted! You can now download it as PDF.")
        
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