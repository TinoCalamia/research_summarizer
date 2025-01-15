"""
Market Research Agent module for web scraping and content analysis.
"""

from typing import Dict, List
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import BeautifulSoupTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import create_extraction_chain
from langchain_openai import ChatOpenAI
from src.config.schema import MARKET_RESEARCH_SCHEMA

class MarketResearchAgent:
    """
    Agent for conducting market research using web sources.
    
    This agent handles web scraping, content extraction, and analysis of market research data.
    
    Attributes:
        llm: Language model instance for content analysis
        schema: Schema definition for content extraction
    """
    
    def __init__(self):
        """Initialize the market research agent with necessary components."""
        self.llm = ChatOpenAI(temperature=0, model="gpt-4o")
        self.schema = MARKET_RESEARCH_SCHEMA

    def extract_content(self, content: str) -> Dict:
        """
        Extract structured information from text content using LLM.
        
        Args:
            content: Raw text content to analyze
            
        Returns:
            Dict: Extracted structured information
        """
        return create_extraction_chain(schema=self.schema, llm=self.llm).run(content)

    def scrape_with_playwright(self, urls: List[str]) -> Dict:
        """
        Scrape content from provided URLs using Playwright.
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            Dict: Processed and synthesized results
        """
        try:
            loader = AsyncChromiumLoader(urls)
            docs = loader.load()
            
            bs_transformer = BeautifulSoupTransformer()
            docs_transformed = bs_transformer.transform_documents(
                docs, 
                tags_to_extract=["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "div"]
            )

            splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                chunk_size=2000, 
                chunk_overlap=200
            )
            splits = splitter.split_documents(docs_transformed)

            all_results = []
            for split in splits[:3]:
                extracted_content = self.extract_content(split.page_content)
                if extracted_content:
                    all_results.extend(extracted_content)

            return self.synthesize_results(all_results)
            
        except Exception as e:
            return {
                "error": f"Error during scraping: {str(e)}",
                "partial_results": all_results if 'all_results' in locals() else []
            }

    def synthesize_results(self, results: List[Dict]) -> Dict:
        """
        Synthesize multiple extraction results into a single report.
        
        Args:
            results: List of extracted results to synthesize
            
        Returns:
            Dict: Synthesized report
        """
        if not results:
            return None

        synthesis = {
            "market_size": "",
            "growth_rate": "",
            "key_players": set(),
            "trends": set(),
            "challenges": set(),
            "opportunities": set()
        }

        for result in results:
            if isinstance(result, dict):
                if "market_size" in result and result["market_size"]:
                    synthesis["market_size"] = result["market_size"]
                if "growth_rate" in result and result["growth_rate"]:
                    synthesis["growth_rate"] = result["growth_rate"]
                if "key_players" in result:
                    synthesis["key_players"].update(result["key_players"])
                if "trends" in result:
                    synthesis["trends"].update(result["trends"])
                if "challenges" in result:
                    synthesis["challenges"].update(result["challenges"])
                if "opportunities" in result:
                    synthesis["opportunities"].update(result["opportunities"])

        return {k: list(v) if isinstance(v, set) else v for k, v in synthesis.items()}

    def research(self, query: str, urls: List[str]) -> Dict:
        """
        Conduct market research on specific URLs.
        
        Args:
            query: Research query string
            urls: List of URLs to analyze
            
        Returns:
            Dict: Research results and analysis
        """
        try:
            results = self.scrape_with_playwright(urls)
            return results
        except Exception as e:
            return {
                "error": f"Error during research: {str(e)}",
                "results": None
            } 