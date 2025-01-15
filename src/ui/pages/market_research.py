"""
Market Research page functionality.
"""

import streamlit as st
from typing import List
from langchain_community.utilities import SerpAPIWrapper
from src.agents.market_research_agent import MarketResearchAgent

def show_market_research():
    """Display the market research interface and handle research workflow."""
    st.title("Market Research Analysis 🔍")
    
    # Input section
    st.markdown("""
    ### Market Research Query
    Enter a specific market, product, or trend you want to research. 
    The tool will:
    1. Search for relevant sources
    2. Analyze top results
    3. Generate a comprehensive report
    
    Examples:
    - Electric vehicle charging infrastructure market
    - B2B software purchasing trends
    - Enterprise collaboration tools market size
    """)
    
    query = st.text_input("Research Query")
    num_sources = st.slider("Number of sources to analyze", 3, 10, 5)
    
    if query:
        if st.button("Conduct Research"):
            _handle_market_research(query, num_sources)

def _handle_market_research(query: str, num_sources: int):
    """
    Handle the market research workflow.
    
    Args:
        query: Research query string
        num_sources: Number of sources to analyze
    """
    with st.spinner("Searching and analyzing sources..."):
        try:
            # Initialize search
            search = SerpAPIWrapper()
            
            # First progress message
            progress_text = st.empty()
            progress_text.text("🔍 Searching for relevant sources...")
            
            # Perform search and get URLs
            search_results = search.results(query)
            urls = _extract_urls(search_results, num_sources)
            
            if not urls:
                st.error("No valid sources found. Please try a different query.")
                return
            
            # Update progress
            progress_text.text("📊 Analyzing content from sources...")
            
            # Create agent and analyze results
            agent = MarketResearchAgent()
            report = agent.research(query, urls)
            
            # Clear progress message
            progress_text.empty()
            
            _display_research_results(report, urls)
            
        except Exception as e:
            st.error(f"Error during research: {str(e)}")
            st.markdown("Detailed error information:")
            st.code(str(e))

def _extract_urls(search_results: dict, num_sources: int) -> List[str]:
    """
    Extract URLs from search results.
    
    Args:
        search_results: Raw search results from SerpAPI
        num_sources: Number of sources to extract
        
    Returns:
        List[str]: List of extracted URLs
    """
    urls = []
    for result in search_results.get("organic_results", [])[:num_sources]:
        if "link" in result:
            urls.append(result["link"])
    return urls

def _display_research_results(report: dict, urls: List[str]):
    """
    Display the research results in a structured format.
    
    Args:
        report: Research report dictionary
        urls: List of analyzed URLs
    """
    if "error" in report:
        st.error(report["error"])
        return

    st.markdown("## Market Research Report")
    
    # Market Size and Growth
    st.markdown("### Market Size & Growth")
    if report.get("market_size"):
        st.write(f"**Market Size:** {report['market_size']}")
    if report.get("growth_rate"):
        st.write(f"**Growth Rate:** {report['growth_rate']}")
    
    # Key Players
    if report.get("key_players"):
        st.markdown("### Key Players")
        for player in report["key_players"]:
            st.markdown(f"- {player}")
    
    # Trends
    if report.get("trends"):
        st.markdown("### Key Trends")
        for trend in report["trends"]:
            st.markdown(f"- {trend}")
    
    # Opportunities and Challenges
    col1, col2 = st.columns(2)
    with col1:
        if report.get("opportunities"):
            st.markdown("### Opportunities")
            for opp in report["opportunities"]:
                st.markdown(f"- {opp}")
    
    with col2:
        if report.get("challenges"):
            st.markdown("### Challenges")
            for challenge in report["challenges"]:
                st.markdown(f"- {challenge}")
    
    # Sources
    with st.expander("Sources Analyzed"):
        for i, url in enumerate(urls, 1):
            st.markdown(f"{i}. [{url}]({url})") 