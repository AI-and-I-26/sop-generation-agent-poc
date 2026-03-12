---

| Field | Value |
|---|---|
| **Title** | Global Technology Infrastructure Qualification SOP |
| **Document ID** | SOP-20260311-2000 |
| **Version** | 1.0 |
| **Status** | {{status}} |
| **Effective Date** | 11-Mar-2026 |
| **Classification** | {{classification}} |
| **Industry** | Life Science |
| **Target Audience** | IT Infrastructure Engineers and System Administrators responsible for managing on-premises and cloud infrastructure |

> **{{status}} — {{classification}}**
> This document is subject to controlled document management.
> Approval signatures (wet or electronic per 21 CFR Part 11) are required
> before this SOP is placed into operational use.
> Always verify you are reading the current approved version before use.

---

1.0 PURPOSE

This Standard Operating Procedure (SOP) establishes the requirements, methodology, and controls governing the qualification of global technology infrastructure within the Life Science operating environment. This SOP is subject to controlled document management and must be maintained, versioned, and approved in accordance with applicable regulatory requirements, including 21 CFR Part 11 for electronic records and signatures, EU GMP Annex 11 for computerised systems, and GAMP 5 (Second Edition, 2022) for the validation of automated systems. Approval signatures, whether wet or electronic via DocuSign or Kneat, are required prior to document release, and every page of this SOP and its associated qualification deliverables must carry a header and footer displaying the document title, document number, revision number, effective date, and Page x of y pagination.

This SOP defines a structured qualification lifecycle comprising three distinct phases — Planning and Design, Testing, and Operational — to ensure that on-premises and cloud infrastructure components supporting GxP systems are fit for intended use, consistently deployed, and maintained in a qualified state. The procedure mandates that an Infrastructure Qualification Plan (IQP) and an As Built Document are reviewed and approved by authorised personnel, including GCVQA review and approval by dated signature, before any testing activity commences. Baseline Configuration documents must likewise be established prior to the start of testing to provide a verified reference state against which qualification evidence is assessed.

This SOP ensures that all qualification documentation is controlled and versioned, that test scripts are numbered sequentially and include the testing type designation, and that post-execution review is performed by a qualified, non-tester Subject Matter Expert (SME). Requalification scope must be assessed whenever a change is made to a qualified infrastructure component, and Annual Reviews must be conducted to evaluate the ongoing qualified state of infrastructure in accordance with the organisation's quality management obligations. Vendor-supplied technology must be approved prior to use in accordance with the Global Vendor Program, and all changes to qualified infrastructure must be managed through the formal change control process defined in GIT-SOP-00001 Change Management Process and GLBL-SOP-00045 Configuration Management SOP.

2.0 SCOPE

This SOP applies to all IT Infrastructure Engineers and System Administrators responsible for planning, executing, and maintaining qualification activities for on-premises and cloud infrastructure components that support GxP and non-GxP systems within the global technology environment. This SOP is subject to controlled document management; all versions must be approved by authorized personnel via wet or electronic signature in accordance with 21 CFR Part 11, and every page must carry a header and footer displaying the document title, document number, revision number, effective date, and Page x of y pagination.

  2.1 In Scope

  The following infrastructure components, activities, and lifecycle phases are within the scope of this SOP:

    2.1.1 Physical and virtual server infrastructure hosted on-premises or in cloud environments (including IaaS, PaaS, and SaaS platforms) that directly or indirectly support regulated GxP operations.

    2.1.2 Network infrastructure components, including switches, routers, firewalls, and load balancers, where such components form part of a qualified or GxP-supporting environment.

    2.1.3 Storage systems, backup infrastructure, and disaster recovery components associated with qualified systems.

    2.1.4 All three qualification lifecycle phases as defined in the Infrastructure Qualification Plan (IQP): Planning and Design, Testing, and Operational phases.

    2.1.5 Qualification documentation, including the IQP, As Built Document, Baseline Configuration documents, test scripts, and the Infrastructure Qualification Report (IQR), all of which must be controlled, versioned, and approved prior to the commencement of testing, in accordance with the documentation lifecycle requirements defined herein.

    2.1.6 Requalification assessments triggered by any change to a qualified infrastructure component, managed in accordance with GIT-SOP-00001 Change Management Process.

    2.1.7 Annual Reviews conducted to evaluate the ongoing qualified state of infrastructure components, including annual account access reviews performed as part of the Operational phase.

    2.1.8 Vendor-supplied technology used within qualified environments, which must be approved prior to use in accordance with the Global Vendor Program.

    2.1.9 Electronic signature and data integrity controls applied to test script execution via Kneat or DocuSign, in compliance with 21 CFR Part 11 and applicable Data Integrity requirements.

    2.1.10 GCVQA review and approval activities required for GxP systems, including dated signature approval of both the IQP and IQR.

  2.2 Out of Scope

  The following activities and systems are outside the scope of this SOP:

    2.2.1 Application-level validation activities, including Installation Qualification (IQ), Operational Qualification (OQ), and Performance Qualification (PQ) of software applications, which are governed by separate Computer System Validation (CSV) procedures.

    2.2.2 Infrastructure components that have no direct or indirect connection to GxP systems and are not subject to qualification requirements under applicable regulatory frameworks.

    2.2.3 Configuration management activities beyond the scope of qualification, which are governed exclusively by GLBL-SOP-00045 Configuration Management SOP.

3.0 RESPONSIBILITIES

The following roles and responsibilities apply to all personnel involved in the planning, execution, review, and approval of infrastructure qualification activities governed by this SOP. All personnel assigned to qualification activities must complete role-specific training before executing any qualification task, and training records must be maintained in accordance with applicable GxP requirements. Responsibilities are assigned as follows:

| ROLE | RESPONSIBILITY |
|---|---|
| IT Infrastructure Engineer | Executes qualification test scripts in accordance with the approved Infrastructure Qualification Plan (IQP); documents test results accurately and completely; raises deviations when actual results do not match expected results; ensures all executed test scripts are submitted for post-execution review. |
| IT Infrastructure Engineer | Prepares the As Built Document prior to the commencement of any testing, ensuring it accurately reflects the installed and configured state of the infrastructure under qualification. |
| System Administrator | Maintains and enforces Baseline Configuration documents prior to and throughout the testing phase; supports configuration management activities in accordance with GLBL-SOP-00045 Configuration Management SOP. |
| System Administrator | Conducts annual account access reviews as part of the Operational Phase to verify that user access rights remain appropriate and are consistent with the qualified state of the system. |
| Subject Matter Expert (SME) | Performs post-execution review of test scripts as a non-tester; must be qualified and trained on the relevant process and system prior to conducting any review activity; confirms that test execution is complete, accurate, and consistent with the approved IQP. |
| IT Qualification Lead | Authors and maintains the Infrastructure Qualification Plan (IQP) and Infrastructure Qualification Report (IQR); ensures all qualification documentation is controlled, versioned, and includes the required header and footer on every page per document control requirements consistent with 21 CFR Part 11. |
| IT Qualification Lead | Ensures the IQP and As Built Document receive required approvals before any testing commences; coordinates the qualification lifecycle across Planning, Testing, and Operational phases as defined in the IQP. |
| IT Qualification Lead | Assesses the need for requalification whenever a change is made to a qualified infrastructure component, in alignment with the change control process defined under GIT-SOP-00001 Change Management Process. |
| IT Qualification Lead | Coordinates and documents Annual Reviews to evaluate the ongoing qualified state of infrastructure components and ensures findings are recorded and addressed appropriately. |
| Quality Assurance (QA) / GCVQA Representative | Reviews and approves the IQP and IQR by dated signature for all GxP systems, ensuring compliance with applicable regulatory requirements including 21 CFR Part 11 and EU GMP Annex 11; reviews and approves all deviation reports prior to proceeding with further qualification activities. |
| Quality Assurance (QA) / GCVQA Representative | Provides QA oversight of the qualification lifecycle, including review of deviation classifications (critical, major, or minor), root cause analyses, and impact assessments to ensure the integrity of the qualification record. |
| Vendor Management / Procurement Representative | Ensures all vendor-supplied technology is approved prior to use in accordance with the Global Vendor Program before it is introduced into any qualification activity. |
| Change Control Board (CCB) / Change Manager | Reviews and approves Requests for Change (RFCs) affecting qualified infrastructure in accordance with GIT-SOP-00001 Change Management Process; ensures requalification scope is assessed and documented for every approved change. |
| Document Control | Maintains all qualification documentation under controlled document management; ensures documents are approved with wet or electronic signatures in accordance with 21 CFR Part 11 and that all pages carry the required header and footer including document title, qualification project number, document version, and Page x of y pagination. |

4.0 DEFINITIONS

The following terms and definitions apply throughout this Standard Operating Procedure and all associated qualification documentation. These definitions are provided to ensure consistent interpretation and application by IT Infrastructure Engineers, System Administrators, and all personnel involved in infrastructure qualification activities governed by this SOP.

As Built Document: A controlled document that records the actual configuration of an infrastructure component as it exists at the time of qualification, including hardware specifications, software versions, network topology, and configuration parameters. The As Built Document must be approved prior to the commencement of any testing activity.

Annual Review: A periodic evaluation, conducted no less than once per calendar year during the Operational Phase, to assess and confirm the ongoing qualified state of infrastructure components. The Annual Review must include an assessment of changes, incidents, and access controls that may affect the qualified state.

Baseline Configuration: A documented and approved record of the verified configuration state of an infrastructure component established prior to the commencement of qualification testing. The Baseline Configuration serves as the authoritative reference point for all subsequent change assessments and requalification activities, consistent with GLBL-SOP-00045 Configuration Management SOP.

Change Control: The formal process by which all proposed modifications to qualified infrastructure components are evaluated, approved, implemented, and documented. All Requests for Change (RFCs) must follow GIT-SOP-00001 Change Management Process. Requalification scope must be assessed for every approved change that affects a qualified infrastructure component.

Data Integrity: The assurance that data is complete, consistent, accurate, and maintained throughout its lifecycle in accordance with ALCOA+ principles. For electronic records and signatures, Data Integrity requirements are governed by 21 CFR Part 11 and EU GMP Annex 11.

Deviation: Any departure from an approved procedure, specification, or expected result identified during qualification activities. Deviations are classified as Critical, Major, or Minor based on their potential impact on system fitness for purpose and data integrity. All deviations must be documented, assessed for impact, and reviewed and approved by Quality Assurance prior to proceeding.

DocuSign: An electronic signature platform used for the execution and approval of test scripts and qualification documentation where Kneat is not employed. DocuSign usage must comply with Data Integrity requirements, including single-user account setup per day and single tester control per test script, in accordance with 21 CFR Part 11.

GAMP 5: Good Automated Manufacturing Practice, Second Edition (2022), published by ISPE. GAMP 5 provides a risk-based framework for the lifecycle management of computerised systems used in regulated environments and is a foundational reference for infrastructure qualification activities under this SOP.

GCVQA: Global Computer Validation and Quality Assurance. The GCVQA function is responsible for the review and approval of the Infrastructure Qualification Plan and Infrastructure Qualification Report for GxP systems, evidenced by dated signature.

GxP: A collective term referring to Good Practice quality guidelines and regulations applicable to life science industries, including Good Manufacturing Practice (GMP), Good Laboratory Practice (GLP), and Good Clinical Practice (GCP). Infrastructure supporting GxP systems is subject to the full qualification lifecycle defined in this SOP.

Infrastructure Qualification Plan (IQP): A controlled document that defines the scope, strategy, roles, responsibilities, test approach, and acceptance criteria for a qualification project. The IQP must be approved by authorised personnel, including GCVQA for GxP systems, prior to the commencement of any testing.

Infrastructure Qualification Report (IQR): A controlled document that summarises the results of all qualification testing activities, documents deviations and their resolutions, and provides a conclusion regarding the qualified state of the infrastructure component. The IQR must be reviewed and approved by GCVQA for GxP systems.

Installation Qualification (IQ): The documented verification that infrastructure components are installed correctly and in accordance with approved specifications, manufacturer recommendations, and the As Built Document.

Kneat: A validated electronic quality management platform used for the authoring, execution, review, and approval of qualification test scripts and documentation, providing an auditable electronic record in compliance with 21 CFR Part 11 and EU GMP Annex 11.

Operational Qualification (OQ): The documented verification that infrastructure components operate as intended across their defined operational range and in accordance with approved functional specifications.

Performance Qualification (PQ): The documented verification that infrastructure components consistently perform in accordance with defined requirements under representative operational conditions.

Qualification: The process of demonstrating and documenting that infrastructure components are fit for their intended purpose and operate in a controlled, consistent, and compliant manner. Qualification follows a documented lifecycle methodology comprising Planning, Testing, and Operational phases as defined in the Infrastructure Qualification Plan.

Requalification: A formal reassessment of the qualified state of an infrastructure component, required whenever an approved change is made that may affect the component's validated or qualified status. The scope of requalification must be assessed and documented prior to implementation of the change.

Request for Change (RFC): A formal submission initiating the change control process for a proposed modification to qualified infrastructure. All RFCs must be processed in accordance with GIT-SOP-00001 Change Management Process.

Subject Matter Expert (SME): An individual with demonstrated knowledge and expertise in a specific technology, process, or system relevant to the qualification activity. Post-execution test script review must be performed by a non-tester SME who is qualified and trained on the relevant process and system.

Test Script: A controlled document specifying the step-by-step instructions, expected results, and acceptance criteria for a discrete qualification test. Test scripts must be numbered sequentially and include the type of testing designation as part of the document number. Test scripts must be developed based on components and configurations documented in the As Built Document to ensure traceability.

Vendor Qualification: The process by which technology vendors are evaluated and approved prior to use in accordance with the organisation's Global Vendor Program. Vendor-supplied technology must not be deployed in qualified infrastructure until vendor approval has been obtained.

5.0 MATERIALS

The following materials, tools, platforms, and documentation resources are required to support the execution of infrastructure qualification activities in accordance with this SOP. All items listed must be available, approved, and version-controlled prior to the commencement of any qualification phase. Vendor-supplied technology must be approved prior to use in accordance with the Global Vendor Program. This section is subject to controlled document management; all referenced templates and diagrams must carry a header and footer indicating document title, document number, revision number, effective date, and Page x of y pagination on every page.

  5.1 Hardware and Infrastructure Components

  The physical and virtual hardware components listed below must be identified, inventoried, and approved prior to inclusion in any qualification scope. All hardware must be procured through approved vendor channels consistent with the Global Vendor Program requirements and must be documented within the As Built Document before testing commences.

    5.1.1 Physical servers, blade chassis, and rack-mounted compute nodes designated for GxP or GxP-supporting workloads.

    5.1.2 Storage area network (SAN) arrays, network-attached storage (NAS) devices, and direct-attached storage (DAS) units.

    5.1.3 Network switching and routing equipment, including core, distribution, and access-layer devices.

    5.1.4 Uninterruptible power supply (UPS) units, power distribution units (PDUs), and environmental monitoring sensors.

    5.1.5 Firewall appliances, load balancers, and hardware security modules (HSMs) where applicable.

    5.1.6 Cabling infrastructure, patch panels, and labelled rack layouts consistent with approved network diagrams.

  5.2 Software and Virtualization Platforms

  All software and virtualization platforms used within the qualified infrastructure must be approved, licensed, and version-controlled. Software versions must be recorded in the As Built Document and Baseline Configuration documents prior to the commencement of any testing, in accordance with GLBL-SOP-00045 Configuration Management SOP.

    5.2.1 Hypervisor platforms (e.g., VMware vSphere, Microsoft Hyper-V) used to host virtual machines supporting GxP workloads.

    5.2.2 Operating system distributions and patch levels for all in-scope servers, documented to the specific version and build number.

    5.2.3 Container orchestration platforms (e.g., Kubernetes, Docker Enterprise) where containerised workloads are within qualification scope.

    5.2.4 Backup and recovery software, including agents and management consoles, required to validate data protection controls.

    5.2.5 Monitoring and alerting platforms (e.g., SIEM tools, infrastructure monitoring agents) used to demonstrate operational controls during the Operational Phase.

    5.2.6 Identity and access management (IAM) software and directory services (e.g., Active Directory, LDAP) subject to annual account access review requirements.

  5.3 Cloud Service Provider Tools and Portals

  Where qualification scope includes cloud-hosted infrastructure, the following cloud service provider (CSP) tools and management portals must be accessible to authorised personnel and must be configured in accordance with approved architecture blueprints. CSP tooling must be approved through the Global Vendor Program prior to use in a GxP context.

    5.3.1 CSP management consoles and administrative portals (e.g., AWS Management Console, Microsoft Azure Portal, Google Cloud Console) used to provision, configure, and evidence in-scope resources.

    5.3.2 Infrastructure-as-Code (IaC) tooling (e.g., Terraform, AWS CloudFormation, Azure Resource Manager templates) used to deploy and document baseline configurations.

    5.3.3 Cloud-native identity and access management tools used to enforce least-privilege access controls and support annual account access reviews.

    5.3.4 CSP audit logging and monitoring services (e.g., AWS CloudTrail, Azure Monitor, Google Cloud Audit Logs) required to provide evidence of system behaviour during test execution.

    5.3.5 CSP compliance and security posture management dashboards used to assess and document the qualified state of cloud infrastructure during Annual Reviews.

  5.4 Qualification and Validation Documentation Templates

  All qualification documentation must be controlled, versioned, and approved in accordance with the Infrastructure Qualification Plan (IQP) lifecycle methodology. The IQP and As Built Document must be approved by authorised personnel, including GCVQA review and approval by dated signature for GxP systems, prior to the commencement of any testing. Documents must be initialled and dated or signed and dated by authorised personnel. Electronic signatures executed via Kneat or DocuSign must comply with 21 CFR Part 11 data integrity requirements, including single-user setup per day and single tester control per test script.

    5.4.1 Infrastructure Qualification Plan (IQP) template, including sections for scope definition, risk assessment, qualification strategy, and approval signature blocks.

    5.4.2 As Built Document template used to record the final, approved configuration of all in-scope infrastructure components prior to test execution.

    5.4.3 Baseline Configuration Document template used to capture and version-control the verified reference state of each qualified component before testing commences.

    5.4.4 Test script templates, numbered sequentially and incorporating the type-of-testing designation as part of the script number, with fields for tester signature, execution date, pass/fail result, and post-execution SME review sign-off.

    5.4.5 Infrastructure Qualification Report (IQR) template, subject to GCVQA review and approval by dated signature for GxP systems, summarising test outcomes, deviations, and qualification conclusions.

    5.4.6 Deviation Report template for documenting deviations identified during test execution, including root cause analysis, impact assessment, and QA review fields.

    5.4.7 Annual Review template used to evaluate the ongoing qualified state of infrastructure and record the outcomes of annual account access reviews.

    5.4.8 Change Control Request for Change (RFC) template aligned with GIT-SOP-00001 Change Management Process, used to initiate and document all changes to qualified infrastructure components.

  5.5 Network Diagrams and Architecture Blueprints

  Current, approved network diagrams and architecture blueprints must be available before qualification activities commence. These documents must reflect the as-built state of the infrastructure, must be version-controlled, and must carry the required header and footer information on every page. Any change to qualified infrastructure that results in a deviation from approved diagrams must be processed through formal change control per GIT-SOP-00001 Change Management Process, and requalification scope must be assessed accordingly.

    5.5.1 Logical network diagrams depicting IP addressing schemes, VLAN segmentation, routing paths, and security zone boundaries for all in-scope environments.

    5.5.2 Physical network diagrams showing rack layouts, cabling paths, port assignments, and physical device locations within data centre facilities.

    5.5.3 Cloud architecture blueprints illustrating virtual network topology, subnet design, security group configurations, and integration points with on-premises infrastructure.

    5.5.4 Data flow diagrams identifying the movement of GxP data across in-scope infrastructure components, used to support risk assessment and qualification scoping activities.

    5.5.5 Disaster recovery and high-availability architecture diagrams documenting failover configurations, replication targets, and recovery point and time objectives for qualified systems.

6.0 PROCEDURE

All infrastructure qualification activities must follow a structured lifecycle methodology comprising Planning and Design, Testing, and Operational phases. Each phase must be completed in sequence, with required approvals obtained before proceeding to the next phase. All qualification documentation must be controlled and versioned in accordance with 21 CFR Part 11 and GAMP 5 (Second Edition, 2022), with a header and footer on every page indicating document title, qualification project number, document version, effective date, and Page x of y pagination.

  6.1 Infrastructure Qualification Planning and Strategy

  The qualification planning phase establishes the scope, approach, roles, and documentation requirements for each qualification project. All planning activities must be completed and approved before any testing commences.

    6.1.1 Infrastructure Qualification Plan (IQP)

    An Infrastructure Qualification Plan must be authored and approved by designated stakeholders, including GCVQA, prior to the commencement of any testing activity. The IQP must define the qualification lifecycle phases, scope of infrastructure components, risk classification, testing strategy, roles and responsibilities, and acceptance criteria. The IQP must be version-controlled and stored within the organisation's controlled document management system consistent with 21 CFR Part 11.

    6.1.2 As Built Document

    An As Built Document must be created to capture the actual installed configuration of all infrastructure components in scope. The As Built Document must be approved prior to the commencement of any testing. Test scripts must be developed based on the components and configurations documented in the As Built Document to ensure full traceability between design and test evidence.

    6.1.3 Baseline Configuration

    Baseline Configuration documents must be created and approved prior to the commencement of any testing. These documents establish the verified reference state of all in-scope infrastructure components and must be maintained in accordance with GLBL-SOP-00045 Configuration Management SOP.

    6.1.4 Vendor Approval

    All vendor-supplied technology must be approved prior to use in accordance with the Global Vendor Program. Evidence of vendor approval must be referenced within the IQP.

    6.1.5 Training Requirements

    All personnel executing qualification activities must complete role-specific training before performing any qualification task. Training records must be maintained per applicable GxP requirements and must be available for review prior to test script execution. A non-tester Subject Matter Expert who is qualified and trained on the process and system must perform post-execution review of all test scripts.

  6.2 Risk Assessment and Impact Classification

  A formal risk assessment must be performed for all infrastructure components within the qualification scope. Risk assessment must be documented within the IQP or as a standalone risk register and must inform the depth and breadth of qualification testing required.

    6.2.1 GxP Impact Assessment

    Each infrastructure component must be assessed to determine its GxP impact classification. Components that directly support GxP systems or processes must be subject to full IQ, OQ, and PQ activities. Components with indirect or no GxP impact must be documented with a rationale supporting the reduced qualification approach, consistent with GAMP 5 (Second Edition, 2022).

    6.2.2 Deviation Classification

    Deviations identified during qualification must be classified as critical, major, or minor based on their potential impact on system fitness for purpose and GxP compliance. All deviations must be documented in a formal deviation report that includes a description of the deviation, root cause analysis, impact assessment, and proposed resolution. No qualification phase may be closed while an unresolved critical or major deviation remains open. QA review and approval of all deviations is mandatory before proceeding.

    6.2.3 Change Control Integration

    All changes to qualified infrastructure must be processed through formal change control in accordance with GIT-SOP-00001 Change Management Process. For every approved change, the requalification scope must be assessed and documented prior to implementation. Requalification activities must be proportionate to the risk and impact of the change as determined by the risk assessment.

  6.3 Installation Qualification (IQ) for On-Premises Infrastructure

  Installation Qualification must verify that all on-premises infrastructure components are installed in accordance with approved design specifications, vendor requirements, and the As Built Document. IQ must be completed and approved before OQ activities commence.

    6.3.1 IQ Test Script Preparation

    IQ test scripts must be numbered sequentially and must include the type of testing designation as part of the script number. Each test script must reference the corresponding As Built Document component and must define the expected result and acceptance criteria for each test step. Test scripts must be approved prior to execution.

    6.3.2 IQ Execution

    IQ test scripts must be executed by qualified personnel. Where DocuSign is used for electronic signature of test script execution, usage must comply with Data Integrity requirements, including single-user setup per day and single tester control per test script, consistent with 21 CFR Part 11. All test evidence must be captured contemporaneously and attached to the test script record.

    6.3.3 Physical Safety During IQ

    Personnel performing IQ activities within the data centre must observe all physical safety requirements, including ESD precautions when handling hardware, adherence to hot and cold aisle access protocols, rack safety procedures, and electrical hazard awareness. Emergency shutdown procedures and escalation contacts must be reviewed prior to commencing on-site activities.

    6.3.4 IQ Review and Approval

    Post-execution review of all IQ test scripts must be performed by a non-tester SME who is qualified and trained on the process and system. The completed IQ package must be reviewed and approved by GCVQA by dated signature before OQ activities commence.

  6.4 Operational Qualification (OQ) for On-Premises Infrastructure

  Operational Qualification must verify that all on-premises infrastructure components operate within defined parameters and perform their intended functions under normal and boundary conditions. OQ must be completed and approved before PQ activities commence.

    6.4.1 OQ Test Script Preparation

    OQ test scripts must be numbered sequentially with the OQ type designation included in the script number. Test scripts must be traceable to the IQP acceptance criteria and the As Built Document. All OQ test scripts must be approved prior to execution.

    6.4.2 OQ Execution

    OQ test scripts must be executed by qualified personnel. Electronic signature of test execution records must comply with 21 CFR Part 11, including single-user setup per day and single tester control per test script where DocuSign is used. All deviations encountered during OQ execution must be classified, documented, and resolved in accordance with section 6.2.2 before the OQ phase is closed.

    6.4.3 Cybersecurity Controls Verification

    OQ must include verification of cybersecurity controls applicable to the infrastructure component, including access control configurations, network segmentation, and audit logging. Cybersecurity incident response procedures, including detection, containment, and escalation steps, must be verified as operational during OQ execution.

    6.4.4 OQ Review and Approval

    Post-execution review of all OQ test scripts must be performed by a non-tester SME. The completed OQ package must be reviewed and approved by GCVQA by dated signature before PQ activities commence.

  6.5 Performance Qualification (PQ) for On-Premises Infrastructure

  Performance Qualification must verify that all on-premises infrastructure components consistently perform in accordance with defined performance criteria under conditions representative of actual operational use. PQ must be completed and approved before the infrastructure is released for GxP operational use.

    6.5.1 PQ Test Script Preparation

    PQ test scripts must be numbered sequentially with the PQ type designation included in the script number. Test scripts must define performance thresholds, load conditions, and acceptance criteria aligned with the IQP. All PQ test scripts must be approved prior to execution.

    6.5.2 PQ Execution

    PQ test scripts must be executed by qualified personnel under conditions that simulate actual operational workloads. Electronic signature requirements per 21 CFR Part 11 apply to all PQ execution records. All deviations must be classified, documented, and resolved in accordance with section 6.2.2.

    6.5.3 PQ Review and Approval

    Post-execution review of all PQ test scripts must be performed by a non-tester SME. The completed PQ package, together with the Infrastructure Qualification Report (IQR), must be reviewed and approved by GCVQA by dated signature. The IQR must summarise all qualification phases, deviations, resolutions, and the overall qualification outcome.

    6.5.4 Annual Review

    Following initial qualification, an Annual Review must be executed to evaluate the ongoing qualified state of the infrastructure. Annual account access reviews must be conducted as part of the operational phase. Results of Annual Reviews must be documented and retained within the controlled document management system.

  6.6 Cloud Infrastructure Qualification Approach

  Cloud infrastructure qualification must follow the same structured lifecycle methodology as on-premises qualification, adapted to reflect the shared responsibility model between the organisation and the cloud service provider. All cloud qualification activities must comply with GAMP 5 (Second Edition, 2022) and EU GMP Annex 11 where applicable.

    6.6.1 Shared Responsibility Assessment

    Prior to qualification, a shared responsibility assessment must be performed to define which qualification activities are the responsibility of the organisation and which are covered by the cloud service provider. Evidence of cloud service provider controls, such as SOC 2 Type II reports or ISO/IEC 27001:2022 certifications, must be obtained and evaluated as part of the IQP. Vendor approval must be confirmed in accordance with the Global Vendor Program.

    6.6.2 Cloud IQ, OQ, and PQ Execution

    Cloud IQ must verify that the cloud environment is provisioned in accordance with the approved As Built Document and organisational security standards. Cloud OQ must verify that all configured services operate within defined parameters, including access controls, encryption, and audit logging consistent with 21 CFR Part 11. Cloud PQ must verify that the environment meets performance and availability requirements under representative operational conditions. All test scripts must be numbered sequentially with the appropriate testing type designation and must be approved prior to execution.

    6.6.3 Cloud Change Control and Requalification

    All changes to qualified cloud infrastructure must be processed through formal change control in accordance with GIT-SOP-00001 Change Management Process. Requalification scope must be assessed for every approved change. Configuration changes must be managed in accordance with GLBL-SOP-00045 Configuration Management SOP.

6.0 PROCEDURE

All infrastructure qualification activities must follow a structured lifecycle methodology comprising Planning and Design, Testing, and Operational phases. Each phase must be completed in sequence, with required approvals obtained before proceeding to the next phase. All qualification documentation must be controlled and versioned in accordance with 21 CFR Part 11 and GAMP 5 (Second Edition, 2022), with a header and footer on every page indicating document title, qualification project number, document version, effective date, and Page x of y pagination.

  6.1 Infrastructure Qualification Planning and Strategy

  The qualification planning phase establishes the scope, approach, roles, and documentation requirements for each qualification project. All planning activities must be completed and approved before any testing commences.

    6.1.1 Infrastructure Qualification Plan (IQP)

    An Infrastructure Qualification Plan must be authored and approved by designated stakeholders, including GCVQA, prior to the commencement of any testing activity. The IQP must define the qualification lifecycle phases, scope of infrastructure components, risk classification, testing strategy, roles and responsibilities, and acceptance criteria. The IQP must be version-controlled and stored within the organisation's controlled document management system consistent with 21 CFR Part 11.

    6.1.2 As Built Document

    An As Built Document must be created to capture the actual installed configuration of all infrastructure components in scope. The As Built Document must be approved prior to the commencement of any testing. Test scripts must be developed based on the components and configurations documented in the As Built Document to ensure full traceability between design and test evidence.

    6.1.3 Baseline Configuration

    Baseline Configuration documents must be created and approved prior to the commencement of any testing. These documents establish the verified reference state of all in-scope infrastructure components and must be maintained in accordance with GLBL-SOP-00045 Configuration Management SOP.

    6.1.4 Vendor Approval

    All vendor-supplied technology must be approved prior to use in accordance with the Global Vendor Program. Evidence of vendor approval must be referenced within the IQP.

    6.1.5 Training Requirements

    All personnel executing qualification activities must complete role-specific training before performing any qualification task. Training records must be maintained per applicable GxP requirements and must be available for review prior to test script execution. A non-tester Subject Matter Expert who is qualified and trained on the process and system must perform post-execution review of all test scripts.

  6.2 Risk Assessment and Impact Classification

  A formal risk assessment must be performed for all infrastructure components within the qualification scope. Risk assessment must be documented within the IQP or as a standalone risk register and must inform the depth and breadth of qualification testing required.

    6.2.1 GxP Impact Assessment

    Each infrastructure component must be assessed to determine its GxP impact classification. Components that directly support GxP systems or processes must be subject to full IQ, OQ, and PQ activities. Components with indirect or no GxP impact must be documented with a rationale supporting the reduced qualification approach, consistent with GAMP 5 (Second Edition, 2022).

    6.2.2 Deviation Classification

    Deviations identified during qualification must be classified as critical, major, or minor based on their potential impact on system fitness for purpose and GxP compliance. All deviations must be documented in a formal deviation report that includes a description of the deviation, root cause analysis, impact assessment, and proposed resolution. No qualification phase may be closed while an unresolved critical or major deviation remains open. QA review and approval of all deviations is mandatory before proceeding.

    6.2.3 Change Control Integration

    All changes to qualified infrastructure must be processed through formal change control in accordance with GIT-SOP-00001 Change Management Process. For every approved change, the requalification scope must be assessed and documented prior to implementation. Requalification activities must be proportionate to the risk and impact of the change as determined by the risk assessment.

  6.3 Installation Qualification (IQ) for On-Premises Infrastructure

  Installation Qualification must verify that all on-premises infrastructure components are installed in accordance with approved design specifications, vendor requirements, and the As Built Document. IQ must be completed and approved before OQ activities commence.

    6.3.1 IQ Test Script Preparation

    IQ test scripts must be numbered sequentially and must include the type of testing designation as part of the script number. Each test script must reference the corresponding As Built Document component and must define the expected result and acceptance criteria for each test step. Test scripts must be approved prior to execution.

    6.3.2 IQ Execution

    IQ test scripts must be executed by qualified personnel. Where DocuSign is used for electronic signature of test script execution, usage must comply with Data Integrity requirements, including single-user setup per day and single tester control per test script, consistent with 21 CFR Part 11. All test evidence must be captured contemporaneously and attached to the test script record.

    6.3.3 Physical Safety During IQ

    Personnel performing IQ activities within the data centre must observe all physical safety requirements, including ESD precautions when handling hardware, adherence to hot and cold aisle access protocols, rack safety procedures, and electrical hazard awareness. Emergency shutdown procedures and escalation contacts must be reviewed prior to commencing on-site activities.

    6.3.4 IQ Review and Approval

    Post-execution review of all IQ test scripts must be performed by a non-tester SME who is qualified and trained on the process and system. The completed IQ package must be reviewed and approved by GCVQA by dated signature before OQ activities commence.

  6.4 Operational Qualification (OQ) for On-Premises Infrastructure

  Operational Qualification must verify that all on-premises infrastructure components operate within defined parameters and perform their intended functions under normal and boundary conditions. OQ must be completed and approved before PQ activities commence.

    6.4.1 OQ Test Script Preparation

    OQ test scripts must be numbered sequentially with the OQ type designation included in the script number. Test scripts must be traceable to the IQP acceptance criteria and the As Built Document. All OQ test scripts must be approved prior to execution.

    6.4.2 OQ Execution

    OQ test scripts must be executed by qualified personnel. Electronic signature of test execution records must comply with 21 CFR Part 11, including single-user setup per day and single tester control per test script where DocuSign is used. All deviations encountered during OQ execution must be classified, documented, and resolved in accordance with section 6.2.2 before the OQ phase is closed.

    6.4.3 Cybersecurity Controls Verification

    OQ must include verification of cybersecurity controls applicable to the infrastructure component, including access control configurations, network segmentation, and audit logging. Cybersecurity incident response procedures, including detection, containment, and escalation steps, must be verified as operational during OQ execution.

    6.4.4 OQ Review and Approval

    Post-execution review of all OQ test scripts must be performed by a non-tester SME. The completed OQ package must be reviewed and approved by GCVQA by dated signature before PQ activities commence.

  6.5 Performance Qualification (PQ) for On-Premises Infrastructure

  Performance Qualification must verify that all on-premises infrastructure components consistently perform in accordance with defined performance criteria under conditions representative of actual operational use. PQ must be completed and approved before the infrastructure is released for GxP operational use.

    6.5.1 PQ Test Script Preparation

    PQ test scripts must be numbered sequentially with the PQ type designation included in the script number. Test scripts must define performance thresholds, load conditions, and acceptance criteria aligned with the IQP. All PQ test scripts must be approved prior to execution.

    6.5.2 PQ Execution

    PQ test scripts must be executed by qualified personnel under conditions that simulate actual operational workloads. Electronic signature requirements per 21 CFR Part 11 apply to all PQ execution records. All deviations must be classified, documented, and resolved in accordance with section 6.2.2.

    6.5.3 PQ Review and Approval

    Post-execution review of all PQ test scripts must be performed by a non-tester SME. The completed PQ package, together with the Infrastructure Qualification Report (IQR), must be reviewed and approved by GCVQA by dated signature. The IQR must summarise all qualification phases, deviations, resolutions, and the overall qualification outcome.

    6.5.4 Annual Review

    Following initial qualification, an Annual Review must be executed to evaluate the ongoing qualified state of the infrastructure. Annual account access reviews must be conducted as part of the operational phase. Results of Annual Reviews must be documented and retained within the controlled document management system.

  6.6 Cloud Infrastructure Qualification Approach

  Cloud infrastructure qualification must follow the same structured lifecycle methodology as on-premises qualification, adapted to reflect the shared responsibility model between the organisation and the cloud service provider. All cloud qualification activities must comply with GAMP 5 (Second Edition, 2022) and EU GMP Annex 11 where applicable.

    6.6.1 Shared Responsibility Assessment

    Prior to qualification, a shared responsibility assessment must be performed to define which qualification activities are the responsibility of the organisation and which are covered by the cloud service provider. Evidence of cloud service provider controls, such as SOC 2 Type II reports or ISO/IEC 27001:2022 certifications, must be obtained and evaluated as part of the IQP. Vendor approval must be confirmed in accordance with the Global Vendor Program.

    6.6.2 Cloud IQ, OQ, and PQ Execution

    Cloud IQ must verify that the cloud environment is provisioned in accordance with the approved As Built Document and organisational security standards. Cloud OQ must verify that all configured services operate within defined parameters, including access controls, encryption, and audit logging consistent with 21 CFR Part 11. Cloud PQ must verify that the environment meets performance and availability requirements under representative operational conditions. All test scripts must be numbered sequentially with the appropriate testing type designation and must be approved prior to execution.

    6.6.3 Cloud Change Control and Requalification

    All changes to qualified cloud infrastructure must be processed through formal change control in accordance with GIT-SOP-00001 Change Management Process. Requalification scope must be assessed for every approved change. Configuration changes must be managed in accordance with GLBL-SOP-00045 Configuration Management SOP.

  6.7 Network and Connectivity Qualification

  Network and connectivity qualification must verify that all network components, topologies, and data transmission pathways supporting GxP systems are configured, secured, and performing in accordance with approved design specifications documented in the As Built Document.

    6.7.1 Scope of Network Qualification

    The network qualification must encompass all physical and logical network components identified in the As Built Document, including but not limited to switches, routers, firewalls, load balancers, virtual LANs (VLANs), and wide-area network (WAN) links. Cloud-based networking constructs such as virtual private clouds (VPCs), security groups, and peering connections must also be included where applicable.

      6.7.1.1 The IT Infrastructure Engineer must confirm that the network topology as implemented matches the approved As Built Document prior to the commencement of any test script execution.

      6.7.1.2 Any discrepancy between the implemented network configuration and the approved As Built Document must be raised as a deviation per section 6.11 before testing proceeds.

    6.7.2 Network Test Script Execution

    Test scripts for network and connectivity qualification must be numbered sequentially and must include the type of testing designation as part of the script number, consistent with the IQP. Test scripts must be developed based on the components and configurations documented in the As Built Document to ensure full traceability.

      6.7.2.1 Each test script must verify connectivity between defined network segments, confirm VLAN segregation, validate firewall rule sets, and confirm that bandwidth and latency thresholds meet approved specifications.

      6.7.2.2 Electronic execution of test scripts must be performed using Kneat or DocuSign in compliance with 21 CFR Part 11 data integrity requirements. Where DocuSign is used, single-user setup per day and single tester control per test script must be enforced.

      6.7.2.3 Post-execution review of each network test script must be performed by a non-tester Subject Matter Expert (SME) who is qualified and trained on the process and system, as required by the IQP.

    6.7.3 Network Baseline Configuration

    A Baseline Configuration document for all network components must be created and approved prior to the commencement of any testing, in accordance with GLBL-SOP-00045 Configuration Management SOP. This document establishes the verified reference state against which all subsequent changes and requalification activities will be assessed.

    6.7.4 Physical Network Safety

    Personnel accessing physical network infrastructure within data centre environments must observe all applicable safety precautions, including electrostatic discharge (ESD) protocols, hot/cold aisle access restrictions, rack safety procedures, and electrical hazard awareness. Emergency shutdown procedures and escalation contacts must be posted at the point of access and must be reviewed by all personnel prior to commencing physical network work.

  6.8 Security Controls and Access Management Verification

  Security controls and access management verification must confirm that all logical and physical security measures protecting qualified infrastructure are implemented as specified in the approved design documentation and comply with 21 CFR Part 11, EU GMP Annex 11, and ISO/IEC 27001:2022.

    6.8.1 Access Control Verification

    The IT Infrastructure Engineer must verify that role-based access controls (RBAC) are configured in accordance with the principle of least privilege and that all user accounts are provisioned as documented in the As Built Document.

      6.8.1.1 All privileged accounts, service accounts, and shared accounts must be identified, documented, and subject to enhanced access controls. Generic or shared credentials must not be used for GxP system access.

      6.8.1.2 Annual account access reviews must be conducted as part of the Operational Phase to confirm that access rights remain appropriate and that dormant or unauthorised accounts are removed. Review outcomes must be documented and retained as qualification records.

    6.8.2 Security Configuration Testing

    Security configuration test scripts must be executed to verify that encryption standards, multi-factor authentication (MFA), audit logging, intrusion detection, and vulnerability management controls are active and functioning as specified.

      6.8.2.1 Audit log integrity must be verified to confirm that logs are complete, tamper-evident, and retained for the period specified in the approved data retention policy, consistent with 21 CFR Part 11 requirements.

      6.8.2.2 Vendor-supplied security technology must be approved prior to use in accordance with the Global Vendor Program before being incorporated into the qualified infrastructure.

    6.8.3 Cybersecurity Incident Response

    A documented cybersecurity incident response procedure must be in place and must be verified as operational during the security controls qualification. The procedure must address detection, containment, eradication, recovery, and escalation steps.

      6.8.3.1 Upon detection of a cybersecurity incident affecting qualified infrastructure, the System Administrator must immediately contain the affected system, notify the IT Security team and Quality Assurance (QA), and initiate a deviation report per section 6.11.

      6.8.3.2 Emergency escalation contacts, including the IT Security Lead, QA Lead, and Data Centre Operations Manager, must be documented in the IQP and must be accessible to all personnel executing qualification activities.

    6.8.4 GxP Security Review

    For GxP systems, the Global Computer Validation and Quality Assurance (GCVQA) team must review and approve all security control test scripts and associated results by dated signature prior to the issuance of the Qualification Summary Report.

  6.9 Disaster Recovery and Business Continuity Testing

  Disaster Recovery (DR) and Business Continuity (BC) testing must demonstrate that qualified infrastructure can be restored to a known good state within approved Recovery Time Objectives (RTOs) and Recovery Point Objectives (RPOs) following a disruptive event. All DR and BC testing must be planned, executed, and documented in accordance with the IQP.

    6.9.1 DR Test Planning

    The IT Infrastructure Engineer must develop DR test scripts based on the recovery scenarios and configurations documented in the As Built Document. Test scripts must be numbered sequentially and must include the type of testing designation as part of the script number.

      6.9.1.1 DR test scripts must define the specific recovery scenario, the systems in scope, the expected RTO and RPO, the step-by-step recovery procedure, and the acceptance criteria for each test.

      6.9.1.2 The IQP and As Built Document must be approved prior to the commencement of any DR testing.

    6.9.2 DR Test Execution

    DR tests must be executed by qualified personnel in a controlled environment that does not risk production data integrity. Electronic execution and sign-off must comply with 21 CFR Part 11 requirements using Kneat or DocuSign.

      6.9.2.1 Each DR test must record the actual recovery time achieved, the data recovery point achieved, any deviations from the expected procedure, and the pass or fail determination against acceptance criteria.

      6.9.2.2 Post-execution review of DR test scripts must be performed by a non-tester SME who is qualified and trained on the process and system.

    6.9.3 DR Test Outcomes and Remediation

    Where DR test results fail to meet approved RTOs or RPOs, or where the recovery procedure cannot be completed as documented, a deviation must be raised per section 6.11. Remediation actions must be completed and the test must be re-executed prior to the issuance of the Qualification Summary Report.

    6.9.4 Business Continuity Verification

    Business Continuity controls, including failover mechanisms, redundant systems, and manual workaround procedures, must be verified as part of the qualification lifecycle. Evidence of successful BC verification must be included in the Qualification Summary Report.

  6.10 Change Control and Requalification Triggers

  All changes to qualified infrastructure must be managed through the formal change control process in accordance with GIT-SOP-00001 Change Management Process. No change to a qualified infrastructure component may be implemented without an approved Request for Change (RFC). The requalification scope must be assessed for every approved change to determine the impact on the qualified state of the infrastructure.

    6.10.1 Change Control Process

    The System Administrator or IT Infrastructure Engineer proposing a change to qualified infrastructure must raise an RFC through the approved change management system in accordance with GIT-SOP-00001 Change Management Process.

      6.10.1.1 The RFC must document the nature of the change, the systems and components affected, the business justification, the risk assessment, the implementation plan, the rollback plan, and the proposed requalification scope.

      6.10.1.2 QA must review and approve all RFCs affecting GxP-qualified infrastructure prior to implementation. GCVQA review is required for changes to GxP systems.

      6.10.1.3 Configuration changes resulting from approved RFCs must be reflected in updated Baseline Configuration documents in accordance with GLBL-SOP-00045 Configuration Management SOP.

    6.10.2 Requalification Scope Assessment

    Following approval of an RFC, the IT Infrastructure Engineer must perform a formal requalification scope assessment to determine which qualification activities must be repeated to re-establish the qualified state of the affected infrastructure.

      6.10.2.1 The requalification scope assessment must be documented and must classify the impact of the change as: no requalification required, partial requalification required, or full requalification required. The rationale for the classification must be recorded.

      6.10.2.2 Where requalification is required, a revised or supplemental IQP must be prepared, approved, and executed in accordance with the qualification lifecycle defined in this SOP.

    6.10.3 Requalification Triggers

    Requalification must be assessed whenever any of the following events occur:

      6.10.3.1 A hardware component within the qualified infrastructure is replaced, upgraded, or decommissioned.

      6.10.3.2 A software version, operating system patch, or firmware update is applied to a qualified system.

      6.10.3.3 A network topology change, firewall rule modification, or access control policy update is implemented.

      6.10.3.4 A migration of qualified infrastructure between physical locations, data centres, or cloud environments is performed.

      6.10.3.5 An Annual Review identifies a gap in the qualified state of the infrastructure.

    6.10.4 Annual Review

    Annual Reviews must be executed during the Operational Phase to evaluate the ongoing qualified state of all infrastructure components in scope. The Annual Review must assess whether the infrastructure continues to operate within the parameters established during qualification, whether any undocumented changes have occurred, and whether the Baseline Configuration documents remain current.

      6.10.4.1 Annual Review outcomes must be documented in a formal Annual Review Report, reviewed by QA, and retained as controlled qualification records.

  6.11 Deviation Handling and Non-Conformance Reporting

  All deviations from approved test scripts, qualification procedures, or acceptance criteria identified during infrastructure qualification activities must be documented, classified, investigated, and resolved in accordance with this section. QA must review and approve all deviations before qualification activities may proceed past the point of the deviation.

    6.11.1 Deviation Classification

    Deviations must be classified according to the following severity levels:

      6.11.1.1 Critical: A deviation that directly impacts patient safety, data integrity, or regulatory compliance, or that renders a GxP system unfit for its intended purpose. Critical deviations require immediate escalation to QA and must halt all affected qualification activities until resolved.

      6.11.1.2 Major: A deviation that represents a significant departure from the approved procedure or acceptance criteria but does not immediately impact patient safety or data integrity. Major deviations require QA review and an approved remediation plan before qualification activities may continue.

      6.11.1.3 Minor: A deviation that represents a low-risk departure from the approved procedure with no impact on the qualified state of the system. Minor deviations must be documented and reviewed by QA but do not require a halt to qualification activities.

    6.11.2 Deviation Documentation Requirements

    All deviations must be documented in a formal Deviation Report at the time of identification. The Deviation Report must include:

      6.11.2.1 A unique deviation identifier linked to the relevant test script number and IQP reference.

      6.11.2.2 A clear description of the deviation, including the expected result, the actual result, and the point in the procedure at which the deviation occurred.

      6.11.2.3 The deviation classification (Critical, Major, or Minor) with documented justification.

      6.11.2.4 An impact assessment evaluating the effect of the deviation on the qualified state of the infrastructure, data integrity, and GxP compliance.

      6.11.2.5 A root cause analysis identifying the underlying cause of the deviation.

      6.11.2.6 Proposed corrective actions and the responsible owner and target completion date for each action.

      6.11.2.7 QA review and approval by dated signature prior to the resumption of affected qualification activities.

    6.11.3 Impact Assessment Before Proceeding

    A documented impact assessment must be completed for every deviation before qualification activities may proceed. The impact assessment must evaluate whether the deviation affects the validity of previously executed test scripts, whether retesting is required, and whether the deviation has implications for other infrastructure components or dependent GxP systems.

    6.11.4 QA Review and Approval

    QA must review and approve all Deviation Reports, impact assessments, and corrective action plans by dated signature. For GxP systems, GCVQA must also review and approve deviations classified as Critical or Major. No qualification activity that has been halted due to a deviation may resume until written QA approval has been obtained.

    6.11.5 Non-Conformance Reporting

    Where a deviation cannot be resolved within the scope of the current qualification activity, or where the root cause indicates a systemic issue, a formal Non-Conformance Report (NCR) must be raised and managed through the organisation's quality management system. The NCR must be referenced in the Qualification Summary Report.

  6.12 Qualification Summary Report and Approval

  Upon completion of all qualification phases and resolution of all open deviations, the IT Infrastructure Engineer must prepare a Qualification Summary Report (QSR) that consolidates the results of all qualification activities and formally declares the qualified state of the infrastructure. The QSR must be reviewed and approved prior to the infrastructure being placed into operational use for GxP purposes.

    6.12.1 QSR Content Requirements

    The Qualification Summary Report must include the following elements:

      6.12.1.1 A reference to the approved IQP, including the qualification project number, version, and approval date.

      6.12.1.2 A summary of the infrastructure components qualified, cross-referenced to the As Built Document.

      6.12.1.3 A complete listing of all test scripts executed, including script number, type of testing designation, execution date, tester identity, post-execution reviewer identity, and pass or fail result.

      6.12.1.4 A summary of all deviations raised during qualification, including deviation identifier, classification, root cause, corrective actions taken, and QA approval status.

      6.12.1.5 Confirmation that all Baseline Configuration documents have been created, approved, and are current as of the date of the QSR.

      6.12.1.6 Results of DR and BC testing, including actual RTOs and RPOs achieved versus approved targets.

      6.12.1.7 Confirmation that all vendor-supplied technology used in the qualified infrastructure has been approved in accordance with the Global Vendor Program.

      6.12.1.8 A formal qualification conclusion statement declaring whether the infrastructure is qualified, conditionally qualified, or not qualified, with supporting rationale.

    6.12.2 QSR Document Control

    The QSR is subject to controlled document management. Every page of the QSR must carry the approved header and footer including document title, qualification project number, document version, effective date, and Page x of y pagination. The QSR must be version-controlled and stored in the approved document management system.

    6.12.3 QSR Review and Approval

    The QSR must be reviewed and approved by the following personnel by dated signature, using wet or electronic signature compliant with 21 CFR Part 11:

      6.12.3.1 The IT Infrastructure Engineer responsible for executing the qualification activities must review the QSR for technical accuracy and completeness.

      6.12.3.2 The System Owner must review the QSR to confirm that the qualified infrastructure meets the operational requirements of the supported GxP system.

      6.12.3.3 QA must review and approve the QSR to confirm that all qualification activities have been completed in accordance with the IQP and that all deviations have been resolved.

      6.12.3.4 For GxP systems, GCVQA must review and approve the QSR by dated signature before the infrastructure may be placed into GxP operational use, consistent with the requirement for GCVQA review and approval of both the IQP and the Infrastructure Qualification Report (IQR).

    6.12.4 Transition to Operational Phase

    Following QSR approval, the infrastructure must be formally transitioned to the Operational Phase. The transition must be documented and must confirm that all Baseline Configuration documents are in place, that Annual Review and annual account access review schedules have been established, and that ongoing change control obligations under GIT-SOP-00001 Change Management Process and GLBL-SOP-00045 Configuration Management SOP are understood and assigned to named owners.

      6.12.4.1 All personnel responsible for operating or maintaining the qualified infrastructure must have completed role-specific training before assuming operational responsibilities. Training records must be maintained per applicable GxP requirements and must be available for inspection upon request.

7.0 REFERENCES

The following documents, standards, and regulations are referenced within this SOP and must be consulted in conjunction with its requirements. All referenced SOPs and guidance documents are subject to controlled document management and must be accessed via the organisation's official document management system to ensure the current approved version is in use.

  7.1 Regulatory Standards and Guidance

    7.1.1 21 CFR Part 11 — Electronic Records; Electronic Signatures (U.S. Food and Drug Administration)

    7.1.2 EU GMP Annex 11 — Computerised Systems (European Medicines Agency)

    7.1.3 GAMP 5: A Risk-Based Approach to Compliant GxP Computerised Systems (Second Edition, 2022) — International Society for Pharmaceutical Engineering (ISPE)

    7.1.4 ISO/IEC 27001:2022 — Information Security Management Systems — Requirements

    7.1.5 ICH Q9 (R1) — Quality Risk Management

    7.1.6 ICH Q10 — Pharmaceutical Quality System

  7.2 Organisational SOPs and Controlled Documents

    7.2.1 GIT-SOP-00001 — Change Management Process: governs all Requests for Change (RFCs) affecting qualified infrastructure components, as referenced in Section 6.0 of this SOP.

    7.2.2 GLBL-SOP-00045 — Configuration Management SOP: governs the creation, maintenance, and control of Baseline Configuration documents and As Built documents, as referenced in Section 6.0 of this SOP.

    7.2.3 Global Vendor Program — Vendor Qualification and Approval Policy: all vendor-supplied technology must be approved prior to use in accordance with this programme.

    7.2.4 Infrastructure Qualification Plan (IQP) Template — controlled template defining the planning, testing, and operational phase requirements for each qualification project.

    7.2.5 Infrastructure Qualification Report (IQR) Template — controlled template for documenting the outcomes of all qualification activities and obtaining GCVQA approval by dated signature.

    7.2.6 Data Integrity Policy — governs the use of electronic signature platforms including DocuSign and Kneat, including single-user setup per day and single tester control per test script requirements.

    7.2.7 Annual Review SOP — defines the process for executing Annual Reviews to evaluate the ongoing qualified state of infrastructure and conducting annual account access reviews.

    7.2.8 Deviation and CAPA Management SOP — defines the classification, documentation, root cause analysis, and QA review requirements for deviations identified during qualification activities.

    7.2.9 Training Management SOP — defines role-specific training requirements and the maintenance of training records per applicable GxP requirements.

8.0 REVISION HISTORY

| Revision | Effective Date | Reason for Revision |
|----------|---------------|---------------------|
| 1.0 | 2025-01-01 | Initial release of the Global Technology Infrastructure Qualification SOP. Establishes the documented qualification lifecycle methodology encompassing Planning, Testing, and Operational phases in accordance with GAMP 5 (Second Edition, 2022) and 21 CFR Part 11. Incorporates requirements for controlled documentation, electronic signature compliance, GxP review and approval workflows, change management per GIT-SOP-00001, and configuration management per GLBL-SOP-00045. |

---

| Field | Value |
|---|---|
| **Document ID** | {{document_id}} |
| **Version** | {{version}} |
| **Status** | {{status}} |
| **Effective Date** | {{effective_date}} |
| **Classification** | {{classification}} |

*This document is controlled. Unauthorised reproduction is prohibited.*  
*{{status}} — {{classification}}*  
*Always verify you are reading the current approved version before use.*