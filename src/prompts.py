def create_basic_prompt():
    return  """Answer the question based only on the following context:
            {context}

            Analyze the following user interview transcript carefully. This interview is aimed at understanding key challenges, pain points, and opportunities in the sales process for [Company/Product/Service]. As you read, identify and structure the insights into the following categories:

            1. Pain Points: Specific challenges or frustrations expressed by the user related to sales activities. Be attentive to difficulties such as:
            Lead generation and qualification issues (e.g., time-consuming processes, low-quality leads).
            Conversion challenges (e.g., handling objections, customer decision delays).
            Follow-up processes (e.g., lack of automation, difficulty in tracking customer responses).
            Sales productivity issues (e.g., repetitive tasks, difficulty in accessing information).
            Any expressed dissatisfaction with current tools or processes.
            
            2. Opportunities for Improvement: Identify statements or hints that suggest unmet needs or potential enhancements. This includes:
            New features or capabilities the user wishes they had (e.g., better CRM integration, improved reporting).
            Specific requests for automation in areas such as follow-ups, reminders, or data entry.
            Suggestions or requests for improved insights or analytics (e.g., customer behavior insights, sales forecasting).
            Gaps in existing tools that the user believes hinder sales performance.
            
            3. Positive Insights and Successful Practices: Note any aspects that the user finds beneficial or successful within their current workflow, such as:
            Techniques or tools that contribute positively to their productivity.
            Positive feedback on specific features or processes that could be enhanced or replicated.
            Mention of strategies that work well in building customer relationships.
            
            4. Additional Considerations: Capture any other details relevant to understanding the user’s perspective, including:
            Desired outcomes or goals the user is trying to achieve (e.g., shorter sales cycles, higher close rates).
            Insights into how the user measures success in sales and areas they believe could have the most impact.
            Any emotional language that indicates strong feelings (e.g., frustration, enthusiasm) about certain aspects of the sales process.
            
            After completing the analysis, structure the output in the following format:

            Pain Points: [List specific pain points]
            Opportunities for Improvement: [List improvement opportunities]
            Positive Insights and Successful Practices: [List positive aspects]
            Additional Considerations: [Other relevant insights]
            Be thorough and consider the implications of each point, aiming to provide a comprehensive understanding of the user’s needs, frustrations, and potential areas for growth within the sales process.

            Question: {question}
            """