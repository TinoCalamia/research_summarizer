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
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        story.append(Paragraph("Solution Analysis Report", title_style))
        story.append(Spacer(1, 20))
        
        # Problem Statement
        story.append(Paragraph("Problem Statement", styles['Heading2']))
        story.append(Paragraph(str(solution_data['inputs'].get('problem', 'N/A')), styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Add Requirements section
        if solution_data['inputs'].get('requirements'):
            story.append(Paragraph("Requirements", styles['Heading2']))
            requirements_data = [[
                Paragraph("Department", styles['Heading4']), 
                Paragraph("Requirement", styles['Heading4'])
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
        
        # Company Context
        story.append(Paragraph("Company Context", styles['Heading2']))
        company_params = solution_data['inputs'].get('company_params', {})
        context_data = [
            ["Industry", company_params.get('industry', 'N/A')],
            ["Company Size", company_params.get('company_size', 'N/A')],
            ["Budget", company_params.get('budget', 'N/A')],
            ["Success Metric", company_params.get('success_metric', 'N/A')]
        ]
        context_table = Table(context_data, colWidths=[150, 350])
        context_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(context_table)
        story.append(Spacer(1, 20))
        
        # Tools Used
        story.append(Paragraph("Current Tools", styles['Heading2']))
        tools = solution_data['inputs'].get('tools', {})
        for category, tool_list in tools.items():
            if tool_list:  # Only show categories with selected tools
                story.append(Paragraph(f"{category}:", styles['Heading4']))
                story.append(Paragraph(", ".join(tool_list), styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Solution Evolution
        story.append(Paragraph("Solution Evolution", styles['Heading2']))
        for role, message in solution_data['conversation']:
            if role != "System":
                role_style = ParagraphStyle(
                    'Role',
                    parent=styles['Normal'],
                    textColor=colors.blue if role == "Assistant" else colors.dark_green,
                    fontSize=10,
                    spaceBefore=15
                )
                story.append(Paragraph(f"{role}:", role_style))
                story.append(Paragraph(str(message), styles['Normal']))
        
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