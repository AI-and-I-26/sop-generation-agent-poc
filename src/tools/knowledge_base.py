"""
Knowledge Base Tool - File 6/14
RAG implementation using Bedrock Knowledge Base

Used by: Research Agent
"""

import os
import json
import logging
from typing import List, Dict
import boto3
from strands.tools import Tool

logger = logging.getLogger(__name__)


class KnowledgeBaseTool:
    """
    Bedrock Knowledge Base RAG Tool for Strands
    
    Provides semantic search across SOP documentation.
    """
    
    def __init__(self):
        """Initialize KB client"""
        self.kb_id = os.getenv('KNOWLEDGE_BASE_ID')
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        
        if not self.kb_id:
            logger.warning("KNOWLEDGE_BASE_ID not set - KB tool will return mock data")
            self.client = None
        else:
            self.client = boto3.client(
                'bedrock-agent-runtime',
                region_name=self.region
            )
            logger.info(f"✓ Initialized KB tool with ID: {self.kb_id}")
    
    def search(self, query: str, max_results: int = 5) -> str:
        """
        Search Bedrock Knowledge Base
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            JSON string with results
        """
        
        if not self.client:
            # Return mock data if KB not configured
            logger.info(f"Returning mock KB results for: {query}")
            return json.dumps({
                "results": [
                    {
                        "content": f"Mock KB result for query: {query}",
                        "score": 0.85,
                        "source": "mock-source.pdf"
                    }
                ],
                "query": query
            })
        
        try:
            response = self.client.retrieve(
                knowledgeBaseId=self.kb_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results
                    }
                }
            )
            
            results = []
            for result in response.get('retrievalResults', []):
                results.append({
                    'content': result['content']['text'],
                    'score': result['score'],
                    'source': result.get('location', {}).get('s3Location', {}).get('uri', 'Unknown')
                })
            
            logger.info(f"✓ KB search found {len(results)} results for: {query}")
            
            return json.dumps({
                "results": results,
                "query": query
            })
            
        except Exception as e:
            logger.error(f"KB search error: {e}")
            return json.dumps({
                "error": str(e),
                "query": query
            })
    
    def create_strands_tool(self) -> Tool:
        """
        Create Strands Tool for research agent
        
        Returns:
            Strands Tool object
        """
        
        return Tool(
            name="search_knowledge_base",
            description="Search Bedrock Knowledge Base for similar SOPs, procedures, and best practices. Returns relevant documentation with relevance scores.",
            function=self.search,
            parameters={
                "query": {
                    "type": "string",
                    "description": "Search query (e.g., 'fire safety procedures', 'equipment calibration')"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default 5)",
                    "default": 5
                }
            }
        )


# Convenience function to create the tool
def create_kb_tool() -> Tool:
    """
    Create and return KB tool for use in agents
    
    Returns:
        Strands Tool configured for KB search
        
    Example:
        >>> kb_tool = create_kb_tool()
        >>> agent = Agent(name="Research", tools=[kb_tool])
    """
    kb = KnowledgeBaseTool()
    return kb.create_strands_tool()
