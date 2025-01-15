def create_basic_prompt():
    return  """Analyze the provided context carefully and answer the question based solely on the information provided.

Context:
{context}

Objective: Extract and structure actionable insights from the user interview transcript. The purpose of this analysis is to identify challenges, unmet needs, opportunities for growth, and areas of success in the sales process for [Company/Product/Service]. Use the following categories to organize your findings:

1. **High-Priority Pain Points:** Identify specific challenges or frustrations expressed by the user. Focus on recurring issues and their impact. Consider:
   - Lead generation and qualification (e.g., time-consuming processes, low-quality leads).
   - Conversion difficulties (e.g., handling objections, decision delays).
   - Follow-up inefficiencies (e.g., limited automation, inconsistent tracking).
   - Productivity barriers (e.g., manual tasks, tool limitations, inaccessible information).
   - Any dissatisfaction with current tools or processes.

2. **Opportunities for Improvement:** Highlight unmet needs or suggestions for enhancement. Focus on frequent mentions or high-value opportunities, including:
   - Feature or tool requests (e.g., CRM integration, advanced reporting).
   - Automation needs (e.g., follow-ups, reminders, data entry).
   - Improved insights and analytics (e.g., customer behavior analysis, trend forecasting).
   - Workflow or process gaps impacting sales performance.

3. **Positive Insights and Successful Practices:** Capture any feedback on what the user finds beneficial or effective, such as:
   - Successful techniques (e.g., personalized outreach, strong follow-up strategies).
   - Positive experiences with specific tools or processes.
   - Strategies that contribute to productivity or customer relationship success.

4. **Additional Considerations:** Note any other relevant details that provide context for understanding the user’s perspective, including:
   - Desired outcomes or goals (e.g., shorter sales cycles, increased close rates).
   - How the user measures success and where they believe improvements would be most impactful.
   - Emotional cues indicating strong feelings about aspects of the process (e.g., frustration, enthusiasm).

Structure your analysis in the following format:
---
Pain Points: [List specific challenges and their frequency/impact]
Opportunities for Improvement: [List improvement opportunities and potential benefits]
Positive Insights and Successful Practices: [List positive aspects and potential for replication]
Additional Considerations: [List other relevant insights or contextual details]
---

Be comprehensive and ensure that frequently mentioned or high-impact insights are prioritized. Use the analysis to provide a detailed understanding of the user’s needs, frustrations, and growth opportunities.
IGNORE PROBLEMS DESCRIBED BY THE INTERVIEWERS.
Question: {question}

            """