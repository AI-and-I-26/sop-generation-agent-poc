"""
Few-Shot Examples - File 5/14
Example prompts for better agent outputs

Used by: Content Agent primarily, but available to all agents
"""

# Content Generation Examples
CONTENT_EXAMPLES = """
EXAMPLE 1: Emergency Shutdown Procedure

INPUT:
Section: Emergency Shutdown Procedure
Industry: Manufacturing
Target Audience: Equipment Operators

OUTPUT:
{
  "section_title": "Emergency Shutdown Procedure",
  "content": "## Emergency Shutdown Procedure\\n\\n**Objective:** Safely shut down the system in emergency situations.\\n\\n**When to Use:**\\n- Equipment malfunction\\n- Pressure exceeding 160 PSI\\n- Detected leaks\\n- Fire alarm activation\\n\\n**Procedure:**\\n\\n1. **Alert Personnel**\\n   - Activate emergency alarm immediately\\n   - Announce \\"EMERGENCY SHUTDOWN\\" over PA system\\n   - Ensure all personnel are aware\\n   - Estimated time: 10 seconds\\n\\n2. **Isolate System**\\n   - Locate emergency shutoff valve (Panel A-3, red handle)\\n   - Rotate valve 90° clockwise until resistance stops\\n   - ✓ CHECKPOINT: Flow indicator shows zero\\n   - ⚠️ WARNING: Do not force valve past stop point\\n   - Estimated time: 30 seconds\\n\\n3. **Verify Pressure Drop**\\n   - Observe pressure gauge on Panel A-3\\n   - Wait for pressure to drop below 20 PSI\\n   - ✓ CHECKPOINT: Pressure ≤ 20 PSI within 2 minutes\\n   - ⚡ CRITICAL: If pressure does not drop, activate backup valve at Panel B-7\\n   - Estimated time: 2-3 minutes\\n\\n4. **Secure Area**\\n   - Post \\"DO NOT OPERATE\\" signs at all control points\\n   - Lock out electrical panel using LOTO procedure\\n   - Evacuate non-essential personnel\\n   - Estimated time: 5 minutes\\n\\n5. **Report and Document**\\n   - Notify shift supervisor immediately\\n   - Complete Incident Report Form IR-2024\\n   - Document all pressure readings and timeline\\n   - Estimated time: 10 minutes",
  "safety_warnings": [
    "Do not force valve past stop point - may cause damage",
    "If pressure does not drop within 2 minutes, activate backup isolation valve immediately"
  ],
  "quality_checkpoints": [
    "Flow indicator shows zero after valve closure",
    "Pressure drops to ≤ 20 PSI within 2 minutes",
    "All signs posted and LOTO applied"
  ],
  "time_estimate_minutes": 20
}

---

EXAMPLE 2: Sterile Sample Collection

INPUT:
Section: Sample Collection Procedure
Industry: Laboratory
Target Audience: Lab Technicians

OUTPUT:
{
  "section_title": "Sample Collection Procedure",
  "content": "## Sample Collection Procedure\\n\\n**Objective:** Collect representative samples while maintaining sterility.\\n\\n**Prerequisites:**\\n- Class A biological safety cabinet operational\\n- Sterile collection vessels available\\n- PPE donned (see Section 3.2)\\n\\n**Procedure:**\\n\\n1. **Prepare Work Area**\\n   - Decontaminate biological safety cabinet with 70% IPA\\n   - Wipe down all surfaces using circular motion from center outward\\n   - Allow 2 minutes air dry time\\n   - ✓ CHECKPOINT: No visible residue or pooling\\n   - Estimated time: 5 minutes\\n\\n2. **Assemble Materials**\\n   - Place within cabinet:\\n     * Sterile 50mL collection vessels (quantity: samples + 1 spare)\\n     * Sterile transfer pipettes\\n     * Sampling manifest (Form SM-101)\\n     * Timer\\n   - Arrange from clean to dirty zones (left to right)\\n   - Estimated time: 3 minutes\\n\\n3. **Collect Sample**\\n   - Remove vessel cap using aseptic technique\\n   - Keep cap facing down, do not set on surface\\n   - Transfer 50mL ± 2mL using sterile pipette\\n   - ⚡ CRITICAL: Complete transfer within 30 seconds to minimize exposure\\n   - Replace cap immediately\\n   - ✓ CHECKPOINT: Volume between 48-52mL\\n   - Estimated time: 2 minutes per sample\\n\\n4. **Label and Document**\\n   - Label vessel with:\\n     * Sample ID (format: YYYY-MM-DD-###)\\n     * Date/Time (24-hour format)\\n     * Collector initials\\n     * Storage conditions required\\n   - Record in sampling manifest\\n   - Cross-reference against batch record\\n   - Estimated time: 2 minutes per sample\\n\\n5. **Transport to Storage**\\n   - Place samples in validated transport container\\n   - Add cold packs if required (2-8°C samples)\\n   - Complete chain of custody form\\n   - Transfer to designated storage within 30 minutes\\n   - ✓ CHECKPOINT: Temperature maintained throughout transport\\n   - Estimated time: 5 minutes",
  "safety_warnings": [
    "Samples exposed to non-sterile conditions must be discarded",
    "Complete transfer within 30 seconds to minimize contamination risk",
    "Never recap needles - use sharps container"
  ],
  "quality_checkpoints": [
    "Cabinet surface shows no visible residue after decontamination",
    "Sample volume is between 48-52mL",
    "All documentation complete and cross-referenced",
    "Temperature maintained during transport"
  ],
  "time_estimate_minutes": 15
}
"""


# Planning Examples
PLANNING_EXAMPLES = """
EXAMPLE: Chemical Spill Response SOP

INPUT:
Topic: Chemical Spill Response
Industry: Manufacturing
Target Audience: Floor Supervisors and Safety Personnel

OUTPUT:
{
  "title": "Chemical Spill Response Procedures",
  "industry": "Manufacturing",
  "sections": [
    {
      "number": "1",
      "title": "Purpose and Scope",
      "subsections": ["1.1 Purpose", "1.2 Scope", "1.3 Applicability"]
    },
    {
      "number": "2",
      "title": "Definitions and Abbreviations",
      "subsections": ["2.1 Definitions", "2.2 Abbreviations"]
    },
    {
      "number": "3",
      "title": "Responsibilities",
      "subsections": ["3.1 Floor Supervisors", "3.2 Safety Personnel", "3.3 Production Staff"]
    },
    {
      "number": "4",
      "title": "Required Materials and Equipment",
      "subsections": ["4.1 Spill Kit Contents", "4.2 PPE Requirements", "4.3 Detection Equipment"]
    },
    {
      "number": "5",
      "title": "Safety Requirements",
      "subsections": ["5.1 Personal Protective Equipment", "5.2 Evacuation Criteria", "5.3 Ventilation"]
    },
    {
      "number": "6",
      "title": "Spill Response Procedures",
      "subsections": ["6.1 Assessment", "6.2 Containment", "6.3 Cleanup", "6.4 Disposal"]
    },
    {
      "number": "7",
      "title": "Emergency Procedures",
      "subsections": ["7.1 Large Spills", "7.2 Evacuation Protocol", "7.3 Emergency Contacts"]
    },
    {
      "number": "8",
      "title": "Documentation",
      "subsections": ["8.1 Incident Report", "8.2 Regulatory Reporting"]
    },
    {
      "number": "9",
      "title": "References",
      "subsections": ["9.1 Related SOPs", "9.2 Regulations"]
    }
  ],
  "estimated_pages": 12
}
"""


# QA Review Examples
QA_EXAMPLES = """
EXAMPLE 1: High-Quality SOP (APPROVED)

REVIEW OUTPUT:
{
  "score": 9.2,
  "feedback": "Excellent SOP with comprehensive coverage. Strengths: Clear evacuation routes with specific details, detailed role assignments, appropriate safety warnings throughout. Minor improvements: Add estimated evacuation times for different building sections, include accessibility considerations for mobility-impaired individuals in Section 5.",
  "approved": true,
  "issues": [
    "Section 4.3: Add estimated evacuation time ranges for each zone",
    "Section 5.1: Include specific guidance for assisting mobility-impaired persons"
  ],
  "completeness_score": 9.5,
  "clarity_score": 9.0,
  "compliance_score": 9.0
}

EXAMPLE 2: Needs Revision (NOT APPROVED)

REVIEW OUTPUT:
{
  "score": 6.5,
  "feedback": "SOP has good structure but lacks critical operational details. Missing: specific calibration standards with model numbers, numerical acceptance criteria for measurements, calibration frequency schedule. Safety section does not adequately address electrical hazards. Troubleshooting section is too brief and lacks specific error codes.",
  "approved": false,
  "issues": [
    "Section 6.2: Specify exact calibration standards (model numbers, traceability certificates)",
    "Section 6.3: Add numerical acceptance criteria for each measurement checkpoint",
    "Section 5: Add comprehensive electrical safety warnings and lockout/tagout procedures",
    "Section 9: Expand troubleshooting with specific error codes and step-by-step solutions",
    "Overall: Add calibration frequency schedule with due date tracking"
  ],
  "completeness_score": 6.0,
  "clarity_score": 7.5,
  "compliance_score": 6.0
}
"""


def get_examples_for_agent(agent_type: str) -> str:
    """
    Get few-shot examples for specific agent
    
    Args:
        agent_type: Type of agent (content, planning, qa)
        
    Returns:
        Example string
    """
    examples = {
        "content": CONTENT_EXAMPLES,
        "planning": PLANNING_EXAMPLES,
        "qa": QA_EXAMPLES
    }
    
    return examples.get(agent_type.lower(), "")