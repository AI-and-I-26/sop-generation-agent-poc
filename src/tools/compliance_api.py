"""
Compliance API Tool - File 8/14
Retrieves compliance and regulatory requirements

Used by: Research Agent
"""

import json
import logging
from strands.tools import Tool

logger = logging.getLogger(__name__)


class ComplianceAPITool:
    """
    Compliance Requirements Tool for Strands
    
    Provides relevant regulatory information based on industry.
    Currently uses a knowledge base - can be extended with external APIs.
    """
    
    def __init__(self):
        """Initialize compliance tool"""
        # Compliance knowledge base (can be replaced with external API)
        self.compliance_db = {
            "Manufacturing": [
                "OSHA 1910 - General Industry Standards",
                "ISO 9001:2015 - Quality Management",
                "EPA 40 CFR - Environmental Protection",
                "ANSI Z535 - Safety Signs and Tags"
            ],
            "Healthcare": [
                "HIPAA - Health Insurance Portability",
                "FDA 21 CFR Part 820 - Quality System Regulation",
                "OSHA 1910.1030 - Bloodborne Pathogens",
                "Joint Commission Standards"
            ],
            "Laboratory": [
                "CLIA - Clinical Laboratory Improvement Amendments",
                "CAP Laboratory Accreditation Standards",
                "OSHA 1910.1450 - Laboratory Standard",
                "ISO/IEC 17025 - Testing and Calibration"
            ],
            "Food": [
                "FDA Food Safety Modernization Act (FSMA)",
                "HACCP - Hazard Analysis Critical Control Points",
                "GMP - Good Manufacturing Practices",
                "ISO 22000 - Food Safety Management"
            ],
            "Chemical": [
                "OSHA 1910.1200 - Hazard Communication",
                "EPA TSCA - Toxic Substances Control Act",
                "DOT Hazmat Regulations",
                "REACH - Registration, Evaluation, Authorization"
            ],
            "Pharmaceutical": [
                "FDA 21 CFR Part 211 - cGMP",
                "ICH Guidelines - International Council for Harmonisation",
                "USP Standards - United States Pharmacopeia",
                "EU GMP Guidelines"
            ],
            "Construction": [
                "OSHA 1926 - Construction Standards",
                "Building Codes (IBC, IRC)",
                "ANSI/ASSP Z359 - Fall Protection",
                "NFPA Codes - Fire Protection"
            ],
            "Office": [
                "OSHA General Duty Clause",
                "Fire Safety Codes (NFPA 101)",
                "ADA - Americans with Disabilities Act",
                "Emergency Action Plan (OSHA 1910.38)"
            ]
        }
        
        logger.info("✓ Initialized Compliance API tool")
    
    def get_requirements(self, industry: str, topic: str = "") -> str:
        """
        Get compliance requirements for industry and topic
        
        Args:
            industry: Industry name
            topic: Specific topic (optional)
            
        Returns:
            JSON string with compliance requirements
        """
        
        # Get base requirements for industry
        requirements = self.compliance_db.get(industry, [])
        
        # If no exact match, try partial match
        if not requirements:
            for key in self.compliance_db.keys():
                if industry.lower() in key.lower():
                    requirements = self.compliance_db[key]
                    break
        
        # Default to general requirements if nothing found
        if not requirements:
            requirements = [
                "General workplace safety standards (OSHA)",
                "Environmental compliance (EPA)",
                "Industry-specific regulations (contact regulatory affairs)"
            ]
        
        # Add topic-specific requirements if provided
        topic_requirements = []
        if topic:
            topic_lower = topic.lower()
            if 'fire' in topic_lower or 'emergency' in topic_lower:
                topic_requirements.extend([
                    "NFPA 101 - Life Safety Code",
                    "Emergency Action Plan requirements",
                    "Fire extinguisher training and placement"
                ])
            elif 'chemical' in topic_lower or 'hazard' in topic_lower:
                topic_requirements.extend([
                    "OSHA Hazard Communication Standard",
                    "SDS (Safety Data Sheet) requirements",
                    "Chemical storage regulations"
                ])
            elif 'equipment' in topic_lower or 'machine' in topic_lower:
                topic_requirements.extend([
                    "Machine guarding standards",
                    "Lockout/Tagout procedures",
                    "Equipment maintenance requirements"
                ])
        
        result = {
            "industry": industry,
            "topic": topic,
            "general_requirements": requirements,
            "topic_specific_requirements": topic_requirements,
            "total_requirements": len(requirements) + len(topic_requirements)
        }
        
        logger.info(f"✓ Found {result['total_requirements']} requirements for {industry}")
        
        return json.dumps(result, indent=2)
    
    def create_strands_tool(self) -> Tool:
        """
        Create Strands Tool for compliance lookup
        
        Returns:
            Strands Tool object
        """
        
        return Tool(
            name="get_compliance_requirements",
            description="Get relevant compliance and regulatory requirements for a specific industry and topic. Returns applicable standards, regulations, and guidelines.",
            function=self.get_requirements,
            parameters={
                "industry": {
                    "type": "string",
                    "description": "Industry name (e.g., 'Manufacturing', 'Healthcare', 'Laboratory')"
                },
                "topic": {
                    "type": "string",
                    "description": "Specific topic or procedure (optional, e.g., 'fire safety', 'chemical handling')",
                    "default": ""
                }
            }
        )


# Convenience function
def create_compliance_tool() -> Tool:
    """
    Create and return compliance tool
    
    Returns:
        Strands Tool configured for compliance lookup
        
    Example:
        >>> compliance_tool = create_compliance_tool()
        >>> agent = Agent(name="Research", tools=[compliance_tool])
    """
    compliance = ComplianceAPITool()
    return compliance.create_strands_tool()
