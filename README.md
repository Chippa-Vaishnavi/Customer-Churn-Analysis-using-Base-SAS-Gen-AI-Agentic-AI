# Customer Churn Analysis using Base SAS, Gen AI, and Agentic AI

## Overview
This project is an end-to-end Customer Churn Analysis solution that combines traditional analytics with Generative AI and Agentic AI. The objective is to identify customers at risk of churn, generate business insights, and automate retention actions through an intelligent workflow. The solution is built using Base SAS, Python, Gemini API, and Streamlit. 【1-59f253】

## Architecture

### 1. SAS Analytics Layer
The SAS layer serves as the foundation of the project and is responsible for data preparation, customer churn analysis, risk scoring, and reporting.

#### Key Activities
- Import telecom churn dataset
- Data validation and profiling
- Duplicate removal and data cleaning
- Feature engineering
- Rule-based churn risk scoring
- Customer segmentation into:
  - Low Risk
  - Medium Risk
  - High Risk
  - Very High Risk
- KPI generation and reporting
- Data export for AI processing

#### SAS Procedures Used
- PROC IMPORT
- PROC CONTENTS
- PROC PRINT
- PROC FREQ
- PROC SORT
- PROC SQL
- DATA Step
- PROC SGPLOT
- PROC EXPORT

---

### 2. Generative AI Layer
The Generative AI layer transforms analytical results into business-friendly narratives.

#### Key Features
- Reads SAS-generated Excel outputs
- Extracts churn KPIs using Pandas
- Uses Gemini API for natural language generation
- Produces:
  - Executive Summary
  - Key Findings
  - Retention Recommendations
  - Business Impact Statement
- Supports grounded Q&A based on churn analysis outputs

#### Technologies Used
- Python
- Pandas
- Gemini API
- google-genai SDK

---

### 3. Agentic AI Layer
The Agentic AI layer converts insights into actionable business workflows.

#### Key Features
- Identifies high-risk customers
- Creates automated retention queues
- Prioritizes customers into:
  - P1 (Critical)
  - P2 (High)
  - P3 (Medium)
- Assigns:
  - Owner
  - Due Date
  - Status
  - Escalation Flag
- Generates action-ready reports for retention teams

#### Technologies Used
- Python
- Pandas
- Rule-Based Workflow Engine

---

### 4. Streamlit Application Layer
An interactive web application that provides a business-friendly interface.

#### Modules
- Overview Dashboard
- KPI Visualization
- Gen AI Summary
- Churn Q&A Assistant
- Agent Queue Explorer
- Risk Analysis Reports

#### Technologies Used
- Streamlit
- Plotly
- Pandas

---

## Workflow

1. Load telecom customer data in SAS.
2. Clean, validate, and transform the data.
3. Generate churn risk scores and customer segments.
4. Export results to Excel.
5. Process churn outputs using Python.
6. Generate AI-powered summaries and recommendations using Gemini.
7. Create retention action queues through Agentic AI workflows.
8. Present insights through a Streamlit dashboard.

---

## Key Business Benefits

- Early identification of churn-prone customers
- AI-generated executive reporting
- Automated retention prioritization
- Improved decision-making
- Reduced customer attrition
- Enhanced operational efficiency

---

## Tech Stack

| Layer | Technologies |
|---------|-------------|
| Analytics | Base SAS |
| Data Processing | Python, Pandas |
| Generative AI | Gemini API |
| Agentic AI | Python Automation |
| Visualization | Plotly |
| Application | Streamlit |
| Reporting | Excel |

---

## Future Enhancements

- ML-based churn prediction models
- Real-time churn monitoring
- CRM integration
- Automated email retention campaigns
- Multi-agent orchestration
- Cloud deployment

---

## Project Outcome

This project demonstrates how traditional SAS analytics can be integrated with Generative AI and Agentic AI to create a complete customer retention decision-support system. It not only predicts churn risk but also generates business recommendations and prioritizes retention actions, making it a practical enterprise-ready solution.
