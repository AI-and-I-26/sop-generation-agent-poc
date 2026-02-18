"""
S3 Search Tool - File 7/14
Search and retrieve documents from S3

Used by: Research Agent (optional tool)
"""

import os
import json
import logging
from typing import List, Dict
import boto3
from strands.tools import Tool

logger = logging.getLogger(__name__)


class S3SearchTool:
    """
    S3 Document Search Tool for Strands
    
    Searches for and retrieves documents from S3 bucket.
    """
    
    def __init__(self):
        """Initialize S3 client"""
        self.bucket = os.getenv('SOP_BUCKET')
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        
        if not self.bucket:
            logger.warning("SOP_BUCKET not set - S3 tool will return mock data")
            self.client = None
        else:
            self.client = boto3.client('s3', region_name=self.region)
            logger.info(f"✓ Initialized S3 tool with bucket: {self.bucket}")
    
    def search_documents(self, keyword: str, max_results: int = 10) -> str:
        """
        Search for documents in S3 by keyword
        
        Args:
            keyword: Search keyword
            max_results: Maximum results
            
        Returns:
            JSON string with document list
        """
        
        if not self.client:
            logger.info(f"Returning mock S3 results for: {keyword}")
            return json.dumps({
                "documents": [
                    {
                        "key": f"sops/mock-{keyword}.pdf",
                        "size": 1024000,
                        "last_modified": "2024-01-01T00:00:00Z"
                    }
                ],
                "keyword": keyword
            })
        
        try:
            # List objects with prefix
            response = self.client.list_objects_v2(
                Bucket=self.bucket,
                Prefix='sops/',
                MaxKeys=max_results
            )
            
            documents = []
            for obj in response.get('Contents', []):
                # Simple keyword matching
                if keyword.lower() in obj['Key'].lower():
                    documents.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat()
                    })
            
            logger.info(f"✓ Found {len(documents)} documents matching: {keyword}")
            
            return json.dumps({
                "documents": documents,
                "keyword": keyword,
                "bucket": self.bucket
            })
            
        except Exception as e:
            logger.error(f"S3 search error: {e}")
            return json.dumps({
                "error": str(e),
                "keyword": keyword
            })
    
    def get_document(self, key: str) -> str:
        """
        Retrieve document content from S3
        
        Args:
            key: S3 object key
            
        Returns:
            JSON string with document content (first 5000 chars)
        """
        
        if not self.client:
            return json.dumps({
                "content": f"Mock content for {key}",
                "key": key
            })
        
        try:
            response = self.client.get_object(
                Bucket=self.bucket,
                Key=key
            )
            
            # Read content (limit to 5000 chars)
            content = response['Body'].read().decode('utf-8', errors='ignore')[:5000]
            
            logger.info(f"✓ Retrieved document: {key}")
            
            return json.dumps({
                "content": content,
                "key": key,
                "size": len(content)
            })
            
        except Exception as e:
            logger.error(f"S3 get error: {e}")
            return json.dumps({
                "error": str(e),
                "key": key
            })
    
    def create_strands_tool(self) -> Tool:
        """
        Create Strands Tool for S3 search
        
        Returns:
            Strands Tool object
        """
        
        return Tool(
            name="search_s3_documents",
            description="Search for SOP documents stored in S3 bucket. Returns list of matching documents with metadata.",
            function=self.search_documents,
            parameters={
                "keyword": {
                    "type": "string",
                    "description": "Search keyword (e.g., 'safety', 'calibration')"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default 10)",
                    "default": 10
                }
            }
        )


# Convenience function
def create_s3_tool() -> Tool:
    """
    Create and return S3 search tool
    
    Returns:
        Strands Tool configured for S3 search
    """
    s3 = S3SearchTool()
    return s3.create_strands_tool()
