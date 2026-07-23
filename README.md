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
The Agentic AI layer converts insights into 
