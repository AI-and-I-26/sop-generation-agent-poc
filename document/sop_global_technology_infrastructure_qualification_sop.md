# Global Technology Infrastructure Qualification SOP

## 1.0 PURPOSE
This Standard Operating Procedure (SOP) establishes the requirements and methodology for qualifying global technology infrastructure within a life sciences environment. It defines the structured lifecycle approach — encompassing requirements gathering, testing, and operational phases — that IT Qualification Engineers and System Administrators must follow to ensure infrastructure components are fit for their intended use and compliant with applicable regulatory and data integrity requirements. This SOP governs the creation, control, approval, and execution of all qualification documentation, including Infrastructure Qualification Plans (IQPs), As Built Documents, Baseline Configuration documents, and test scripts, ensuring that each artifact is properly versioned, approved, and traceable prior to and throughout the qualification effort. Adherence to this procedure supports consistent, auditable qualification practices across all sites and ensures that qualified infrastructure is accurately reflected in the Configuration Management Database (CMDB) upon acceptance.

## 2.0 SCOPE
This procedure applies to all global technology infrastructure qualification activities performed within the Life Sciences organization, including the qualification of servers, network devices, storage systems, virtual environments, and associated infrastructure components that support regulated operations. It governs the full qualification lifecycle from initial requirements gathering and documentation through the testing phase and into the operational phase, encompassing all sites, facilities, and environments where IT infrastructure is deployed in support of GxP or other regulated business functions. This procedure applies to IT Qualification Engineers, System Administrators, authorized IT personnel, and approved vendors involved in the installation, configuration, testing, acceptance, and ongoing maintenance of qualified infrastructure. All qualification activities must adhere to the documentation, approval, change management, and data integrity requirements defined herein, including compliance with the Global Vendor Program for vendor and vendor-supplied technology approval. Where requalification is required, the scope and rationale for requalification must be described in the Scope and Process sections of the Infrastructure Qualification Plan prior to the commencement of any requalification activities.

## 3.0 RESPONSIBILITIES
The following roles and responsibilities apply to all activities performed under this Standard Operating Procedure.

| ROLE | RESPONSIBILITY |
|---|---|
| IT Qualification Engineer | Authors, executes, and reviews qualification documentation including the Infrastructure Qualification Plan (IQP), As Built Document, Baseline Configuration documents, and test scripts in accordance with this SOP. |
| IT Qualification Engineer | Ensures all qualification documentation is controlled, versioned, and formatted with the required header/footer elements including document title, qualification project number, document version, and Page x of y pagination. |
| IT Qualification Engineer | Numbers test scripts sequentially and includes the applicable testing type designation (e.g., IQ, UAT) as part of each script number. |
| IT Qualification Engineer | Labels all supporting documentation with the associated test script identification number and corresponding test step number(s). |
| IT Qualification Engineer | Ensures the IQP and As Built Document are approved prior to the commencement of any testing, and that Baseline Configuration documents are created prior to the start of testing. |
| IT Qualification Engineer | Describes the requalification scope in the Scope and Process sections of the IQP when requalification is required. |
| System Administrator | Implements infrastructure changes only when authorized, and ensures all changes, configurations, and patches are executed in accordance with applicable Change, Configuration, and Patch Management procedures during the Operational Phase. |
| System Administrator | Maintains Backup and Restore and Disaster Recovery procedures throughout the Operational Phase and ensures infrastructure items are entered into the Configuration Management Database (CMDB) upon acceptance. |
| System Administrator | Conducts the annual account access review as required during the Operational Phase. |
| DocuSign Sender | Sets up test scripts for a single user only on a single day in compliance with Data Integrity requirements governing electronic signature use. |
| Document Approver | Reviews and approves the IQP, As Built Document, and other qualification deliverables prior to the commencement of testing, providing a wet or electronic signature with date in accordance with applicable signature requirements. |
| Vendor / Authorized Third Party | Performs infrastructure changes only when authorized and approved, and must be qualified in accordance with the Global Vendor Program prior to performing any work or supplying technology used in qualification activities. |
| Quality Assurance | Reviews qualification documentation for compliance with this SOP, applicable regulatory requirements, and Data Integrity standards, and provides approval signatures as required. |

## 4.0 DEFINITIONS / ABBREVIATIONS

| TERM / ABBREVIATION | DEFINITION |
|---|---|
| As Built Document | A controlled document that captures the actual configuration, components, and settings of an infrastructure item as it exists at the time of qualification, used as the basis for test script development. |
| Baseline Configuration | A documented and approved record of the configuration state of an infrastructure item established prior to the commencement of any qualification testing, serving as a reference point for change control and requalification activities. |
| CMDB | Configuration Management Database — the authoritative repository into which all accepted and qualified infrastructure items must be entered and maintained throughout the Operational Phase. |
| Data Integrity | The assurance that data is complete, consistent, accurate, and maintained throughout its lifecycle in compliance with applicable regulatory requirements and internal controls. |
| DocuSign | An electronic signature platform used to obtain compliant signatures on qualification documents; usage must adhere to Data Integrity requirements, including the restriction that a DocuSign Sender may set up test scripts for a single user only on a single day. |
| IQ | Installation Qualification — a phase of qualification testing that verifies an infrastructure item has been installed in accordance with approved specifications and vendor requirements. |
| IQP | Infrastructure Qualification Plan — the master planning document that defines the scope, approach, roles, responsibilities, and testing strategy for a qualification project; must be approved prior to the commencement of any testing. |
| IT | Information Technology — the organizational function responsible for the design, implementation, and maintenance of technology infrastructure within the enterprise. |
| Kneat | A validated electronic qualification management platform used to author, execute, and approve qualification documentation, including test scripts and supporting records. |
| Operational Phase | The period following formal acceptance of a qualified infrastructure item during which Change, Configuration and Patch Management procedures, Backup and Restore and Disaster Recovery procedures, and annual account access reviews must be maintained. |
| Qualification | The structured process of demonstrating that IT infrastructure components are fit for their intended purpose through documented requirements gathering, installation verification, and functional testing activities. |
| Requalification | A qualification activity performed on a previously qualified infrastructure item following a significant change; the scope of requalification must be described in the Scope and Process sections of the applicable IQP. |
| SOP | Standard Operating Procedure — a controlled document that prescribes the steps required to perform a defined process in a consistent and compliant manner. |
| UAT | User Acceptance Testing — a phase of qualification testing that verifies an infrastructure item meets defined user requirements and performs as intended within the operational environment. |
| Vendor | An external supplier of technology, services, or components used in IT infrastructure qualification activities; vendors and vendor-supplied technology must be approved prior to use in accordance with the Global Vendor Program. |

## 6.0 PROCEDURE
The following subsections define the requirements and sequential activities for qualifying global technology infrastructure components within the life sciences environment. All personnel executing qualification activities shall adhere to the phases, documentation standards, and compliance requirements described herein.

  6.1  Document Requirements: All qualification documentation shall be controlled and versioned. Every document shall include a header and footer on each page containing the document title, qualification project number, document version, and pagination in Page x of y format. Documents shall bear a status banner designating the record as CURRENT, Confidential and Proprietary, and shall include a document approval signature block identifying the Author, Reviewer, and Approver roles with associated timestamps and user IDs. Signatures shall be wet or electronic; electronic signatures shall be executed via DocuSign or Kneat in compliance with applicable Data Integrity requirements.

  6.2  Overview: The qualification lifecycle for all infrastructure components shall follow three defined phases: a Requirements Gathering Phase, a Testing Phase, and an Operational Phase. An Infrastructure Qualification Plan (IQP) shall be developed prior to the commencement of any qualification activity. The IQP shall define the qualification scope, strategy, roles, acceptance criteria, and, where applicable, the requalification scope described within the Scope and Process sections of the IQP. The IQP shall be approved by authorized personnel before any testing commences. A risk assessment shall be performed for each infrastructure component or system subject to qualification. The risk assessment shall determine the impact classification of the component and shall inform the scope and depth of qualification testing required. General Safety requirements shall be observed for all infrastructure qualification activities.

  6.3  Process:
       6.3.1  Requirements Gathering Phase:
              6.3.1.1  The IQP shall be developed and approved prior to the commencement of any qualification activity, defining the qualification scope, strategy, roles, and acceptance criteria.
              6.3.1.2  The As Built Document shall be developed to capture the actual configuration, components, and settings of the infrastructure item as it exists at the time of qualification.
              6.3.1.3  Baseline Configuration documents shall be created and approved prior to the commencement of any testing.
              6.3.1.4  A risk assessment shall be documented and retained as a controlled qualification record, versioned and paginated in accordance with section 6.1.
              6.3.1.5  Impact classification shall consider the component's role in supporting GxP-regulated processes, data integrity, patient safety, and product quality.
              6.3.1.6  The risk assessment outcome shall be referenced in the IQP to justify the qualification strategy and the extent of testing assigned to each component.
              6.3.1.7  Vendors and vendor-supplied technology utilized in qualified infrastructure shall be approved prior to use in accordance with the Global Vendor Program.
              6.3.1.8  Infrastructure changes shall be made only by authorized IT personnel or by vendors who are authorized and approved in accordance with the Global Vendor Program.
              6.3.1.9  Where requalification is required, the scope of requalification activities shall be described in the Scope and Process sections of the IQP prior to the commencement of any requalification activities.

       6.3.2  Testing Phase:
              6.3.2.1  The IQP and the As Built Document shall be approved prior to the commencement of any testing.
              6.3.2.2  Test scripts shall be numbered sequentially and shall include the applicable testing type designation (e.g., IQ, UAT) as part of each script number.
              6.3.2.3  Supporting documentation generated during test execution shall be labeled with the associated test script identification number and the applicable test step number or numbers.
              6.3.2.4  All test scripts shall be initialed and dated or signed and dated, using wet or electronic signature, upon execution and review.
              6.3.2.5  Installation Qualification (IQ) activities shall verify that infrastructure components are installed correctly, that the physical and logical environment meets defined specifications, and that all documentation accurately reflects the installed configuration. IQ test scripts shall be developed based on the components and configuration documented in the As Built Document.
              6.3.2.6  Operational Qualification (OQ) activities shall verify that infrastructure components operate as intended across their defined operational range and that all functional requirements are met under normal and boundary conditions. OQ testing shall not commence until IQ has been successfully completed or formally accepted with documented deviations resolved.
              6.3.2.7  Performance Qualification (PQ) activities shall verify that infrastructure components consistently perform within defined specifications under conditions representative of actual operational use. PQ testing shall not commence until OQ has been successfully completed or formally accepted with documented deviations resolved.
              6.3.2.8  Network infrastructure and connectivity components that support GxP-regulated systems or processes shall be subject to qualification in accordance with the risk assessment and impact classification. Baseline Configuration documents for network components, including switches, routers, firewalls, and related devices, shall be created and approved prior to the commencement of any testing.
              6.3.2.9  Data integrity verification activities shall confirm that audit trail functionality is enabled and captures all required system events, that audit trail records are time-stamped and attributable to individual user accounts, and that data storage configurations enforce integrity controls as specified in the As Built Document.
              6.3.2.10  Security controls verification shall confirm that user account provisioning and role-based access controls are configured in accordance with the principle of least privilege, that password policies and multi-factor authentication requirements conform to approved security standards, and that administrative and privileged accounts are restricted to authorized IT personnel only.
              6.3.2.11  Disaster recovery testing shall verify that the qualified infrastructure can be restored to a defined operational state within the approved Recovery Time Objective (RTO) and Recovery Point Objective (RPO) following a simulated failure event.
              6.3.2.12  Deviations identified during test execution shall be documented, assessed for impact, and resolved prior to phase acceptance. A deviation shall be raised whenever a test step result does not meet the defined acceptance criteria, an unexpected system behavior is observed, or a procedural departure from the approved test script occurs.
              6.3.2.13  Upon successful completion and acceptance of IQ, qualified infrastructure items shall be entered into the Configuration Management Database (CMDB).

       6.3.3  Operational Phase:
              6.3.3.1  No infrastructure component shall be placed into operational use until the Qualification Summary Report (QSR) has received all required approvals.
              6.3.3.2  Upon QSR approval, the Operational Phase shall commence and the CMDB record shall be updated to reflect the accepted qualification status of each infrastructure component.
              6.3.3.3  All changes to qualified infrastructure during the Operational Phase, including hardware replacements, software upgrades, configuration modifications, and patch applications, shall be initiated, reviewed, and approved through the site Change Control process prior to implementation.
              6.3.3.4  Changes shall be made only by authorized IT personnel or authorized and approved vendors in accordance with the Global Vendor Program.
              6.3.3.5  Backup and Restore and Disaster Recovery procedures shall be maintained and periodically reviewed during the Operational Phase to ensure continued effectiveness and compliance with approved specifications.
              6.3.3.6  The CMDB shall be updated to reflect all approved changes to qualified infrastructure items following successful completion of change implementation and any required requalification activities.

       6.3.4  Ongoing Maintenance: Change, Configuration, and Patch Management procedures must be followed during the Operational Phase for all modifications to qualified infrastructure components. Following implementation of an approved change, the IT Qualification Engineer shall perform a change impact assessment to determine whether requalification activities are required. The assessment shall consider the nature and extent of the change relative to the original qualification scope, the potential impact on validated or qualified system functions, and regulatory and compliance implications. Configuration and Patch Management activities shall be documented and traceable to the associated change control record throughout the Operational Phase.

       6.3.5  Annual Review:
              6.3.5.1  An annual account access review shall be conducted as part of the Operational Phase to ensure continued appropriateness of user access rights.
              6.3.5.2  The annual review shall confirm that administrative and privileged accounts remain restricted to authorized IT personnel only and that role-based access controls remain consistent with the principle of least privilege.
              6.3.5.3  Results of the annual account access review shall be documented and retained as controlled records in accordance with site document control procedures.

       6.3.6  Deliverable Requirements:
              6.3.6.1  The Infrastructure Qualification Plan (IQP) shall be a controlled document approved by authorized personnel prior to the commencement of any testing. The IQP shall define the qualification scope, approach, roles, responsibilities, testing strategy, and, where applicable, the requalification scope.
              6.3.6.2  The As Built Document shall be a controlled document approved prior to the commencement of any testing. It shall capture the actual components and configuration of the qualified infrastructure and shall serve as the basis for test script development.
              6.3.6.3  Baseline Configuration documents shall be created and approved prior to the commencement of any testing and shall serve as a reference point for change control and requalification activities.
              6.3.6.4  Test scripts shall be numbered sequentially and shall include the applicable testing type designation as part of the script number. All supporting documentation shall be labeled with the associated test script identification number and test step number(s).
              6.3.6.5  The Qualification Summary Report (QSR) shall be prepared by the IT Qualification Engineer upon completion of all test script execution, deviation resolution, and CAPA closure activities. The QSR shall include a summary of qualification scope, a listing of all test scripts executed, a summary of all deviations and CAPAs, confirmation that Baseline Configuration documents were completed prior to testing, confirmation that all qualified infrastructure items have been entered into the CMDB, and an overall qualification conclusion. The QSR shall be reviewed by the Qualification Lead and approved by the System Owner and Quality representative prior to operational acceptance.

       6.3.7  Infrastructure Qualification Report (IQR): The IQR serves as the formal record of qualification execution outcomes and provides the basis for operational acceptance of the qualified infrastructure. The IQR shall be a controlled document versioned in accordance with site document control procedures, with a header and footer on every page containing the document title, qualification project number, document version, and pagination in Page x of y format. Approval shall be executed via wet or electronic signature (DocuSign or Kneat), with each signatory providing their name, role, user ID, and timestamp. All open deviations and associated CAPAs shall be reviewed and resolved prior to approval of the IQR. The disposition of each deviation shall be documented within the IQR.

       6.3.8  DocuSign Usage Requirements: Where DocuSign is used to execute test scripts, a DocuSign Sender shall set up each test script for a single user only on a single day, in compliance with Data Integrity requirements. Test scripts shall not be configured to allow multiple users to sign on behalf of one another within the same execution instance.

| DocuSign Reason | Test Script Use |
|---|---|
| Data Integrity compliance | A DocuSign Sender must set up each test script for a single user only on a single day. |
| Electronic signature traceability | Each signatory must provide their name, role, user ID, and timestamp upon signing. |
| Prohibition on shared execution | Test scripts shall not be configured to allow multiple users to sign on behalf of one another within the same execution instance. |

## 7.0 REFERENCES

  7.1  SOPs:
       7.1.1  21 CFR Part 11 — Electronic Records; Electronic Signatures
       7.1.2  GAMP 5: A Risk-Based Approach to Compliant GxP Computerized Systems (ISPE)
       7.1.3  ICH Q10 — Pharmaceutical Quality System
       7.1.4  ISO/IEC 27001 — Information Security Management Systems
       7.1.5  Global Vendor Program SOP — Vendor qualification and approval requirements applicable to all vendors and vendor-supplied technology used in infrastructure qualification activities
       7.1.6  Change, Configuration and Patch Management SOP — Procedures governing authorized infrastructure changes, configuration updates, and patch deployment during the Operational Phase
       7.1.7  Backup and Restore and Disaster Recovery SOP — Procedures for maintaining backup, restore, and disaster recovery capabilities during the Operational Phase
       7.1.8  Data Integrity SOP — Requirements governing electronic signature usage, including DocuSign sender and single-user-per-day constraints for test script execution
       7.1.9  Configuration Management Database (CMDB) Procedure — Requirements for entering accepted infrastructure items into the CMDB following qualification acceptance
       7.1.10  Account Access Review Procedure — Requirements for conducting annual account access reviews as part of the Operational Phase
       7.1.11  General Safety and IT Infrastructure Policy — Safety requirements applicable to all IT infrastructure qualification activities
       7.1.12  Infrastructure Qualification Plan (IQP) Template — Master planning document defining qualification scope, approach, and requalification criteria; must be approved prior to commencement of any testing
       7.1.13  As Built Document Template — Records the actual components and configuration of the qualified infrastructure; must be approved prior to commencement of any testing
       7.1.14  Baseline Configuration Document Template — Captures the approved baseline configuration state; must be completed prior to commencement of any testing
       7.1.15  Test Script Template — Standardized format for IQ and UAT test scripts; scripts must be numbered sequentially and include the testing type designation as part of the script number
       7.1.16  Supporting Documentation Label Form — Used to label supporting documentation with the associated test script identification number and test step number(s)