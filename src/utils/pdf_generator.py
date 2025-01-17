"""
PDF generation utility for solution export.
"""

from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from io import BytesIO
import streamlit as st

def format_assistant_message(message: str) -> str:
    """
    Format assistant's message for better readability in PDF.
    
    Args:
        message: Raw message from assistant
        
    Returns:
        str: Formatted message
    """
    # Split message into paragraphs
    paragraphs = message.split('\n')
    formatted_paragraphs = []
    
    for para in paragraphs:
        # Check if it's a numbered item (e.g., "1.", "2.", etc.)
        if para.strip() and para.strip()[0].isdigit() and '. ' in para:
            formatted_paragraphs.append(f"\n{para.strip()}")
        # Check if it's a sub-bullet point
        elif para.strip().startswith('-') or para.strip().startswith('•'):
            formatted_paragraphs.append(f"   {para.strip()}")
        # Check if it's a section header (all caps or ends with ':')
        elif para.strip().isupper() or para.strip().endswith(':'):
            formatted_paragraphs.append(f"\n{para.strip()}")
        else:
            formatted_paragraphs.append(para.strip())
    
    return '\n'.join(p for p in formatted_paragraphs if p)

def generate_solution_pdf(solution_data: dict) -> bytes:
    """
    Generate a PDF report from the solution data.
    
    Args:
        solution_data: Dictionary containing solution information
        
    Returns:
        bytes: PDF file content
    """
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        styles.add(ParagraphStyle(
            name='MainHeading',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        ))
        
        styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10
        ))
        
        styles.add(ParagraphStyle(
            name='SubHeading',
            parent=styles['Heading3'],
            fontSize=12,
            spaceBefore=15,
            spaceAfter=5
        ))
        
        styles.add(ParagraphStyle(
            name='BulletPoint',
            parent=styles['Normal'],
            fontSize=10,
            leftIndent=20,
            spaceBefore=5
        ))
        
        # Title
        story.append(Paragraph("Solution Analysis Report", styles['MainHeading']))
        story.append(Spacer(1, 20))
        
        # Problem Statement
        story.append(Paragraph("Problem Statement", styles['SectionHeading']))
        story.append(Paragraph(str(solution_data['inputs'].get('problem', 'N/A')), styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Requirements section
        if solution_data['inputs'].get('requirements'):
            story.append(Paragraph("Requirements", styles['SectionHeading']))
            requirements_data = [[
                Paragraph("Department", styles['SubHeading']), 
                Paragraph("Requirement", styles['SubHeading'])
            ]]
            for req in solution_data['inputs']['requirements']:
                requirements_data.append([
                    Paragraph(req['department'], styles['Normal']),
                    Paragraph(req['requirement'], styles['Normal'])
                ])
            
            req_table = Table(requirements_data, colWidths=[150, 350])
            req_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(req_table)
            story.append(Spacer(1, 20))
        
        # Solution Evolution
        story.append(Paragraph("Solution Evolution", styles['SectionHeading']))
        for role, message in solution_data['conversation']:
            if role != "System":
                # Role header
                role_style = ParagraphStyle(
                    'Role',
                    parent=styles['Normal'],
                    textColor=colors.black if role == "Assistant" else colors.green,
                    fontSize=12,
                    spaceBefore=15,
                    bold=True
                )
                story.append(Paragraph(f"{role}:", role_style))
                
                # Format message content
                if role == "Assistant":
                    formatted_message = format_assistant_message(message)
                    # Split into paragraphs and format each
                    for para in formatted_message.split('\n'):
                        if para.strip():
                            if para.strip()[0].isdigit() and '. ' in para:
                                # Numbered items
                                story.append(Paragraph(para, styles['SubHeading']))
                            elif para.strip().startswith(('   -', '   •')):
                                # Sub-bullets
                                story.append(Paragraph(para, styles['BulletPoint']))
                            elif para.strip().isupper() or para.strip().endswith(':'):
                                # Section headers
                                story.append(Paragraph(para, styles['SubHeading']))
                            else:
                                # Normal paragraphs
                                story.append(Paragraph(para, styles['Normal']))
                else:
                    # User messages
                    story.append(Paragraph(message, styles['Normal']))
                
                story.append(Spacer(1, 10))
        
        # Final Notes
        story.append(Spacer(1, 30))
        story.append(Paragraph("Generated on: " + str(solution_data.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))), styles['Italic']))
        
        # Build PDF
        doc.build(story)
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
        
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        raise e