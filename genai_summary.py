import os
import pandas as pd
from google import genai
from google.genai import types

# =========================================================
# 1) CONFIG
# =========================================================
# Option 1: set env var before running:
# export GEMINI_API_KEY="your_key_here"   (Mac/Linux)
# set GEMINI_API_KEY=your_key_here        (Windows CMD)
# $env:GEMINI_API_KEY="your_key_here"     (PowerShell)         
               
# Option 2: hardcode temporarily (not recommended for long term)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "YOUR_GEMINI_API_KEY"

# Folder where your exported SAS Excel files are saved
BASE_FOLDER = r"C:\Users\vachippa\Desktop\SAS_Projects\Churn_rate_analysis"
# Example Linux path:
# BASE_FOLDER = "/home/yourname/Churn_rate_analysis"

PROJECT_SUMMARY_FILE = os.path.join(BASE_FOLDER, "project_summary.xlsx")
HIGH_RISK_FILE = os.path.join(BASE_FOLDER, "high_risk_actions.xlsx")

OUTPUT_FILE = os.path.join(BASE_FOLDER, "executive_summary_gemini.txt")

# =========================================================
# 2) READ SAS OUTPUTS
# =========================================================
summary_df = pd.read_excel(PROJECT_SUMMARY_FILE)
high_risk_df = pd.read_excel(HIGH_RISK_FILE)

total_customers = int(summary_df.loc[0, "total_customers"])
churned_customers = int(summary_df.loc[0, "churned_customers"])
churn_rate = float(summary_df.loc[0, "churn_rate"])
high_risk_customers = int(summary_df.loc[0, "high_risk_customers"])
very_high_risk_customers = int(summary_df.loc[0, "very_high_risk_customers"])

# Top risky customers for richer context
top10 = high_risk_df.sort_values(by="risk_score", ascending=False).head(10)

customer_lines = []
for _, row in top10.iterrows():
    customer_lines.append(
        f"CustomerID={row['customerID']}, "
        f"RiskBand={row['risk_band']}, "
        f"RiskScore={row['risk_score']}, "
        f"Contract={row['Contract']}, "
        f"MonthlyCharges={row['MonthlyCharges']}, "
        f"PaymentMethod={row['PaymentMethod']}, "
        f"InternetService={row['InternetService']}, "
        f"TechSupport={row['TechSupport']}, "
        f"Priority={row['priority']}, "
        f"RecommendedAction={row['recommended_action']}, "
        f"ActualChurn={row['Churn']}"
    )

top_customers_text = "\n".join(customer_lines)

# =========================================================
# 3) CREATE THE GEMINI CLIENT
# =========================================================
client = genai.Client(api_key=GEMINI_API_KEY)

# =========================================================
# 4) BUILD THE REQUEST
# =========================================================
system_instruction = """
You are a business analytics assistant.
Write a presentation-ready customer churn analysis summary.

Your output must contain:
1. Executive Summary
2. Key Findings
3. 3 Retention Recommendations
4. A short concluding business impact statement

Guidelines:
- Be concise but insightful.
- Use professional business language.
- Mention the churn rate clearly.
- Highlight that month-to-month customers are a critical churn segment.
- Mention that high and very high risk customers need proactive action.
- Do not invent metrics beyond what is given.
"""

user_content = f"""
Customer churn analytics results from a SAS project:

Overall metrics:
- Total customers: {total_customers}
- Churned customers: {churned_customers}
- Churn rate: {churn_rate:.2f}%
- High-risk customers: {high_risk_customers}
- Very high-risk customers: {very_high_risk_customers}

Additional known insight from SAS:
- Month-to-month contract customers show the highest churn.

Sample high-risk customers:
{top_customers_text}

Generate the final business summary now.
"""

# =========================================================
# 5) CALL GEMINI
# =========================================================
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=user_content,
    config=types.GenerateContentConfig(
        system_instruction=system_instruction
    )
)

final_text = response.text

# =========================================================
# 6) PRINT + SAVE THE ACTUAL MODEL OUTPUT
# =========================================================
print("\n===== GEMINI GENERATED SUMMARY =====\n")
print(final_text)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(final_text)

print(f"\nSaved to: {OUTPUT_FILE}")
