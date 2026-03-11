(.venv) C:\Users\cr242786\sop-strands-agent - poc>set KNOWLEDGE_BASE_ID=1NR6BI4TNO

(.venv) C:\Users\cr242786\sop-strands-agent - poc>set AWS_REGION=us-east-2

(.venv) C:\Users\cr242786\sop-strands-agent - poc>set RESEARCH_MAX_TOKENS=15000

(.venv) C:\Users\cr242786\sop-strands-agent - poc>set RESEARCH_MAX_ATTEMPTS=2

(.venv) C:\Users\cr242786\sop-strands-agent - poc>set CONTENT_MAX_TOKENS = 7000

(.venv) C:\Users\cr242786\sop-strands-agent - poc>set CONTENT_MAX_TOKENS_PER_SECTION=6000

(.venv) C:\Users\cr242786\sop-strands-agent - poc>set CONTENT_MAX_FACTS_PER_SECTION=10

(.venv) C:\Users\cr242786\sop-strands-agent - poc>set CONTENT_MAX_CITES_PER_SECTION=6

(.venv) C:\Users\cr242786\sop-strands-agent - poc>set FORMATTING_MAX_TOKENS =7000

(.venv) C:\Users\cr242786\sop-strands-agent - poc>set CONTENT_MAX_JSON_BYTES=100000

(.venv) C:\Users\cr242786\sop-strands-agent - poc>set FORMATTER_READ_TIMEOUT=400 

(.venv) C:\Users\cr242786\sop-strands-agent - poc>set FORMATTER_MAX_JSON_BYTES=50000 

(.venv) C:\Users\cr242786\sop-strands-agent - poc>set FORMATTER_MAX_CONCURRENCY=2 

(.venv) C:\Users\cr242786\sop-strands-agent - poc>set FORMATTER_MAX_ATTEMPTS=3

(.venv) C:\Users\cr242786\sop-strands-agent - poc>python -m app.test.custom_sop
2026-03-11 11:26:45 - botocore.credentials - INFO - Found credentials in shared credentials file: C:\Users\cr242786\sop-strands-agent - poc\app\.aws\credentials
2026-03-11 11:26:46 - botocore.credentials - INFO - Found credentials in shared credentials file: C:\Users\cr242786\sop-strands-agent - poc\app\.aws\credentials
2026-03-11 11:26:46 - src.agents.content_agent - INFO - Content caps | TOKENS/section=6000, FACTS/section=10, CITES/section=6, PROCEDURE_SPLIT_MIN=4
2026-03-11 11:26:46 - botocore.credentials - INFO - Found credentials in shared credentials file: C:\Users\cr242786\sop-strands-agent - poc\app\.aws\credentials
C:\Users\cr242786\sop-strands-agent - poc\app\src\agents\formatter_agent.py:62: UserWarning: Invalid configuration parameters: ['client_config', 'region'].
Valid parameters are: ['additional_args', 'additional_request_fields', 'additional_response_field_paths', 'cache_prompt', 'cache_tools', 'guardrail_id', 'guardrail_redact_input', 'guardrail_redact_input_message', 'guardrail_redact_output', 'guardrail_redact_output_message', 'guardrail_stream_processing_mode', 'guardrail_trace', 'guardrail_version', 'include_tool_result_status', 'max_tokens', 'model_id', 'stop_sequences', 'streaming', 'temperature', 'top_p'].

See https://github.com/strands-agents/sdk-python/issues/815
  return BedrockModel(model_id=model_id, region=_REGION, client_config=client_config)  # type: ignore[arg-type]
2026-03-11 11:26:46 - botocore.credentials - INFO - Found credentials in shared credentials file: C:\Users\cr242786\sop-strands-agent - poc\app\.aws\credentials
C:\Users\cr242786\sop-strands-agent - poc\app\src\agents\qa_agent.py:41: UserWarning: Invalid configuration parameters: ['region'].
Valid parameters are: ['additional_args', 'additional_request_fields', 'additional_response_field_paths', 'cache_prompt', 'cache_tools', 'guardrail_id', 'guardrail_redact_input', 'guardrail_redact_input_message', 'guardrail_redact_output', 'guardrail_redact_output_message', 'guardrail_stream_processing_mode', 'guardrail_trace', 'guardrail_version', 'include_tool_result_status', 'max_tokens', 'model_id', 'stop_sequences', 'streaming', 'temperature', 'top_p'].

See https://github.com/strands-agents/sdk-python/issues/815
  return BedrockModel(model_id=_get_model_id(env_var), region=_REGION)
2026-03-11 11:26:47 - botocore.credentials - INFO - Found credentials in shared credentials file: C:\Users\cr242786\sop-strands-agent - poc\app\.aws\credentials
2026-03-11 11:26:47 - strands.multiagent.graph - WARNING - Graph without execution limits may run indefinitely if cycles exist

============================================================
SOP Generation Starting...
  Topic:    Global Technology Infrastructure Qualification SOP
  Industry: Life Science
  Audience: IT Infrastructure Engineers and System Administrators responsible for managing on-premises and cloud infrastructure
============================================================

2026-03-11 11:26:48 - src.graph.sop_workflow - INFO - ============================================================
2026-03-11 11:26:48 - src.graph.sop_workflow - INFO - SOP Generation START | topic='Global Technology Infrastructure Qualification SOP' | industry='Life Science'
2026-03-11 11:26:48 - src.graph.sop_workflow - INFO - workflow_id: sop-6828956471617685896
2026-03-11 11:26:48 - src.graph.sop_workflow - INFO - ============================================================
2026-03-11 11:26:48 - strands.telemetry.metrics - INFO - Creating Strands MetricsClient

Tool #1: run_planning
2026-03-11 11:26:51 - src.agents.planning_agent - INFO - >>> run_planning called | prompt: workflow_id::sop-6828956471617685896 | Generate a Standard Operating Procedure for: Global Technology Infrastructure Qua
2026-03-11 11:26:51 - src.agents.planning_agent - INFO - State found | topic='Global Technology Infrastructure Qualification SOP' industry='Life Science'
2026-03-11 11:26:51 - src.agents.planning_agent - INFO - Using model: arn:aws:bedrock:us-east-2:070797854596:inference-profile/global.anthropic.claude-sonnet-4-6
2026-03-11 11:26:51 - botocore.credentials - INFO - Found credentials in shared credentials file: C:\Users\cr242786\sop-strands-agent - poc\app\.aws\credentials
2026-03-11 11:27:02 - src.agents.planning_agent - INFO - Planning complete — 8 sections | workflow_id=sop-6828956471617685896
# 🏥 Global Technology Infrastructure Qualification SOP

**Industry:** Life Science
**Audience:** IT Infrastructure Engineers and System Administrators
**Document Type:** Standard Operating Procedure
**Workflow ID:** sop-6828956471617685896

---

## 📋 Table of Contents

1. [Purpose](#1-purpose)
2. [Scope](#2-scope)
3. [Roles and Responsibilities](#3-roles-and-responsibilities)
4. [Prerequisites and Required Resources](#4-prerequisites-and-required-resources)
5. [Infrastructure Qualification Procedure](#5-infrastructure-qualification-procedure)
6. [Acceptance Criteria and Testing Protocols](#6-acceptance-criteria-and-testing-protocols)
7. [Documentation and Change Control](#7-documentation-and-change-control)
8. [Compliance, Deviation Management, and References](#8-compliance-deviation-management-and-references)

---

## 1. Purpose

This Standard Operating Procedure (SOP) establishes a standardized, repeatable, and auditable process for qualifying global technology infrastructure components — including on-premises servers, network devices, storage systems, virtualization platforms, and cloud-based infrastructure — within a Life Science organization.

The purpose of this SOP is to:

- Ensure all IT infrastructure components that support **GxP-regulated systems** (GMP, GLP, GCP) and **non-GxP critical systems** meet defined qualification requirements before being placed into production.
- Provide IT Infrastructure Engineers and System Administrators with a structured framework aligned with **GAMP 5**, **21 CFR Part 11**, **EU Annex 11**, and **ICH Q9/Q10** guidelines.  
- Minimize the risk of infrastructure failures that could impact patient safety, data integrity, or regulatory compliance.
- Maintain a continuously qualified and audit-ready infrastructure estate across all global sites and cloud environments.

---

## 2. Scope

### 2.1 In Scope

This SOP applies to all IT infrastructure components that:

| Category | Examples |
|---|---|
| **Physical / On-Premises** | Servers (bare metal), rack/blade chassis, storage arrays (SAN/NAS), network switches, firewalls, load balancers, UPS systems |
| **Virtualization Platforms** | VMware vSphere/vSAN, Microsoft Hyper-V, KVM hypervisors |
| **Cloud Infrastructure** | AWS, Microsoft Azure, Google Cloud Platform (IaaS/PaaS provisioned resources — VMs, VNets, storage accounts, managed databases) |
| **Hybrid Connectivity** | ExpressRoute, Direct Connect, SD-WAN, VPN gateways |
| **Operating Systems** | Windows Server, Red Hat Enterprise Linux (RHEL), Ubuntu Server LTS |
| **Infrastructure Services** | Active Directory / LDAP, DNS, DHCP, NTP, backup and recovery systems, monitoring platforms |

### 2.2 Out of Scope

- Application-level validation (covered by separate Application Validation SOP).
- End-user device qualification (covered by End-User Computing SOP).
- Decommissioning procedures (covered by Infrastructure Decommissioning SOP).

### 2.3 Geographic Applicability

This SOP applies to all global sites, regional data centers, and cloud tenants operated or managed by the organization's IT Infrastructure team, regardless of geographic location or regulatory jurisdiction.

---

## 3. Roles and Responsibilities

| Role | Responsibility |
|---|---|
| **IT Infrastructure Engineer** | Executes qualification activities; performs IQ, OQ, and PQ testing; documents evidence; raises deviations |
| **System Administrator** | Supports configuration baseline establishment; executes operational qualification scripts; manages OS-level configurations |
| **IT Qualification Lead / Validation Engineer** | Authors and reviews qualification protocols; approves test results; manages the qualification lifecycle |
| **IT Risk Manager** | Performs infrastructure risk assessments; assigns GxP criticality classification; reviews risk mitigation controls |
| **IT Change Manager** | Ensures qualification activities are linked to approved Change Records; manages change windows |
| **Quality Assurance (QA) Representative** | Reviews and approves qualification documentation; ensures compliance with regulatory requirements; performs periodic audits |
| **Site IT Manager / Global IT Director** | Final approval authority for qualification reports; accountable for qualified infrastructure estate |
| **Cloud Services Administrator** | Manages cloud tenancy configuration; ensures cloud-shared responsibility model compliance; provides CSP documentation |

> **⚠️ Segregation of Duties Note:** The individual who executes qualification testing **must not** be the sole approver of the resulting qualification report without QA co-signature.   

---

## 4. Prerequisites and Required Resources

### 4.1 Documentation Prerequisites

Before initiating any qualification activity, the following documents must be available and approved:

- [ ] **Infrastructure Risk Assessment** — Criticality classification completed (GxP Critical / Business Critical / Standard)
- [ ] **User Requirements Specification (URS)** — Defines infrastructure performance, availability, and security requirements
- [ ] **System/Infrastructure Description Document** — Describes architecture, components, and integration points
- [ ] **Approved Change Request** — All qualification activities must be linked to an approved change ticket
- [ ] **Vendor/CSP Documentation** — Certificates of conformance, hardware specs, CSP audit reports (e.g., SOC 2 Type II, ISO 27001)

### 4.2 Tools and Access Requirements

| Resource | Details |
|---|---|
| **Qualification Management System** | e.g., Veeva Vault QualityDocs, OpenText Documentum, or equivalent |
| **Configuration Management Database (CMDB)** | ServiceNow or equivalent — for asset registration |
| **Monitoring and Alerting Platform** | Datadog, Nagios, Azure Monitor, or equivalent |
| **Vulnerability Scanner** | Qualys, Tenable Nessus, or equivalent |
| **Privileged Access** | Elevated credentials approved via PAM tool (e.g., CyberArk) for qualification window only |
| **Network Diagram / Architecture Tools** | Visio, Lucidchart, or equivalent |

### 4.3 Environmental Requirements

- A dedicated **Qualification Environment** (separate from Production) should be used where possible.
- Where qualification must occur in Production (e.g., existing live infrastructure), a formal **Risk Acceptance Form** must be completed and QA-approved.
- All testing must occur within an **approved Change Window**.

---

## 5. Infrastructure Qualification Procedure

The qualification process follows the **V-Model validation lifecycle** adapted for infrastructure, consisting of four phases:

```
[ URS / Risk Assessment ]
          |
[ Design Qualification (DQ) ]
          |
[ Installation Qualification (IQ) ]
          |
[ Operational Qualification (OQ) ]
          |
[ Performance Qualification (PQ) ]
          |
[ Qualification Report & Release ]
```

---

### Phase 1 — Design Qualification (DQ)

**Objective:** Verify that the infrastructure design meets documented requirements before procurement or deployment.

| Step | Action | Responsible |
|---|---|---|
| **DQ-01** | Review and confirm the URS is complete and approved by stakeholders | IT Qualification Lead |
| **DQ-02** | Conduct a **traceability review** — map each URS requirement to a design specification element | IT Qualification Lead + IT Infrastructure Engineer |
| **DQ-03** | Assess vendor documentation: hardware datasheets, firmware release notes, CSP service descriptions | IT Infrastructure Engineer |
| **DQ-04** | Perform a **GxP Criticality Assessment** — determine if infrastructure directly or indirectly supports regulated data or processes | IT Risk Manager + QA |
| **DQ-05** | Complete **DQ Protocol** and obtain required signatures (IT Lead, QA) | IT Qualification Lead |
| **DQ-06** | Document any design gaps as **open items** and assign remediation owners with target dates | IT Qualification Lead |

> **✅ DQ Exit Criteria:** Signed DQ report with all open items resolved or formally risk-accepted.

---

### Phase 2 — Installation Qualification (IQ)

**Objective:** Verify that the infrastructure component has been installed correctly, according to manufacturer/vendor specifications and the approved design.

#### 2.1 Physical / On-Premises IQ Steps

| Step | Action | Evidence Required |
|---|---|---|
| **IQ-01** | Verify hardware asset tag, serial number, and model match purchase order and CMDB record | CMDB screenshot, delivery note |
| **IQ-02** | Confirm physical rack location, power connections (dual PSU), and cable labeling comply with data center standards | Rack diagram, photo evidence |
| **IQ-03** | Verify firmware/BIOS version against approved baseline configuration | Firmware version screenshot |
| **IQ-04** | Confirm OS installation version, patch level, and build date match approved golden image | OS version output (`uname -a` / `winver`) |
| **IQ-05** | Validate storage configuration: RAID level, LUN sizing, multipath configuration | Storage configuration report |
| **IQ-06** | Verify network interface configuration: IP addressing, VLAN assignment, bonding/teaming | Network configuration output |
| **IQ-07** | Confirm security baseline applied: host-based firewall, CIS Benchmark hardening, endpoint agent installed | Hardening checklist, vulnerability scan |
| **IQ-08** | Register asset in CMDB with full configuration details | CMDB record screenshot |

#### 2.2 Cloud Infrastructure IQ Steps

| Step | Action | Evidence Required |
|---|---|---|
| **IQ-C01** | Verify cloud resource provisioned via approved Infrastructure-as-Code (IaC) template (Terraform/ARM/CloudFormation) | IaC code version, pipeline run log |
| **IQ-C02** | Confirm resource region, availability zone placement, and resource group/tagging standards | Cloud portal screenshot or CLI output |
| **IQ-C03** | Validate network security group (NSG) / security group rules against approved firewall matrix | NSG/SG export |
| **IQ-C04** | Confirm managed identity / IAM role assignments follow least-privilege principles | IAM policy review output |
| **IQ-C05** | Verify encryption at rest and in transit settings (CMK vs. platform-managed keys) | Key vault / KMS configuration |
| **IQ-C06** | Confirm diagnostic logs and audit logs are forwarded to the central SIEM / log management system | Log analytics workspace configuration |
| **IQ-C07** | Validate backup policy applied and retention period meets requirements | Backup policy screenshot |

> **✅ IQ Exit Criteria:** All IQ checklist items verified with documented evidence. Any failures recorded as deviations. Signed IQ report obtained.

---

### Phase 3 — Operational Qualification (OQ)

**Objective:** Verify that the infrastructure operates correctly and reliably across its intended operational range, including boundary and exception conditions.

#### 3.1 Core OQ Test Cases

| Test ID | Test Description | Pass Criteria |
|---|---|---|
| **OQ-001** | **Connectivity Test** — Verify all network interfaces are active and reachable | Ping/traceroute success; no packet loss |
| **OQ-002** | **Authentication & Authorization Test** — Validate domain join / directory service integration; test RBAC roles | Users authenticate successfully; unauthorized access denied |
| **OQ-003** | **Storage I/O Test** — Execute read/write performance benchmarks (fio/IOmeter) | I/O throughput meets URS-defined minimum thresholds |
| **OQ-004** | **High Availability / Failover Test** — Simulate primary component failure (NIC, PSU, node) | Failover completes within defined RTO; no data loss |
| **OQ-005** | **Backup and Restore Test** — Execute a test backup and full restore to alternate location | Restore completes successfully; data integrity verified via hash comparison | 
| **OQ-006** | **Monitoring & Alerting Test** — Trigger a threshold breach; confirm alert generated and received | Alert received by on-call team within defined SLA |
| **OQ-007** | **Time Synchronization Test** — Verify NTP synchronization accuracy | System time within ±1 second of authoritative NTP source |
| **OQ-008** | **Patch Management Test** — Apply a test patch through the approved patching workflow | Patch applied successfully; system stable post-patch; rollback tested |
| **OQ-009** | **Security Vulnerability Scan** — Execute authenticated vulnerability scan | No Critical or High findings unmitigated; all findings documented |
| **OQ-010** | **Disaster Recovery Connectivity Test** — Validate DR site replication link and failover routing | DR replication active; RTO/RPO metrics meet policy requirements |       
| **OQ-011** | **Audit Logging Verification** — Perform test administrative actions; confirm all events logged in SIEM | All privileged actions captured with timestamp, user ID, and action detail |
| **OQ-012** | **Capacity and Resource Utilization Baseline** — Record CPU, RAM, storage, and network utilization under representative load | Utilization within acceptable thresholds; baseline recorded in CMDB |

> **✅ OQ Exit Criteria:** All OQ test cases executed. Pass/Fail result documented. All failures addressed via deviation process. Signed OQ report obtained.

---

### Phase 4 — Performance Qualification (PQ)

**Objective:** Demonstrate, under realistic production-like conditions over a defined observation period, that the infrastructure consistently meets performance, availability, and reliability requirements.

| Step | Action | Details |
|---|---|---|
| **PQ-01** | **Define PQ Observation Period** | Minimum **10 business days** for GxP-critical infrastructure; 5 business days for non-GxP |
| **PQ-02** | **Establish Production Load Simulation** | Simulate representative workloads using load generation tools or parallel production traffic mirroring |
| **PQ-03** | **Continuous Monitoring Data Collection** | Collect CPU, memory, disk I/O, network throughput, and latency metrics continuously throughout the PQ period |
| **PQ-04** | **Availability Measurement** | Calculate uptime percentage; must meet or exceed SLA (e.g., ≥99.9% for GxP Critical systems) |
| **PQ-05** | **Incident and Error Log Review** | Review all system logs and monitoring alerts generated during PQ period; categorize and investigate anomalies |
| **PQ-06** | **Recurring Backup Verification** | Confirm automated backups execute successfully each day of the PQ period; spot-check restore integrity |
| **PQ-07** | **Security Events Review** | Review SIEM alerts for anomalous access patterns or security events; confirm no unresolved findings |
| **PQ-08** | **PQ Report Compilation** | Compile all metrics, evidence, and observations; compare against URS acceptance criteria |

> **✅ PQ Exit Criteria:** PQ report demonstrates consistent performance meeting all URS requirements over the full observation period. Signed PQ/Qualification Summary Report obtained from IT Lead and QA.

---

## 6. Acceptance Criteria and Testing Protocols

### 6.1 Standard Acceptance Criteria Summary

| Parameter | GxP Critical Infrastructure | Business Critical Infrastructure | Standard Infrastructure |
|---|---|---|---|
| **Availability (Uptime)** | ≥ 99.9% | ≥ 99.5% | ≥ 99.0% |
| **RTO (Recovery Time Objective)** | ≤ 4 hours | ≤ 8 hours | ≤ 24 hours |
| **RPO (Recovery Point Objective)** | ≤ 1 hour | ≤ 4 hours | ≤ 24 hours |
| **NTP Synchronization Accuracy** | ±1 second | ±5 seconds | ±60 seconds |
| **Critical Vulnerability Resolution** | 100% mitigated before production | 100% mitigated within 30 days | 100% mitigated within 60 days |
| **Audit Log Retention** | Minimum 3 years | Minimum 1 year | Minimum 90 days |
| **Backup Verification Frequency** | Daily automated + monthly restore test | Weekly automated + quarterly restore | Weekly automated |

### 6.2 Test Failure Classification

| Severity | Definition | Resolution Requirement |
|---|---|---|
| **Critical** | Test failure that directly impacts GxP data integrity, patient safety, or regulatory compliance | **Stop qualification.** Immediate escalation to QA and IT Management. No production release until resolved and re-tested. |
| **Major** | Test failure that could impact system reliability, security, or business continuity | Deviation raised; root cause documented; corrective action completed before production release |
| **Minor** | Test failure with no direct compliance or business impact; cosmetic or documentation issue | Deviation raised; corrective action may be completed post-release with QA approval and defined timeline |

---

## 7. Documentation and Change Control

### 7.1 Qualification Document Set

The following documents must be produced and retained for every qualification activity:

| Document | Description | Retention Period |
|---|---|---|
| Infrastructure Risk Assessment | GxP criticality classification and risk controls | System lifetime + 3 years |
| User Requirements Specification (URS) | Functional and non-functional requirements | System lifetime + 3 years |
| Design Qualification (DQ) Protocol & Report | Design review evidence and traceability matrix | System lifetime + 3 years |
| Installation Qualification (IQ) Protocol & Report | Installation verification evidence | System lifetime + 3 years |
| Operational Qualification (OQ) Protocol & Report | Operational test cases and results | System lifetime + 3 years |
| Performance Qualification (PQ) Protocol & Report | Performance evidence over observation period | System lifetime + 3 years |
| Qualification Summary Report | Overall qualification conclusion and release approval | System lifetime + 3 years |
| Deviation Reports | Record of all test failures and corrective actions | System lifetime + 3 years |
| Configuration Baseline Record | Approved configuration snapshot stored in CMDB | System lifetime |

### 7.2 Re-qualification Triggers

Any of the following changes **must trigger a re-qualification assessment**. The IT Qualification Lead and QA will determine the scope (full re-qualification vs. impact-assessed partial re-qualification):

- ✳️ Hardware replacement (like-for-like vs. specification change)
- ✳️ Major OS upgrade or migration to a new OS version
- ✳️ Hypervisor platform upgrade (e.g., VMware major version)
- ✳️ Cloud region migration or tenancy restructure
- ✳️ Network architecture changes (routing, segmentation, firewall policy)
- ✳️ Change to backup/recovery platform or policy
- ✳️ Change in data classification (e.g., non-GxP system promoted to GxP scope)
- ✳️ Security incident that compromises infrastructure integrity
- ✳️ Regulatory finding or internal audit observation

### 7.3 Change Control Integration

All qualification activities must be executed under an **approved Change Request** in the ITSM platform. The change record must reference:
- The qualification protocol document ID
- Planned change window
- Rollback plan
- Post-implementation review date

---

## 8. Compliance, Deviation Management, and References

### 8.1 Regulatory and Standards Compliance

This SOP is designed to support compliance with the following regulations and standards:

| Regulation / Standard | Applicability |
|---|---|
| **21 CFR Part 11** (FDA) | Electronic records and electronic signatures for GxP systems |
| **EU Annex 11** | Computerized systems used in GMP-regulated environments |
| **GAMP 5** (ISPE) | Risk-based approach to computerized system validation — Category 1 infrastructure |
| **ICH Q9** | Quality risk management principles applied to infrastructure risk assessment |
| **ICH Q10** | Pharmaceutical quality system — infrastructure as an enabler |
| **ISO/IEC 27001** | Information security management for infrastructure and data protection |
| **NIST SP 800-53** | Security and privacy controls for federal/regulated information systems |
| **SOC 2 Type II** | Cloud provider audit reports to satisfy infrastructure vendor qualification |
| **GDPR / Data Privacy Regulations** | Infrastructure hosting personal data of EU subjects |

### 8.2 Deviation Management Process

```
Deviation Identified During Testing
            │
            ▼
   Record in Deviation Log (immediate)
            │
            ▼
   Classify Severity (Critical / Major / Minor)
            │
     ┌──────┴──────┐
     ▼             ▼
  Critical      Major/Minor
  Escalate      Raise formal
  to QA +       Deviation Report
  Stop Test
            │
            ▼
   Root Cause Analysis (RCA) — use 5-Why or Fishbone
            │
            ▼
   Corrective and Preventive Action (CAPA) defined
            │
            ▼
   Re-test affected area
            │
            ▼
   QA review and closure of deviation
            │
            ▼
   Reference in Qualification Report
```

### 8.3 Periodic Review

- This SOP must be reviewed **at minimum annually** or upon a significant change to the regulatory landscape, infrastructure strategy, or following a major audit finding.
- The periodic review must be documented with a review record and any revisions managed through the document change control process.

### 8.4 Related Documents and References

| Document | Reference |
|---|---|
| Application Validation SOP | [Internal Reference] |
| Infrastructure Decommissioning SOP | [Internal Reference] |
| IT Change Management SOP | [Internal Reference] |
| IT Risk Assessment Procedure | [Internal Reference] |
| CMDB Management Procedure | [Internal Reference] |
| Data Integrity Policy | [Internal Reference] |
| Business Continuity and DR Plan | [Internal Reference] |
| ISPE GAMP 5 Guide | ISBN: 978-1-931879-61-5 |
| FDA 21 CFR Part 11 | https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11 |
| EU Annex 11 | EudraLex Volume 4, Annex 11 |

---

## 📝 Document Control

| Field | Details |
|---|---|
| **Document Title** | Global Technology Infrastructure Qualification SOP |
| **Document ID** | sop-6828956471617685896 |
| **Version** | 1.0 |
| **Status** | Draft — Pending QA Review |
| **Industry** | Life Science |
| **Target Audience** | IT Infrastructure Engineers, System Administrators |
| **Author** | IT Qualification / SOP Generation Pipeline |
| **Review Frequency** | Annual |
| **Next Review Due** | 12 months from effective date |

> **⚠️ Disclaimer:** This SOP is a template generated to provide a comprehensive starting framework. All sections must be reviewed, customized to your organization's specific systems andd regulatory obligations, and formally approved by Quality Assurance and relevant stakeholders before use in a regulated environment.
Tool #1: run_research
2026-03-11 11:30:22 - src.agents.research_agent - INFO - >>> run_research | prompt: Original Task: workflow_id::sop-6828956471617685896 | Generate a Standard Operating Procedure for: Global Technology Infrastructure Qualification SOP | Industry
2026-03-11 11:30:22 - src.agents.research_agent - INFO - Research | topic='Global Technology Infrastructure Qualification SOP' industry='Life Science' audience='IT Infrastructure Engineers and System Administrators responsible for managing on-premises and cloud infrastructure'
2026-03-11 11:30:23 - src.agents.research_agent - INFO - KB Round 1: 46 hits across 7 queries
2026-03-11 11:30:23 - src.agents.research_agent - INFO - KB retrieval done — hits=46 | queries_tried=7
2026-03-11 11:35:29 - src.agents.research_agent - ERROR - Research FAILED for workflow_id=sop-6828956471617685896
Traceback (most recent call last):
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connectionpool.py", line 534, in _make_request
    response = conn.getresponse()
               ^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connection.py", line 571, in getresponse
    httplib_response = super().getresponse()
                       ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\http\client.py", line 1374, in getresponse
    response.begin()
  File "C:\Python311\Lib\http\client.py", line 318, in begin
    version, status, reason = self._read_status()
                              ^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\http\client.py", line 279, in _read_status
    line = str(self.fp.readline(_MAXLINE + 1), "iso-8859-1")
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\socket.py", line 705, in readinto
    return self._sock.recv_into(b)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\ssl.py", line 1278, in recv_into
    return self.read(nbytes, buffer)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\ssl.py", line 1134, in read
    return self._sslobj.read(len, buffer)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TimeoutError: The read operation timed out

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\httpsession.py", line 477, in send
    urllib_response = conn.urlopen(
                      ^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connectionpool.py", line 841, in urlopen
    retries = retries.increment(
              ^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\util\retry.py", line 449, in increment
    raise reraise(type(error), error, _stacktrace)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\util\util.py", line 39, in reraise
    raise value
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connectionpool.py", line 787, in urlopen
    response = self._make_request(
               ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connectionpool.py", line 536, in _make_request
    self._raise_timeout(err=e, url=url, timeout_value=read_timeout)
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\urllib3\connectionpool.py", line 367, in _raise_timeout
    raise ReadTimeoutError(
urllib3.exceptions.ReadTimeoutError: AWSHTTPSConnectionPool(host='bedrock-runtime.us-east-2.amazonaws.com', port=443): Read timed out. (read timeout=60)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\Users\cr242786\sop-strands-agent - poc\app\src\agents\research_agent.py", line 1034, in run_research
    findings = await _synthesize_findings(state, kb_docs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent - poc\app\src\agents\research_agent.py", line 798, in _synthesize_findings
    data = await asyncio.to_thread(_invoke)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\asyncio\threads.py", line 25, in to_thread
    return await loop.run_in_executor(None, func_call)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python311\Lib\concurrent\futures\thread.py", line 58, in run
    result = self.fn(*self.args, **self.kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\opentelemetry\instrumentation\threading\__init__.py", line 171, in wrapped_func
    return original_func(*func_args, **func_kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent - poc\app\src\agents\research_agent.py", line 788, in _invoke
    return _invoke_model_json(
           ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent - poc\app\src\agents\research_agent.py", line 337, in _invoke_model_json
    resp = client.invoke_model(
           ^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\client.py", line 602, in _api_call
    return self._make_api_call(operation_name, kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\context.py", line 123, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\client.py", line 1060, in _make_api_call
    http, parsed_response = self._make_request(
                            ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\client.py", line 1084, in _make_request
    return self._endpoint.make_request(operation_model, request_dict)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\endpoint.py", line 119, in make_request
    return self._send_request(request_dict, operation_model)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\endpoint.py", line 200, in _send_request
    while self._needs_retry(
          ^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\endpoint.py", line 360, in _needs_retry
    responses = self._event_emitter.emit(
                ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\hooks.py", line 412, in emit
    return self._emitter.emit(aliased_event_name, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\hooks.py", line 256, in emit
    return self._emit(event_name, kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\hooks.py", line 239, in _emit
    response = handler(**kwargs)
               ^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 207, in __call__
    if self._checker(**checker_kwargs):
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 284, in __call__
    should_retry = self._should_retry(
                   ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 320, in _should_retry
    return self._checker(attempt_number, response, caught_exception)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 363, in __call__
    checker_response = checker(
                       ^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 247, in __call__
    return self._check_caught_exception(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\retryhandler.py", line 416, in _check_caught_exception
    raise caught_exception
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\endpoint.py", line 279, in _do_get_response
    http_response = self._send(request)
                    ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\endpoint.py", line 383, in _send
    return self.http_session.send(request)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\cr242786\sop-strands-agent\.venv\Lib\site-packages\botocore\httpsession.py", line 514, in send
    raise ReadTimeoutError(endpoint_url=request.url, error=e)
botocore.exceptions.ReadTimeoutError: Read timeout on endpoint URL: "https://bedrock-runtime.us-east-2.amazonaws.com/model/arn%3Aaws%3Abedrock%3Aus-east-2%3A070797854596%3Ainference-profile%2Fglobal.anthropic.claude-sonnet-4-6/invoke"
I encountered a timeout error when attempting to run the research step for workflow `sop-6828956471617685896`. This is a transient infrastructure connectivity issue with the AI backend (AWS Bedrock endpoint timeout), not an error in the SOP content itself.

**What this means:**
- The research tool attempted to connect to the Claude inference endpoint but the request timed out before a response was received.
- The planning output (the full SOP draft above) was successfully generated and is complete and well-structured.

**Recommended next steps:**
1. **Retry the research node** — Re-submit the same prompt to trigger a fresh attempt. Timeout errors are typically transient and resolve on retry.
2. **Check endpoint health** — If retries continue to fail, verify that the AWS Bedrock `us-east-2` inference profile (`global.anthropic.claude-sonnet-4-6`) is operational and that the IAM/network configuration allows outbound calls.
3. **Proceed with the planning output** — The SOP draft produced by the planning node is comprehensive and covers all required sections (DQ/IQ/OQ/PQ, GAMP 5, 21 CFR Part 11, EU Annex 11, acceptance criteria, deviation management, etc.). If the research enrichment step is non-blocking for your workflow, the existing draft can move forward to the writing/formatting node. 

Would you like me to retry the research call now?
Tool #1: run_content
2026-03-11 11:35:44 - src.agents.content_agent - INFO - >>> run_content | prompt: Original Task: workflow_id::sop-6828956471617685896 | Generate a Standard Operating Procedure for: Global Technology Infrastructure Qualification SOP | Industry
2026-03-11 11:35:44 - src.agents.content_agent - ERROR - Content generation FAILED: No research findings in state. Ensure research agent completed successfully.
Traceback (most recent call last):
  File "C:\Users\cr242786\sop-strands-agent - poc\app\src\agents\content_agent.py", line 434, in run_content
    raise ValueError(
ValueError: No research findings in state. Ensure research agent completed successfully.
The content generation node returned a failure because the upstream research step did not complete successfully (due to the prior timeout). The pipeline requires valid research findings in the workflow state before content can be generated.

## What Happened
The `run_content` tool checks `SOPState` for research findings populated by the research node. Since that node timed out and stored no data, the content node has nothing to build from and correctly rejects the request.

---

## How to Resolve

You have **two clear paths forward**:

### ✅ Option 1 — Retry the Full Pipeline (Recommended)
Re-trigger the workflow from the **research node** for `workflow_id::sop-6828956471617685896`. Once research completes successfully and populates `SOPState`, the content node will have the inputs it needs and can proceed automatically.

> 🔁 Simply re-submit the original task to restart the pipeline from research → planning → content.

---

### ✅ Option 2 — Manual Research Bypass (If Retries Keep Failing)
If the Bedrock endpoint continues to time out, a human operator or pipeline admin can **inject placeholder research findings** directly into `SOPState` for `sop-6828956471617685896`. The planning node already produced a comprehensive draft covering:
- **DQ / IQ / OQ / PQ** qualification phases
- **GAMP 5** risk-based approach
- **21 CFR Part 11** and **EU Annex 11** compliance
- Acceptance criteria and deviation management

Those outputs can serve as the research payload to unblock content generation.

---

### 🔧 Option 3 — Endpoint Health Check
If this is a recurring issue, verify:
| Check | Action |
|---|---|
| AWS Bedrock `us-east-2` status | Check AWS Service Health Dashboard |
| IAM permissions | Confirm `bedrock:InvokeModel` is granted for the inference profile |
| Network/VPC | Ensure outbound HTTPS (443) to Bedrock endpoints is not blocked |
| Inference profile ID | Validate `global.anthropic.claude-sonnet-4-6` is active and not deprecated |

---

**Would you like me to retry the pipeline now, or would you prefer to manually inject research state to bypass the research node?**
Tool #1: run_formatting
2026-03-11 11:36:04 - src.agents.formatter_agent - INFO - >>> run_formatting | prompt: Original Task: workflow_id::sop-6828956471617685896 | Generate a Standard Operating Procedure for: Global Technology Inf
2026-03-11 11:36:04 - src.agents.formatter_agent - ERROR - Formatting FAILED: No content sections available for formatting.
Traceback (most recent call last):
  File "C:\Users\cr242786\sop-strands-agent - poc\app\src\agents\formatter_agent.py", line 372, in run_formatting
    raise ValueError("No content sections available for formatting.")
ValueError: No content sections available for formatting.
## ⚠️ Formatting Pipeline — Stage Failed

**Workflow ID:** `sop-6828956471617685896`
**Stage:** Formatting Node
**Status:** ❌ FAILED — `No content sections available for formatting`

---

### Why This Happened

The formatting node requires fully generated SOP content sections (produced by the content node) as its input. Because the pipeline stalled at the **research node** due to a timeout, neither the content node nor the formatting node have any material to work with. This failure is an expected cascade from the upstream research failure — the formatting node is correctly rejecting an empty payload.

---

### Current Pipeline State Summary

| Stage | Status | Reason |
|---|---|---|
| 🔬 Research Node | ❌ Failed (Timeout) | Bedrock endpoint timed out; no findings stored in `SOPState` |
| 📋 Planning Node | ✅ Completed | Draft structure covering DQ/IQ/OQ/PQ, GAMP 5, 21 CFR Part 11, EU Annex 11 |
| ✍️ Content Node | ❌ Failed | No research findings available in `SOPState` |
| 🖨️ Formatting Node | ❌ Failed | No content sections available to format |

---

### How to Resolve

The root cause is the **research node timeout**. Fixing that unblocks all downstream stages automatically. You have three options:

**✅ Option 1 — Retry the Full Pipeline (Recommended)**
Re-submit the original task to restart from the research stage. Once research populates `SOPState`, the content and formatting nodes will execute in sequence without further intervention.

**✅ Option 2 — Manual Research Bypass**
Inject placeholder research findings directly into `SOPState` for `sop-6828956471617685896`, using the planning node's existing output (DQ/IQ/OQ/PQ phases, GAMP 5 risk approach, regulatory compliance mappings) as the research payload. This unblocks content → formatting immediately.

**🔧 Option 3 — Endpoint Health Check Before Retrying**
If timeouts are recurring, validate the following before re-triggering:
- **AWS Bedrock `us-east-2` health** via the AWS Service Health Dashboard
- **IAM permissions** — confirm `bedrock:InvokeModel` is granted for the inference profile
- **Network/VPC** — ensure outbound HTTPS (port 443) to Bedrock endpoints is not blocked
- **Inference profile** — verify `global.anthropic.claude-sonnet-4-6` is active and not deprecated

---

> 🔁 **Recommended next step:** Retry the full pipeline for `workflow_id::sop-6828956471617685896`. All pipeline stages are intact and will execute correctly once the research node completes successfully.
Tool #1: run_qa
2026-03-11 11:36:22 - src.agents.qa_agent - ERROR - QA review failed: No formatted document available for QA review
**QA Node Result — `workflow_id::sop-6828956471617685896`**

**Status: ❌ QA FAILED — `No formatted document available for QA review`**

---

### QA Assessment

The QA node has correctly rejected this workflow run. There is **no formatted SOP document** available for review, which is a direct cascade failure from the upstream pipeline breakdown. QA cannot assess, score, or approve content that does not exist.

---

### Full Pipeline Failure Chain Summary

| Stage | Status | Root Cause |
|---|---|---|
| 📋 Planning Node | ✅ Completed | Successful — DQ/IQ/OQ/PQ structure, GAMP 5, 21 CFR Part 11, EU Annex 11 mapped |
| 🔬 Research Node | ❌ Failed | Bedrock endpoint timeout — no findings written to `SOPState` |
| ✍️ Content Node | ❌ Failed | No research findings available in `SOPState` |
| 🖨️ Formatting Node | ❌ Failed | No content sections available to format |
| ✅ QA Node | ❌ Failed | No formatted document available for QA review |

---

### Required Action

The **single root cause** is the Research Node timeout. All five downstream failures resolve automatically once the research node completes successfully.

**➡️ Recommended Next Step: Retry the full pipeline for `workflow_id::sop-6828956471617685896`.**

Before retrying, optionally validate:
1. **AWS Bedrock health** in `us-east-2` via the AWS Service Health Dashboard
2. **IAM permissions** — confirm `bedrock:InvokeModel` is authorized for the inference profile
3. **Network/VPC** — confirm outbound HTTPS (port 443) to Bedrock endpoints is open
4. **Inference profile** — verify `global.anthropic.claude-sonnet-4-6` is active and not deprecated2026-03-11 11:36:30 - src.graph.sop_workflow - INFO - SOP Generation COMPLETE | status=failed | tokens=1500 | kb_hits=46
2026-03-11 11:36:30 - src.graph.sop_workflow - INFO - QA Result | score=5.0 | approved=False
⚠️  WARNING: No formatted document in result. Check logs for errors.
   Status: failed
   Errors: ['[2026-03-11T15:35:44.379162] Content generation failed: No research findings in state. Ensure research agent completed successfully.', '[2026-03-11T15:36:04.038231] Formatting failed: No content sections available for formatting.', '[2026-03-11T15:36:22.375891] QA review failed: No formatted document available for QA review']

(.venv) C:\Users\cr242786\sop-strands-agent - poc>
