---

| Field | Value |
|---|---|
| **Title** | Standard Operating Procedure for Responsible AI Use in Global Technology |
| **Document ID** | SOP-20260311-2028 |
| **Version** | 1.0 |
| **Status** | {{status}} |
| **Effective Date** | 11-Mar-2026 |
| **Classification** | {{classification}} |
| **Industry** | Life Sciences and Regulated IT (GxP-Aligned) |
| **Target Audience** | Global Technology Teams, AI Developers, Cloud Engineers, System Administrators, and Risk/Compliance Stakeholders |

> **{{status}} — {{classification}}**
> This document is subject to controlled document management.
> Approval signatures (wet or electronic per 21 CFR Part 11) are required
> before this SOP is placed into operational use.
> Always verify you are reading the current approved version before use.

---

1.0 PURPOSE

This Standard Operating Procedure (SOP) establishes the requirements, controls, and governance framework for the responsible development, deployment, validation, and ongoing management of Artificial Intelligence (AI) systems within the Global Technology function of a life sciences organisation. This SOP is subject to controlled document management; all revisions require approval signatures executed in accordance with 21 CFR Part 11 for electronic records, or wet-ink signatures where applicable, and every page of this document must carry a header and footer displaying the document title, document identifier, revision number, effective date, and page number in the format 'Page x of y', together with a 'CURRENT — Confidential and Proprietary' status designation.

This SOP ensures that all AI systems operating within or interfacing with GxP-regulated environments comply with applicable regulatory requirements, including but not limited to Computer System Validation (CSV) obligations, the organisation's Data Integrity Policy (GLBL-POL-00007), SOX compliance requirements for applicable financial applications such as SAP, and change management obligations governed by GIT-SOP-00001. All AI systems that generate, modify, or process electronic records subject to regulatory oversight must be developed, qualified, and maintained in a manner consistent with GAMP 5 (Second Edition, 2022), EU GMP Annex 11, and 21 CFR Part 11.

This SOP further establishes that all vendors supplying AI tools or platforms must receive formal approval prior to use in accordance with the Global Vendor Program. Retention, transfer, and disposal of GxP-regulated materials produced by or associated with AI systems must comply with GLBL-POL-00078, and secure destruction of confidential documents must comply with GLBL-POL-00050. A risk-based approach shall be applied to all AI system documentation, whereby the level of planning detail reflects the perceived size, impact, risk, complexity, and novelty of the system. All qualified AI systems and supporting infrastructure components must be registered in the Configuration Management Database (CMDB) upon acceptance into the production environment.

2.0 SCOPE

This SOP applies to all Global Technology personnel, AI developers, cloud engineers, system administrators, and risk and compliance stakeholders involved in the design, development, deployment, operation, maintenance, and retirement of artificial intelligence systems and AI-enabled tools within the organisation's technology environment. This document is subject to controlled document management; all revisions require approval signatures executed in accordance with 21 CFR Part 11 for electronic records, and every page of this SOP must carry a header and footer displaying the document title, document ID, revision number, effective date, and page number in the format page x of y, together with the status designation CURRENT and the Confidential and Proprietary classification.

  2.1 Included Systems and Activities: This SOP governs the following systems, activities, and personnel:

    2.1.1 All AI systems and AI-enabled tools used in life sciences operations that are subject to GxP alignment requirements, including systems that generate, process, or store electronic records subject to Data Integrity Policy GLBL-POL-00007.

    2.1.2 Computer systems subject to Computer System Validation (CSV) requirements, including AI-driven systems that support or interface with GxP-regulated processes, for which a formal Development Plan must be established as part of SDLC documentation.

    2.1.3 Financial and enterprise applications subject to SOX compliance requirements, including but not limited to SAP and any AI-augmented modules integrated therein.

    2.1.4 All qualified infrastructure components and AI systems for which changes must follow the established change management process defined in GIT-SOP-00001, and for which requalification scope must be assessed upon every approved change.

    2.1.5 All AI development projects for which a project file must be maintained containing all applicable formal documentation, including IQP, As Built Documents, Test Scripts, Baseline Configuration Documents, and IQR, each approved by dated signature before testing commences.

    2.1.6 All qualified AI systems and infrastructure components that must be registered in the Configuration Management Database (CMDB) upon acceptance and maintained therein throughout the system lifecycle.

    2.1.7 Vendor-supplied AI tools and services, which must receive vendor approval prior to use in accordance with the Global Vendor Program.

    2.1.8 All electronic records and AI-generated outputs subject to retention, transfer, or disposal requirements under GLBL-POL-00078, and confidential documentation subject to secure destruction requirements under GLBL-POL-00050.

  2.2 Excluded Systems and Activities: The following are outside the scope of this SOP:

    2.2.1 Non-GxP, non-SOX, and non-regulated personal productivity tools that do not interact with qualified systems, regulated data, or AI-generated outputs used in regulated decision-making.

    2.2.2 Research and exploratory AI prototypes operating exclusively within isolated sandbox environments that have no connectivity to production systems and do not process regulated or confidential data, provided such prototypes are formally designated as out-of-scope through the organisation's risk classification process.

  2.3 Geographic and Organisational Applicability: This SOP applies globally across all organisational sites, business units, and third-party engagements where the organisation's AI systems are deployed or maintained. All personnel, contractors, and vendors operating within scope must comply with the requirements set forth herein. A risk-based approach shall be applied to documentation and qualification activities, whereby the level of detail in planning documentation reflects the perceived size, impact, risk, complexity, and novelty of the system under consideration.

3.0 RESPONSIBILITIES

The following roles and responsibilities apply to all personnel involved in the development, deployment, administration, oversight, and use of AI-enabled systems within the Global Technology function. All personnel must complete role-specific training before executing any qualification, development, or administrative activity associated with AI systems. Training records must be maintained in accordance with applicable GxP requirements and made available for inspection upon request. Responsibilities are assigned in alignment with GxP principles, Computer System Validation (CSV) requirements, Data Integrity policy GLBL-POL-00007, and change management SOP GIT-SOP-00001.

| ROLE | RESPONSIBILITY |
|---|---|
| Global Technology Leadership | Accountable for the governance and strategic oversight of all AI-enabled systems within the Global Technology function, ensuring alignment with GxP, SOX, and CSV requirements. |
| Global Technology Leadership | Responsible for approving the formal Development Plan for all GxP AI systems as part of SDLC documentation prior to project initiation. |
| Global Technology Leadership | Responsible for ensuring that a Configuration Management Database (CMDB) entry is established and maintained for all qualified AI systems and infrastructure components upon acceptance. |
| Global Technology Leadership | Responsible for ensuring that all changes to qualified AI systems are processed through formal change control in accordance with GIT-SOP-00001 and that requalification scope is assessed for every approved change. |
| Global Technology Leadership | Responsible for ensuring that vendor approval is obtained prior to the use of any AI tool or platform, in accordance with the Global Vendor Program. |
| Global Technology Leadership | Responsible for ensuring that annual account access reviews are conducted for all qualified AI systems and that results are documented and retained. |
| AI Developers and Data Scientists | Responsible for developing AI models and systems in accordance with GxP-aligned SDLC documentation requirements, including the preparation and maintenance of a formal project file containing all applicable documentation readily available for inspection. |
| AI Developers and Data Scientists | Responsible for applying a risk-based approach to documentation, ensuring that the level of detail in planning documentation reflects the perceived size, impact, risk, complexity, and novelty of the AI system. |
| AI Developers and Data Scientists | Responsible for ensuring that peer review is documented for all GxP AI systems during the design and build phases, in accordance with CSV requirements. |
| AI Developers and Data Scientists | Responsible for ensuring that all qualification documents — including the Installation Qualification Plan (IQP), As Built Document, Test Scripts, Baseline Configuration Documents, and Installation Qualification Report (IQR) — are approved by dated signature before testing commences. |
| AI Developers and Data Scientists | Responsible for ensuring that AI-generated outputs are treated as electronic records subject to Data Integrity policy GLBL-POL-00007 and that data integrity controls are embedded at the point of design. |
| AI Developers and Data Scientists | Responsible for classifying and documenting deviations identified during development or testing, including root cause analysis and impact assessment, and for escalating deviations to QA for review and approval prior to proceeding. |
| Cloud Engineers and System Administrators | Responsible for the installation, configuration, and ongoing administration of AI-enabled infrastructure in accordance with approved qualification documentation and baseline configuration standards. |
| Cloud Engineers and System Administrators | Responsible for developing and maintaining technical work instructions for commonly repeated AI system administration tasks, including monitoring, capacity management, and lifecycle management. |
| Cloud Engineers and System Administrators | Responsible for ensuring that all changes to qualified infrastructure are submitted through formal change control per GIT-SOP-00001 and that requalification is triggered when changes affect qualified AI systems or infrastructure components. |
| Cloud Engineers and System Administrators | Responsible for maintaining CMDB entries for all qualified AI systems and infrastructure components, ensuring records are current and accurate at all times. |
| Cloud Engineers and System Administrators | Responsible for implementing physical data centre safety practices, including ESD precautions, hot/cold aisle access controls, rack safety protocols, and electrical hazard awareness, when performing hands-on infrastructure activities. |
| Cloud Engineers and System Administrators | Responsible for executing cybersecurity incident response procedures, including detection, containment, and escalation of security events affecting AI systems, in accordance with the organisation's incident response framework. |
| Risk and Compliance Stakeholders | Responsible for providing oversight and assurance that all AI-enabled systems comply with applicable GxP, SOX, CSV, and data integrity requirements, including Data Integrity policy GLBL-POL-00007. |
| Risk and Compliance Stakeholders | Responsible for reviewing and approving all deviation reports associated with qualified AI systems, including assessment of root cause, impact, and corrective and preventive actions (CAPAs) prior to system release or continued operation. |
| Risk and Compliance Stakeholders | Responsible for ensuring that retention, transfer, and disposal of GxP-regulated materials generated by or associated with AI systems comply with GLBL-POL-00078, and that secure destruction of confidential documents complies with GLBL-POL-00050. |
| Risk and Compliance Stakeholders | Responsible for conducting or coordinating annual account access reviews for all qualified AI systems and for ensuring that review outcomes are documented, actioned, and retained as controlled records. |
| Risk and Compliance Stakeholders | Responsible for assessing the compliance impact of proposed changes to qualified AI systems and for confirming that requalification scope has been appropriately defined before change implementation proceeds. |
| End Users of AI-Enabled Systems | Responsible for using AI-enabled systems only in accordance with approved procedures, user access privileges, and applicable training requirements, and must not operate any AI system for which role-specific training has not been completed and documented. |
| End Users of AI-Enabled Systems | Responsible for reporting anomalies, unexpected outputs, or potential data integrity concerns arising from AI-enabled systems to the system owner or designated support contact in a timely manner. |
| End Users of AI-Enabled Systems | Responsible for ensuring that AI-generated outputs used in GxP-regulated activities are reviewed, verified, and documented in accordance with Data Integrity policy GLBL-POL-00007 before those outputs are relied upon for regulated decisions or records. |
| End Users of AI-Enabled Systems | Responsible for adhering to cybersecurity awareness requirements and for escalating suspected security incidents involving AI-enabled systems to the appropriate IT security contact without delay. |

4.0 DEFINITIONS

The following terms and definitions apply throughout this Standard Operating Procedure. All personnel responsible for the development, deployment, validation, monitoring, or governance of AI and ML systems within the global technology environment must interpret these terms as defined below. These definitions are aligned with GxP regulatory expectations, Computer System Validation (CSV) requirements, and applicable industry frameworks including GAMP 5 (Second Edition, 2022) and EU GMP Annex 11.

Artificial Intelligence (AI): A class of computer-based systems designed to perform tasks that typically require human intelligence, including reasoning, learning, pattern recognition, natural language processing, and decision-making. In the context of this SOP, AI encompasses both rule-based systems and systems that learn from data.

Machine Learning (ML): A subset of Artificial Intelligence in which algorithms are trained on datasets to identify patterns, make predictions, or generate outputs without being explicitly programmed for each task. ML models used in GxP-regulated environments are subject to Computer System Validation requirements and must be documented in accordance with GAMP 5 (Second Edition, 2022).

GxP-Regulated Environment: Any operational context in which Good Practice (GxP) quality guidelines apply, including Good Manufacturing Practice (GMP), Good Clinical Practice (GCP), Good Laboratory Practice (GLP), and Good Distribution Practice (GDP). AI and ML systems operating within a GxP-regulated environment must comply with applicable regulatory requirements, including 21 CFR Part 11, EU GMP Annex 11, and the organisation's Data Integrity Policy (GLBL-POL-00007).

Responsible AI Principles: A set of ethical and operational standards governing the design, development, deployment, and retirement of AI systems. These principles include fairness, accountability, transparency, explainability, safety, privacy, and human oversight. All AI systems deployed within the global technology environment must be developed and maintained in accordance with these principles and consistent with applicable regulatory and organisational requirements.

AI Model Validation: The formal process of confirming that an AI or ML model performs as intended within its defined operational parameters and produces reliable, accurate, and reproducible outputs. AI model validation is a component of Computer System Validation (CSV) and must be executed in accordance with GAMP 5 (Second Edition, 2022), with all qualification documents — including Installation Qualification Plans (IQP), Test Scripts, and Installation Qualification Reports (IQR) — approved by dated signature prior to testing commencement.

Algorithmic Bias: Systematic and repeatable errors in AI or ML model outputs that result in unfair or inequitable outcomes, typically arising from flawed assumptions in the model design, unrepresentative training data, or inappropriate feature selection. Algorithmic bias must be identified, assessed, and mitigated as part of the risk-based approach to AI system development and validation.

Fairness: The property of an AI system whereby its outputs and decisions do not systematically disadvantage any individual, group, or population based on protected or sensitive characteristics. Fairness assessments must be documented as part of the AI risk classification and model validation processes.

Explainability: The degree to which the internal logic, decision pathways, and outputs of an AI or ML model can be understood and articulated in human-interpretable terms. Explainability is required for all AI systems used in regulated decision-making contexts and must be addressed in system design documentation consistent with EU GMP Annex 11 and GAMP 5 (Second Edition, 2022).

Transparency: The principle that the existence, purpose, data inputs, limitations, and decision logic of an AI system are disclosed to relevant stakeholders, including end users, regulators, and oversight bodies. Transparency requirements must be reflected in system documentation maintained within the project file and the Configuration Management Database (CMDB).

AI Risk Classification: A structured assessment process used to categorise AI systems according to the potential impact of their outputs on patient safety, data integrity, regulatory compliance, business operations, and ethical considerations. Risk classification determines the level of validation rigour, documentation depth, and governance controls required, consistent with the risk-based approach mandated by GAMP 5 (Second Edition, 2022) and the organisation's change management process (GIT-SOP-00001). Classifications are typically designated as high, medium, or low risk based on the perceived size, impact, complexity, and novelty of the system.

5.0 MATERIALS

The following materials, documents, templates, and reference frameworks shall be available to all personnel responsible for executing, reviewing, or overseeing activities governed by this SOP. All listed materials must be maintained under controlled document management in accordance with the organisation's document control procedures and, where applicable, must comply with 21 CFR Part 11 for electronic records and signatures. Personnel must ensure that only current, approved versions of these materials are used. Superseded versions must be archived and must not be used for active qualification or compliance activities.

  5.1 AI Governance Policy Documents

  The following governance documents establish the organisational policy framework for responsible AI use and must be consulted prior to initiating any AI development, deployment, or operational activity: the organisation's Responsible AI Use Policy; the Data Integrity Policy (GLBL-POL-00007), which must be adhered to for all electronic records including AI-generated outputs; the Retention, Transfer or Disposal of GxP Regulated Materials Policy (GLBL-POL-00078); the Secure Destruction of Confidential Documents Policy (GLBL-POL-00050); the Global Vendor Program policy governing vendor approval prior to use of any third-party AI tool or platform; and the Change Management SOP (GIT-SOP-00001), which must be followed for all modifications to qualified AI systems and infrastructure. A Configuration Management Database (CMDB) entry must be established and maintained for all qualified AI systems and infrastructure components upon acceptance into the production environment.

  5.2 Regulatory Guidance References (FDA, EMA, ICH)

  The following regulatory guidance documents and standards must be referenced when designing, validating, and operating AI systems within GxP-aligned and regulated IT environments: FDA Guidance on Artificial Intelligence and Machine Learning in Software as a Medical Device (SaMD); FDA 21 CFR Part 11 (Electronic Records and Electronic Signatures); EU GMP Annex 11 (Computerised Systems); EMA Reflection Paper on the Use of Artificial Intelligence in the Lifecycle of Medicines; ICH Q9(R1) (Quality Risk Management); ICH Q10 (Pharmaceutical Quality System); GAMP 5 (Second Edition, 2022) for risk-based approaches to compliant GxP computerised systems; and applicable SOX compliance requirements for AI tools integrated with financial systems such as SAP. These references must be reviewed periodically to ensure alignment with current regulatory expectations.

  5.3 AI Risk Assessment Templates

  Standardised risk assessment templates must be used for all AI systems subject to GxP or regulated IT requirements. Templates must support a risk-based approach consistent with ICH Q9(R1) and GAMP 5 (Second Edition, 2022), whereby the level of documentation detail reflects the perceived size, impact, risk, complexity, and novelty of the system under assessment. Required templates include: the AI System Risk Classification Template, used to categorise systems by GxP impact and business criticality; the Intended Use and Intended User Risk Assessment Form; the Algorithmic Bias and Fairness Assessment Template; and the Vendor Risk Assessment Form, completed prior to approval of any third-party AI vendor in accordance with the Global Vendor Program. All completed risk assessments must be approved by dated signature before qualification activities commence and must be retained in the applicable project file.

  5.4 Model Validation and Qualification Protocols

  All AI systems used in GxP operations must satisfy Computer System Validation (CSV) requirements and must be supported by a complete set of qualification and validation documentation. The following documents must be prepared, approved, and retained in the project file for each applicable system: a formal Development Plan as part of the SDLC documentation; an Installation Qualification Protocol (IQP) and Installation Qualification Report (IQR); an As-Built Document; Baseline Configuration Documents; Test Scripts; and, where applicable, Operational Qualification (OQ) and Performance Qualification (PQ) protocols. All qualification documents must be approved by dated signature before testing commences, in accordance with GAMP 5 (Second Edition, 2022) and EU GMP Annex 11. Peer review of design and build phase documentation must be performed and recorded for all GxP systems. Requalification must be triggered whenever changes are made to qualified AI systems or infrastructure, with scope assessed in accordance with GIT-SOP-00001.

  5.5 Data Management and Privacy Frameworks

  Data management activities associated with AI systems must be governed by the following frameworks and documents: the Data Integrity Policy (GLBL-POL-00007), which applies to all electronic records including AI-generated outputs and must be adhered to throughout the data lifecycle; applicable data privacy regulations including the EU General Data Protection Regulation (GDPR) and relevant national data protection legislation; the organisation's Data Classification Policy; and data retention and disposal procedures established under GLBL-POL-00078 and GLBL-POL-00050. AI systems processing personal data or sensitive health information must have a completed Data Protection Impact Assessment (DPIA) on file prior to go-live. All data management documentation must be maintained in the project file and must be available for inspection upon request.

  5.6 Incident Response and Deviation Forms

  The following forms and procedural documents must be available to all personnel involved in the operation, monitoring, and oversight of AI systems, and must be used whenever an incident, deviation, or non-conformance is identified: the AI Incident Report Form, used to document cybersecurity incidents, system failures, and unexpected AI outputs; the Deviation Report Form, which must capture deviation classification (critical, major, or minor), root cause analysis, and impact assessment in accordance with GxP requirements; the Corrective and Preventive Action (CAPA) Form; and the Emergency Escalation Contact List, which must include data centre safety contacts, cybersecurity incident response leads, and QA representatives. All completed incident and deviation records must be reviewed and approved by Quality Assurance prior to closure and must be retained in accordance with GLBL-POL-00078. Technical work instructions for AI system monitoring, capacity management, and lifecycle management must be developed, maintained, and made available to qualified personnel to support consistent and repeatable operational activities.

6.0 PROCEDURE

This section defines the mandatory procedural requirements governing the responsible identification, assessment, development, validation, and deployment of Artificial Intelligence systems within the Global Technology organisation. All personnel executing activities described herein must have completed role-specific training prior to performing any qualification or AI lifecycle activity, and training records must be maintained in accordance with applicable GxP requirements. All AI systems that support or interact with GxP-regulated processes must comply with Computer System Validation (CSV) requirements, Data Integrity Policy GLBL-POL-00007, and applicable change management controls as defined in GIT-SOP-00001. This SOP is subject to controlled document management; approval signatures, whether wet or electronic, must comply with 21 CFR Part 11. Every page of this document must carry a header displaying the document title, document ID, revision number, effective date, and page x of y notation, together with a CURRENT, Confidential and Proprietary footer.

  6.1 AI Use Case Identification and Intake

  All proposed AI use cases must be formally identified, documented, and submitted through the AI Intake process before any development, procurement, or deployment activity commences. This process ensures that AI initiatives are aligned with organisational strategy, regulatory obligations, and responsible AI principles prior to resource commitment.

    6.1.1 The requesting business unit or technology team must complete an AI Use Case Intake Form, capturing the intended purpose, target user population, data inputs and outputs, system dependencies, and anticipated business benefit of the proposed AI system.

    6.1.2 The intake submission must identify whether the proposed AI system will interact with, support, or produce outputs consumed by GxP-regulated processes, SOX-applicable applications such as SAP, or other controlled environments. This determination governs the applicable validation and compliance pathway.

    6.1.3 The AI Governance Lead or designated intake reviewer must assess each submission within ten business days of receipt and assign a preliminary classification of GxP, non-GxP regulated, or non-regulated to guide subsequent risk and ethical review activities.

    6.1.4 A project file must be established for every approved AI development or procurement initiative. This file must contain all applicable formal documentation and must be maintained in a location readily available for inspection by Quality Assurance and regulatory authorities.

    6.1.5 Any AI system sourced from an external vendor must not proceed beyond the intake stage until vendor approval has been obtained in accordance with the Global Vendor Program. Vendor qualification records must be retained within the project file.

    6.1.6 Approved intake records must be stored in the controlled document management system and referenced in the Configuration Management Database (CMDB) entry established for the AI system upon acceptance into the qualified environment.

  6.2 AI Risk Classification and Impact Assessment

  Every AI system that has passed the intake stage must undergo a formal risk classification and impact assessment before design or procurement activities proceed. The risk classification must follow a risk-based approach consistent with GAMP 5 (Second Edition, 2022) principles, whereby the level of documentation, testing rigour, and oversight is proportionate to the perceived size, impact, risk, complexity, and novelty of the system.

    6.2.1 The responsible AI Developer or System Owner must complete a Risk Classification Record that assigns the AI system to one of the following tiers: Critical (direct patient safety, product quality, or data integrity impact), High (indirect GxP impact or significant SOX financial reporting relevance), Medium (operational impact with limited regulatory exposure), or Low (administrative or analytical tools with no regulated output).

    6.2.2 The impact assessment must evaluate the following dimensions at minimum: patient safety and product quality risk, data integrity risk as defined under GLBL-POL-00007, cybersecurity and information security risk consistent with ISO/IEC 27001:2022, operational continuity risk, and regulatory inspection risk.

    6.2.3 For AI systems classified as Critical or High, a formal Risk Assessment Report must be authored, peer-reviewed, and approved by dated signature from the System Owner and Quality Assurance representative before design activities commence.

    6.2.4 Deviation classification thresholds must be established within the Risk Assessment Report. Deviations identified during any subsequent lifecycle phase must be classified as Critical, Major, or Minor based on their potential impact on patient safety, data integrity, or regulatory compliance. All deviations must be documented in a Deviation Report that includes a root cause analysis, impact assessment, and corrective action. Quality Assurance must review and approve all deviation records before the affected activity proceeds.

    6.2.5 The Risk Classification Record and Risk Assessment Report must be retained in the project file and referenced in the CMDB entry for the AI system. These records are subject to the retention requirements of GLBL-POL-00078 governing Retention, Transfer or Disposal of GxP Regulated Materials.

    6.2.6 Risk classification must be reviewed and, where necessary, revised whenever a material change to the AI system's scope, data inputs, algorithmic approach, or deployment environment is proposed. Requalification scope must be assessed for every approved change in accordance with GIT-SOP-00001.

  6.3 Ethical Review and Responsible AI Principles Evaluation

  All AI systems, regardless of risk classification, must undergo an Ethical Review prior to development or deployment. The Ethical Review ensures that AI systems are designed and operated in a manner consistent with the organisation's Responsible AI Principles, applicable human rights obligations, and relevant regulatory guidance including the EU AI Act where applicable.

    6.3.1 The AI Governance Lead must convene an Ethical Review Panel comprising representatives from Legal, Privacy, Compliance, the requesting business unit, and, for GxP-classified systems, Quality Assurance. The panel must evaluate the proposed AI system against the following Responsible AI Principles:

      6.3.1.1 Transparency: the AI system's decision-making logic must be explainable to the degree required by its risk classification and intended use.

      6.3.1.2 Fairness: the AI system must not produce outputs that systematically disadvantage individuals or groups on the basis of protected characteristics.

      6.3.1.3 Accountability: a named System Owner must be designated for every AI system, with clearly documented responsibilities for ongoing monitoring and performance review.

      6.3.1.4 Privacy and Data Minimisation: the AI system must process only the minimum personal data necessary for its intended purpose, in compliance with applicable data protection legislation and the organisation's Privacy Policy.

      6.3.1.5 Human Oversight: AI systems that produce outputs used in regulated decisions must incorporate a defined human review step before those outputs are acted upon.

      6.3.1.6 Safety and Reliability: the AI system must be designed to fail safely, with defined fallback procedures and escalation contacts documented in the system's operational runbook.

    6.3.2 The Ethical Review Panel must produce a signed Ethical Review Record documenting the evaluation findings, any conditions imposed on development or deployment, and the panel's approval or rejection decision. This record must be retained in the project file.

    6.3.3 Where the Ethical Review Panel identifies concerns that cannot be resolved through design controls or operational safeguards, the AI use case must be escalated to the Chief Compliance Officer and, where patient safety is implicated, to the Head of Quality Assurance for a final determination on whether to proceed.

    6.3.4 Ethical Review outcomes must be revisited whenever the AI system's intended use, target population, or data processing scope changes materially. The AI Governance Lead must initiate a supplementary Ethical Review in such circumstances, and the outcome must be documented as an addendum to the original Ethical Review Record.

  6.4 Data Governance and Quality Requirements for AI Systems

  All data used in the training, validation, testing, and ongoing operation of AI systems must meet the data governance and quality standards defined in this section. Compliance with Data Integrity Policy GLBL-POL-00007 is mandatory for all electronic records, including AI-generated outputs, in accordance with 21 CFR Part 11 and EU GMP Annex 11.

    6.4.1 The System Owner must ensure that a Data Governance Plan is produced for every AI system prior to the commencement of model development. The plan must document data sources, data lineage, data quality acceptance criteria, data access controls, and the process for managing data changes throughout the AI system lifecycle.

    6.4.2 All training, validation, and test datasets must be subject to documented data quality checks that verify completeness, accuracy, consistency, and representativeness. Data quality check results must be recorded and retained in the project file.

    6.4.3 Data used in GxP-classified AI systems must satisfy the ALCOA+ principles (Attributable, Legible, Contemporaneous, Original, Accurate, plus Complete, Consistent, Enduring, and Available) as required by GLBL-POL-00007.

      6.4.3.1 Electronic audit trails must be enabled for all data transformations applied to GxP training or operational datasets. Audit trail records must be protected from unauthorised modification and must be retained for the period specified in GLBL-POL-00078.

    6.4.4 Access to AI training data, model artefacts, and AI-generated outputs must be controlled through role-based access management. Annual account access reviews must be conducted for all qualified AI systems in accordance with the organisation's access management policy.

    6.4.5 Data used in AI systems must not be transferred, retained beyond its authorised retention period, or disposed of without compliance with GLBL-POL-00078 (Retention, Transfer or Disposal of GxP Regulated Materials) and GLBL-POL-00050 (Secure Destruction of Confidential Documents).

    6.4.6 Where AI systems ingest real-time or near-real-time operational data, a data monitoring procedure must be established to detect data drift, schema changes, or quality degradation. Detected anomalies must be logged, assessed for impact on model performance and data integrity, and escalated to the System Owner and Quality Assurance as appropriate.

  6.5 AI Model Development Standards and Controls

  AI model development must follow a structured Software Development Lifecycle (SDLC) that incorporates the controls required by GAMP 5 (Second Edition, 2022) for GxP-classified systems and applicable best practices for all other AI systems. A formal Development Plan must be produced for every GxP AI system as a mandatory SDLC document.

    6.5.1 The Development Plan must define the development methodology, technology stack, model architecture selection rationale, version control strategy, peer review requirements, testing approach, and acceptance criteria. The plan must be approved by dated signature from the System Owner and Quality Assurance representative before development commences.

    6.5.2 All model development artefacts, including source code, configuration files, training scripts, hyperparameter settings, and model weights, must be stored in a version-controlled repository. Commit history must be preserved and must not be altered or deleted.

    6.5.3 Peer review must be documented for all GxP AI systems during the design and build phases. Peer review records must capture the reviewer's identity, the artefacts reviewed, the review date, findings raised, and the disposition of each finding. Peer review records must be retained in the project file.

    6.5.4 Model hyperparameters, architecture decisions, and training configurations must be documented in a Baseline Configuration Document. This document must be approved by dated signature before model training commences in the validation or production environment.

    6.5.5 All changes to model code, configuration, or training data after the Baseline Configuration Document has been approved must be processed through the formal change control process defined in GIT-SOP-00001. Unauthorised modifications to baseline artefacts are prohibited.

    6.5.6 Technical work instructions must be developed for commonly repeated AI system administration tasks, including model monitoring, capacity management, retraining procedures, and lifecycle management activities. These work instructions must be version-controlled and subject to the same document approval requirements as this SOP.

    6.5.7 Physical and cybersecurity controls must be applied throughout the development environment. Developers must observe electrostatic discharge (ESD) precautions when working with hardware components, adhere to hot and cold aisle access protocols in data centre environments, and follow electrical hazard awareness procedures. Cybersecurity incident response procedures must be documented and must include detection, containment, and escalation steps with named emergency contacts. Emergency shutdown procedures and escalation contacts must be maintained in the system's operational runbook and reviewed annually.

  6.6 GxP Validation and Qualification of AI Systems

  All AI systems classified as GxP must undergo formal Computer System Validation (CSV) in accordance with GAMP 5 (Second Edition, 2022), 21 CFR Part 11, and EU GMP Annex 11 before being placed into operational use in a regulated environment. The validation lifecycle must be documented, executed, and approved in accordance with the requirements of this section.

    6.6.1 A Validation Master Plan or system-level Validation Plan must be produced for each GxP AI system. The plan must define the validation strategy, scope, roles and responsibilities, deliverables, acceptance criteria, and the approach to managing deviations identified during testing.

    6.6.2 The following qualification documents must be produced, approved by dated signature, and placed under document control before testing commences: Installation Qualification Protocol (IQP), As-Built Document, Test Scripts, Baseline Configuration Document, and Installation Qualification Report (IQR). No testing activity may commence until all required qualification documents carry the required approvals.

    6.6.3 Operational Qualification (OQ) and Performance Qualification (PQ) activities must be executed in accordance with approved test scripts. Test execution must be performed by trained personnel, and all test results, including pass, fail, and deviation records, must be documented contemporaneously in accordance with GLBL-POL-00007.

    6.6.4 Deviations identified during qualification testing must be classified as Critical, Major, or Minor. Critical and Major deviations must be resolved and their resolution verified before the qualification phase is closed. All deviations must be documented in a Deviation Report containing a root cause analysis, impact assessment, and corrective action plan. Quality Assurance must review and approve all Deviation Reports.

    6.6.5 Upon successful completion of all qualification phases, a Validation Summary Report must be produced and approved by dated signature from the System Owner and Quality Assurance representative. The report must confirm that the AI system meets its predefined acceptance criteria and is suitable for its intended use in the regulated environment.

    6.6.6 A CMDB entry must be created for every AI system accepted into the qualified environment. The CMDB entry must reference the Validation Summary Report, Baseline Configuration Document, and all associated qualification records.

    6.6.7 Requalification must be triggered whenever a change is made to the qualified AI system's infrastructure, model, configuration, or operational environment. The requalification scope must be assessed and documented as part of the change control process in accordance with GIT-SOP-00001. Annual account access reviews must be conducted for all qualified AI systems.

  6.7 Bias Detection, Fairness Testing, and Explainability Review

  All AI systems must undergo bias detection, fairness testing, and explainability review as part of the pre-deployment qualification process and at defined intervals throughout the operational lifecycle. For GxP-classified systems, these activities must be documented and approved in accordance with the CSV requirements of GAMP 5 (Second Edition, 2022) and 21 CFR Part 11.

    6.7.1 The AI Developer must execute a documented Bias Detection Assessment against the model's training and validation datasets prior to deployment. The assessment must evaluate the distribution of outcomes across relevant demographic and operational subgroups and must record any statistically significant disparities identified.

    6.7.2 Fairness testing must be conducted using pre-defined fairness metrics that are appropriate to the AI system's intended use and risk classification. Acceptance thresholds for fairness metrics must be documented in the Validation Plan and approved by Quality Assurance before testing commences.

    6.7.3 Where fairness testing identifies bias that exceeds the defined acceptance thresholds, the finding must be classified as a deviation in accordance with section 6.2.4, and a Deviation Report must be raised. Development must not proceed to the next lifecycle phase until the deviation has been resolved and approved by Quality Assurance.

    6.7.4 An Explainability Review must be conducted for every AI system prior to deployment. The review must assess whether the AI system's outputs can be explained to the degree required by its risk classification, intended use, and applicable regulatory requirements. For AI systems that produce outputs used in GxP-regulated decisions, the explainability approach must be documented in the Validation Summary Report.

    6.7.5 For AI systems classified as Critical or High risk, the Explainability Review must include a demonstration that subject matter experts and end users can interpret model outputs sufficiently to exercise meaningful human oversight, consistent with the Human Oversight principle defined in section 6.3.1.5.

    6.7.6 Bias detection and fairness testing must be repeated following any model retraining, significant data change, or change to the AI system's operational scope. Results must be documented and retained in the project file. Requalification scope must be assessed for every such change in accordance with GIT-SOP-00001.

    6.7.7 All Bias Detection Assessment records, Fairness Testing records, and Explainability Review records must be retained in accordance with GLBL-POL-00078 and must be available for inspection by Quality Assurance and regulatory authorities upon request.

6.0 PROCEDURE

This section defines the mandatory procedural requirements governing the responsible identification, assessment, development, validation, and deployment of Artificial Intelligence systems within the Global Technology organisation. All personnel executing activities described herein must have completed role-specific training prior to performing any qualification or AI lifecycle activity, and training records must be maintained in accordance with applicable GxP requirements. All AI systems that support or interact with GxP-regulated processes must comply with Computer System Validation (CSV) requirements, Data Integrity Policy GLBL-POL-00007, and applicable change management controls as defined in GIT-SOP-00001. This SOP is subject to controlled document management; approval signatures, whether wet or electronic, must comply with 21 CFR Part 11. Every page of this document must carry a header displaying the document title, document ID, revision number, effective date, and page x of y notation, together with a CURRENT, Confidential and Proprietary footer.

  6.1 AI Use Case Identification and Intake

  All proposed AI use cases must be formally identified, documented, and submitted through the AI Intake process before any development, procurement, or deployment activity commences. This process ensures that AI initiatives are aligned with organisational strategy, regulatory obligations, and responsible AI principles prior to resource commitment.

    6.1.1 The requesting business unit or technology team must complete an AI Use Case Intake Form, capturing the intended purpose, target user population, data inputs and outputs, system dependencies, and anticipated business benefit of the proposed AI system.

    6.1.2 The intake submission must identify whether the proposed AI system will interact with, support, or produce outputs consumed by GxP-regulated processes, SOX-applicable applications such as SAP, or other controlled environments. This determination governs the applicable validation and compliance pathway.

    6.1.3 The AI Governance Lead or designated intake reviewer must assess each submission within ten business days of receipt and assign a preliminary classification of GxP, non-GxP regulated, or non-regulated to guide subsequent risk and ethical review activities.

    6.1.4 A project file must be established for every approved AI development or procurement initiative. This file must contain all applicable formal documentation and must be maintained in a location readily available for inspection by Quality Assurance and regulatory authorities.

    6.1.5 Any AI system sourced from an external vendor must not proceed beyond the intake stage until vendor approval has been obtained in accordance with the Global Vendor Program. Vendor qualification records must be retained within the project file.

    6.1.6 Approved intake records must be stored in the controlled document management system and referenced in the Configuration Management Database (CMDB) entry established for the AI system upon acceptance into the qualified environment.

  6.2 AI Risk Classification and Impact Assessment

  Every AI system that has passed the intake stage must undergo a formal risk classification and impact assessment before design or procurement activities proceed. The risk classification must follow a risk-based approach consistent with GAMP 5 (Second Edition, 2022) principles, whereby the level of documentation, testing rigour, and oversight is proportionate to the perceived size, impact, risk, complexity, and novelty of the system.

    6.2.1 The responsible AI Developer or System Owner must complete a Risk Classification Record that assigns the AI system to one of the following tiers: Critical (direct patient safety, product quality, or data integrity impact), High (indirect GxP impact or significant SOX financial reporting relevance), Medium (operational impact with limited regulatory exposure), or Low (administrative or analytical tools with no regulated output).

    6.2.2 The impact assessment must evaluate the following dimensions at minimum: patient safety and product quality risk, data integrity risk as defined under GLBL-POL-00007, cybersecurity and information security risk consistent with ISO/IEC 27001:2022, operational continuity risk, and regulatory inspection risk.

    6.2.3 For AI systems classified as Critical or High, a formal Risk Assessment Report must be authored, peer-reviewed, and approved by dated signature from the System Owner and Quality Assurance representative before design activities commence.

    6.2.4 Deviation classification thresholds must be established within the Risk Assessment Report. Deviations identified during any subsequent lifecycle phase must be classified as Critical, Major, or Minor based on their potential impact on patient safety, data integrity, or regulatory compliance. All deviations must be documented in a Deviation Report that includes a root cause analysis, impact assessment, and corrective action. Quality Assurance must review and approve all deviation records before the affected activity proceeds.

    6.2.5 The Risk Classification Record and Risk Assessment Report must be retained in the project file and referenced in the CMDB entry for the AI system. These records are subject to the retention requirements of GLBL-POL-00078 governing Retention, Transfer or Disposal of GxP Regulated Materials.

    6.2.6 Risk classification must be reviewed and, where necessary, revised whenever a material change to the AI system's scope, data inputs, algorithmic approach, or deployment environment is proposed. Requalification scope must be assessed for every approved change in accordance with GIT-SOP-00001.

  6.3 Ethical Review and Responsible AI Principles Evaluation

  All AI systems, regardless of risk classification, must undergo an Ethical Review prior to development or deployment. The Ethical Review ensures that AI systems are designed and operated in a manner consistent with the organisation's Responsible AI Principles, applicable human rights obligations, and relevant regulatory guidance including the EU AI Act where applicable.

    6.3.1 The AI Governance Lead must convene an Ethical Review Panel comprising representatives from Legal, Privacy, Compliance, the requesting business unit, and, for GxP-classified systems, Quality Assurance. The panel must evaluate the proposed AI system against the following Responsible AI Principles:

      6.3.1.1 Transparency: the AI system's decision-making logic must be explainable to the degree required by its risk classification and intended use.

      6.3.1.2 Fairness: the AI system must not produce outputs that systematically disadvantage individuals or groups on the basis of protected characteristics.

      6.3.1.3 Accountability: a named System Owner must be designated for every AI system, with clearly documented responsibilities for ongoing monitoring and performance review.

      6.3.1.4 Privacy and Data Minimisation: the AI system must process only the minimum personal data necessary for its intended purpose, in compliance with applicable data protection legislation and the organisation's Privacy Policy.

      6.3.1.5 Human Oversight: AI systems that produce outputs used in regulated decisions must incorporate a defined human review step before those outputs are acted upon.

      6.3.1.6 Safety and Reliability: the AI system must be designed to fail safely, with defined fallback procedures and escalation contacts documented in the system's operational runbook.

    6.3.2 The Ethical Review Panel must produce a signed Ethical Review Record documenting the evaluation findings, any conditions imposed on development or deployment, and the panel's approval or rejection decision. This record must be retained in the project file.

    6.3.3 Where the Ethical Review Panel identifies concerns that cannot be resolved through design controls or operational safeguards, the AI use case must be escalated to the Chief Compliance Officer and, where patient safety is implicated, to the Head of Quality Assurance for a final determination on whether to proceed.

    6.3.4 Ethical Review outcomes must be revisited whenever the AI system's intended use, target population, or data processing scope changes materially. The AI Governance Lead must initiate a supplementary Ethical Review in such circumstances, and the outcome must be documented as an addendum to the original Ethical Review Record.

  6.4 Data Governance and Quality Requirements for AI Systems

  All data used in the training, validation, testing, and ongoing operation of AI systems must meet the data governance and quality standards defined in this section. Compliance with Data Integrity Policy GLBL-POL-00007 is mandatory for all electronic records, including AI-generated outputs, in accordance with 21 CFR Part 11 and EU GMP Annex 11.

    6.4.1 The System Owner must ensure that a Data Governance Plan is produced for every AI system prior to the commencement of model development. The plan must document data sources, data lineage, data quality acceptance criteria, data access controls, and the process for managing data changes throughout the AI system lifecycle.

    6.4.2 All training, validation, and test datasets must be subject to documented data quality checks that verify completeness, accuracy, consistency, and representativeness. Data quality check results must be recorded and retained in the project file.

    6.4.3 Data used in GxP-classified AI systems must satisfy the ALCOA+ principles (Attributable, Legible, Contemporaneous, Original, Accurate, plus Complete, Consistent, Enduring, and Available) as required by GLBL-POL-00007.

      6.4.3.1 Electronic audit trails must be enabled for all data transformations applied to GxP training or operational datasets. Audit trail records must be protected from unauthorised modification and must be retained for the period specified in GLBL-POL-00078.

    6.4.4 Access to AI training data, model artefacts, and AI-generated outputs must be controlled through role-based access management. Annual account access reviews must be conducted for all qualified AI systems in accordance with the organisation's access management policy.

    6.4.5 Data used in AI systems must not be transferred, retained beyond its authorised retention period, or disposed of without compliance with GLBL-POL-00078 (Retention, Transfer or Disposal of GxP Regulated Materials) and GLBL-POL-00050 (Secure Destruction of Confidential Documents).

    6.4.6 Where AI systems ingest real-time or near-real-time operational data, a data monitoring procedure must be established to detect data drift, schema changes, or quality degradation. Detected anomalies must be logged, assessed for impact on model performance and data integrity, and escalated to the System Owner and Quality Assurance as appropriate.

  6.5 AI Model Development Standards and Controls

  AI model development must follow a structured Software Development Lifecycle (SDLC) that incorporates the controls required by GAMP 5 (Second Edition, 2022) for GxP-classified systems and applicable best practices for all other AI systems. A formal Development Plan must be produced for every GxP AI system as a mandatory SDLC document.

    6.5.1 The Development Plan must define the development methodology, technology stack, model architecture selection rationale, version control strategy, peer review requirements, testing approach, and acceptance criteria. The plan must be approved by dated signature from the System Owner and Quality Assurance representative before development commences.

    6.5.2 All model development artefacts, including source code, configuration files, training scripts, hyperparameter settings, and model weights, must be stored in a version-controlled repository. Commit history must be preserved and must not be altered or deleted.

    6.5.3 Peer review must be documented for all GxP AI systems during the design and build phases. Peer review records must capture the reviewer's identity, the artefacts reviewed, the review date, findings raised, and the disposition of each finding. Peer review records must be retained in the project file.

    6.5.4 Model hyperparameters, architecture decisions, and training configurations must be documented in a Baseline Configuration Document. This document must be approved by dated signature before model training commences in the validation or production environment.

    6.5.5 All changes to model code, configuration, or training data after the Baseline Configuration Document has been approved must be processed through the formal change control process defined in GIT-SOP-00001. Unauthorised modifications to baseline artefacts are prohibited.

    6.5.6 Technical work instructions must be developed for commonly repeated AI system administration tasks, including model monitoring, capacity management, retraining procedures, and lifecycle management activities. These work instructions must be version-controlled and subject to the same document approval requirements as this SOP.

    6.5.7 Physical and cybersecurity controls must be applied throughout the development environment. Developers must observe electrostatic discharge (ESD) precautions when working with hardware components, adhere to hot and cold aisle access protocols in data centre environments, and follow electrical hazard awareness procedures. Cybersecurity incident response procedures must be documented and must include detection, containment, and escalation steps with named emergency contacts. Emergency shutdown procedures and escalation contacts must be maintained in the system's operational runbook and reviewed annually.

  6.6 GxP Validation and Qualification of AI Systems

  All AI systems classified as GxP must undergo formal Computer System Validation (CSV) in accordance with GAMP 5 (Second Edition, 2022), 21 CFR Part 11, and EU GMP Annex 11 before being placed into operational use in a regulated environment. The validation lifecycle must be documented, executed, and approved in accordance with the requirements of this section.

    6.6.1 A Validation Master Plan or system-level Validation Plan must be produced for each GxP AI system. The plan must define the validation strategy, scope, roles and responsibilities, deliverables, acceptance criteria, and the approach to managing deviations identified during testing.

    6.6.2 The following qualification documents must be produced, approved by dated signature, and placed under document control before testing commences: Installation Qualification Protocol (IQP), As-Built Document, Test Scripts, Baseline Configuration Document, and Installation Qualification Report (IQR). No testing activity may commence until all required qualification documents carry the required approvals.

    6.6.3 Operational Qualification (OQ) and Performance Qualification (PQ) activities must be executed in accordance with approved test scripts. Test execution must be performed by trained personnel, and all test results, including pass, fail, and deviation records, must be documented contemporaneously in accordance with GLBL-POL-00007.

    6.6.4 Deviations identified during qualification testing must be classified as Critical, Major, or Minor. Critical and Major deviations must be resolved and their resolution verified before the qualification phase is closed. All deviations must be documented in a Deviation Report containing a root cause analysis, impact assessment, and corrective action plan. Quality Assurance must review and approve all Deviation Reports.

    6.6.5 Upon successful completion of all qualification phases, a Validation Summary Report must be produced and approved by dated signature from the System Owner and Quality Assurance representative. The report must confirm that the AI system meets its predefined acceptance criteria and is suitable for its intended use in the regulated environment.

    6.6.6 A CMDB entry must be created for every AI system accepted into the qualified environment. The CMDB entry must reference the Validation Summary Report, Baseline Configuration Document, and all associated qualification records.

    6.6.7 Requalification must be triggered whenever a change is made to the qualified AI system's infrastructure, model, configuration, or operational environment. The requalification scope must be assessed and documented as part of the change control process in accordance with GIT-SOP-00001. Annual account access reviews must be conducted for all qualified AI systems.

  6.7 Bias Detection, Fairness Testing, and Explainability Review

  All AI systems must undergo bias detection, fairness testing, and explainability review as part of the pre-deployment qualification process and at defined intervals throughout the operational lifecycle. For GxP-classified systems, these activities must be documented and approved in accordance with the CSV requirements of GAMP 5 (Second Edition, 2022) and 21 CFR Part 11.

    6.7.1 The AI Developer must execute a documented Bias Detection Assessment against the model's training and validation datasets prior to deployment. The assessment must evaluate the distribution of outcomes across relevant demographic and operational subgroups and must record any statistically significant disparities identified.

    6.7.2 Fairness testing must be conducted using pre-defined fairness metrics that are appropriate to the AI system's intended use and risk classification. Acceptance thresholds for fairness metrics must be documented in the Validation Plan and approved by Quality Assurance before testing commences.

    6.7.3 Where fairness testing identifies bias that exceeds the defined acceptance thresholds, the finding must be classified as a deviation in accordance with section 6.2.4, and a Deviation Report must be raised. Development must not proceed to the next lifecycle phase until the deviation has been resolved and approved by Quality Assurance.

    6.7.4 An Explainability Review must be conducted for every AI system prior to deployment. The review must assess whether the AI system's outputs can be explained to the degree required by its risk classification, intended use, and applicable regulatory requirements. For AI systems that produce outputs used in GxP-regulated decisions, the explainability approach must be documented in the Validation Summary Report.

    6.7.5 For AI systems classified as Critical or High risk, the Explainability Review must include a demonstration that subject matter experts and end users can interpret model outputs sufficiently to exercise meaningful human oversight, consistent with the Human Oversight principle defined in section 6.3.1.5.

    6.7.6 Bias detection and fairness testing must be repeated following any model retraining, significant data change, or change to the AI system's operational scope. Results must be documented and retained in the project file. Requalification scope must be assessed for every such change in accordance with GIT-SOP-00001.

    6.7.7 All Bias Detection Assessment records, Fairness Testing records, and Explainability Review records must be retained in accordance with GLBL-POL-00078 and must be available for inspection by Quality Assurance and regulatory authorities upon request.

  6.8 Cybersecurity and Cloud Infrastructure Controls for AI

  All AI systems hosted on cloud or on-premises infrastructure must be secured in accordance with ISO/IEC 27001:2022 and organisational data integrity policy GLBL-POL-00007. Access to AI infrastructure must be restricted to authorised personnel only, with role-based access controls enforced and reviewed annually per the qualified system account access review requirement. Personnel working within physical data centre environments must observe ESD precautions, adhere to hot/cold aisle access protocols, follow rack safety procedures, and maintain electrical hazard awareness at all times. Cybersecurity incident response must follow a defined sequence of detection, containment, and escalation. Upon detection of a security event, the responsible engineer must isolate the affected system, notify the Information Security team, and escalate to the AI System Owner and QA within two hours. Emergency shutdown procedures and escalation contact lists must be maintained within the project file and reviewed annually.

  6.9 Change Control and Configuration Management for AI Models

  All changes to qualified AI systems, including model updates, hyperparameter modifications, infrastructure changes, and integration amendments, must be submitted through the formal change management process defined in GIT-SOP-00001 before implementation. A requalification scope assessment must be completed for every approved change to determine whether full or partial requalification is required. A Configuration Management Database (CMDB) entry must be maintained for all qualified AI systems and infrastructure components from the point of acceptance. Baseline configuration documents must be version-controlled, approved by dated signature, and stored within the project file. No change may be deployed to a qualified AI system without documented QA review and approval.

  6.10 AI System Monitoring, Performance Tracking, and Drift Detection

  Qualified AI systems must be subject to continuous monitoring of performance metrics, including accuracy, precision, recall, and latency, against approved baseline thresholds. Technical work instructions must be developed and maintained for routine monitoring, capacity management, and lifecycle management tasks. Model drift must be assessed at defined intervals or upon trigger events such as data distribution changes or significant performance degradation. Monitoring results must be recorded as electronic records in compliance with GLBL-POL-00007 and retained in accordance with GLBL-POL-00078. Where drift exceeds defined thresholds, the AI System Owner must initiate a formal deviation or requalification process as appropriate.

  6.11 Incident Management and Deviation Handling for AI Systems

  All incidents and deviations involving qualified AI systems must be classified as critical, major, or minor based on patient safety impact, data integrity risk, and regulatory exposure. A formal deviation report must be raised for every classified deviation, documenting the event description, root cause analysis, and immediate containment actions. An impact assessment must be completed and approved before the affected system is returned to operational use. QA must review and approve all deviation reports prior to closure. Critical deviations must be escalated to the AI Governance Committee and relevant regulatory affairs stakeholders within 24 hours of identification, consistent with EU GMP Annex 11 requirements.

  6.12 Audit Trail, Documentation, and Record Retention

  All AI systems processing GxP-relevant data must maintain a complete, attributable, legible, contemporaneous, original, and accurate (ALCOA+) audit trail in accordance with 21 CFR Part 11 and GLBL-POL-00007. Audit trail records must capture user identity, timestamp, action performed, and system state. All qualification documents, including the IQP, As Built Document, Test Scripts, Baseline Configuration Documents, and IQR, must be approved by dated signature before testing commences and retained within the project file. Retention, transfer, and disposal of GxP-regulated records must comply with GLBL-POL-00078. Secure destruction of confidential documents must comply with GLBL-POL-00050.

  6.13 Training and Competency Requirements for AI Practitioners

  All personnel involved in the development, validation, operation, or oversight of qualified AI systems must complete role-specific training before executing any qualification or operational activity. Training must cover applicable GxP requirements, this SOP, relevant technical work instructions, and system-specific procedures. Training records must be maintained per GxP requirements and made available for inspection upon request. The AI System Owner is responsible for ensuring that training curricula remain current and reflect any changes to system configuration or regulatory guidance.

  6.14 Decommissioning and Retirement of AI Systems

  The retirement of a qualified AI system must be initiated through the formal change management process per GIT-SOP-00001. A decommissioning plan must be prepared, reviewed by QA, and approved before any system shutdown activity commences. All GxP-relevant records and audit trails must be archived in a retrievable format for the retention period specified under GLBL-POL-00078 prior to system removal. Data destruction must comply with GLBL-POL-00050. The CMDB entry for the decommissioned system must be updated to reflect retired status upon completion. A final decommissioning report must be signed, dated, and retained within the project file.

7.0 REFERENCES

The following references govern the requirements, standards, and internal policies applicable to this Standard Operating Procedure for Responsible AI Use in Global Technology. All personnel responsible for implementing, operating, or overseeing AI systems in life sciences and regulated IT environments must consult and comply with the documents listed below.

  7.1 Regulatory and Industry Guidance

    7.1.1 21 CFR Part 11 — Electronic Records; Electronic Signatures (U.S. Food and Drug Administration): governs the use of electronic records and electronic signatures for GxP-regulated systems, including AI-generated outputs and audit trail requirements.

    7.1.2 21 CFR Part 820 — Quality System Regulation (U.S. Food and Drug Administration): establishes quality system requirements applicable to software and AI tools used in the design, manufacture, and distribution of medical devices.

    7.1.3 EU GMP Annex 11 — Computerised Systems (European Medicines Agency): defines requirements for the validation, operation, and control of computerised systems, including AI-driven systems, used in GxP-regulated environments.

    7.1.4 EU AI Act (Regulation (EU) 2024/1689): establishes a risk-based regulatory framework for artificial intelligence systems deployed within the European Union, including requirements for high-risk AI applications in life sciences.

    7.1.5 GAMP 5 (Second Edition, 2022) — A Risk-Based Approach to Compliant GxP Computerised Systems (ISPE): provides industry guidance on the application of risk-based approaches to the validation and lifecycle management of GxP computerised systems, including AI and machine learning systems.

    7.1.6 FDA Guidance for Industry — Artificial Intelligence and Machine Learning in Software as a Medical Device (SaMD): provides regulatory expectations for the development, validation, and post-market monitoring of AI/ML-based software used in medical device applications.

    7.1.7 Sarbanes-Oxley Act (SOX) — Sections 302 and 404: establishes internal control and financial reporting requirements applicable to systems such as SAP that support financial data processing and reporting.

    7.1.8 ICH Q10 — Pharmaceutical Quality System: defines the pharmaceutical quality system model applicable across the product lifecycle, including the management of computerised systems and AI tools supporting GxP operations.

  7.2 Internal Policies and SOPs

    7.2.1 GIT-SOP-00001 — Change Management SOP: governs the formal change control process that must be followed for all modifications to qualified systems, including AI systems and supporting infrastructure, consistent with requalification assessment requirements.

    7.2.2 GLBL-POL-00007 — Data Integrity Policy: mandates data integrity controls for all electronic records, including AI-generated outputs, to ensure records are attributable, legible, contemporaneous, original, and accurate (ALCOA+).

    7.2.3 GLBL-POL-00078 — Retention, Transfer or Disposal of GxP Regulated Materials Policy: defines requirements for the retention, transfer, and disposal of GxP-regulated records and materials, including those produced or managed by AI systems.

    7.2.4 GLBL-POL-00050 — Secure Destruction of Confidential Documents Policy: establishes requirements for the secure destruction of confidential documents and data, applicable to AI system outputs and associated records at end of retention.

    7.2.5 Global Vendor Program SOP: requires formal vendor approval prior to the procurement or use of any AI tool, platform, or service in regulated operations, including assessment of vendor qualification and supply chain risk.

    7.2.6 Computer System Validation (CSV) SOP: defines the validation lifecycle requirements for GxP computerised systems, including AI-driven systems, encompassing Development Plan, peer review, qualification documentation, and SDLC controls.

    7.2.7 Access Management and Annual Account Review SOP: mandates annual account access reviews for all qualified systems, including AI platforms, to ensure access rights remain appropriate and are documented in accordance with GxP requirements.

    7.2.8 Configuration Management and CMDB SOP: requires that a Configuration Management Database (CMDB) entry be established and maintained for all qualified AI systems and infrastructure components upon acceptance into the production environment.

  7.3 Standards and Frameworks (ISO, NIST, IEEE)

    7.3.1 ISO/IEC 42001:2023 — Artificial Intelligence Management System: specifies requirements for establishing, implementing, maintaining, and continually improving an AI management system within organisations developing or using AI systems in regulated contexts.

    7.3.2 ISO/IEC 27001:2022 — Information Security Management Systems: defines requirements for the establishment and operation of an information security management system, applicable to AI platforms, data pipelines, and supporting cloud infrastructure.

    7.3.3 ISO/IEC 27701:2019 — Privacy Information Management: extends ISO/IEC 27001 to address privacy requirements for personally identifiable information (PII) processed by AI systems, including data used for model training and inference.

    7.3.4 ISO 9001:2015 — Quality Management Systems: establishes quality management principles applicable to the development, deployment, and continuous improvement of AI systems used in life sciences operations.

    7.3.5 NIST AI Risk Management Framework (AI RMF 1.0, 2023): provides a structured approach to identifying, assessing, and managing risks associated with AI systems across their full lifecycle, including governance, mapping, measurement, and management functions.

    7.3.6 NIST Special Publication 800-53 (Revision 5) — Security and Privacy Controls for Information Systems and Organisations: defines security and privacy controls applicable to AI systems and supporting IT infrastructure operating in regulated environments.

    7.3.7 NIST Special Publication 800-37 (Revision 2) — Risk Management Framework for Information Systems and Organisations: establishes a risk management framework for the categorisation, selection, implementation, and assessment of security controls for AI and IT systems.

    7.3.8 IEEE 7000-2021 — Model Process for Addressing Ethical Concerns During System Design: provides a process framework for embedding ethical considerations, including transparency, fairness, and accountability, into the design and deployment of AI systems.

    7.3.9 IEEE 7010-2020 — Recommended Practice for Assessing the Impact of Autonomous and Intelligent Systems on Human Well-Being: establishes recommended practices for evaluating the societal and human impact of AI systems deployed in regulated and public-facing contexts.

8.0 REVISION HISTORY

| Revision | Effective Date | Reason for Revision |
|----------|---------------|---------------------|
| 1.0 | 2025-01-01 | Initial release of the Standard Operating Procedure for Responsible AI Use in Global Technology. Establishes governance, qualification, change control, data integrity, and vendor approval requirements for AI systems used in GxP-aligned and regulated IT environments, consistent with 21 CFR Part 11, GAMP 5 (Second Edition, 2022), EU GMP Annex 11, ISO/IEC 27001:2022, and applicable internal policies including GLBL-POL-00007, GLBL-POL-00078, GLBL-POL-00050, and GIT-SOP-00001. |

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