import os
import pandas as pd
from datetime import datetime, timedelta

# Optional Gemini imports
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# =========================================================
# 1) CONFIGURATION
# =========================================================
BASE_FOLDER = r"C:\Users\vachippa\Desktop\SAS_Projects\Churn_rate_analysis"
INPUT_FILE = os.path.join(BASE_FOLDER, "high_risk_actions.xlsx")

OUTPUT_FOLDER = os.path.join(BASE_FOLDER, "agent_outputs")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

MASTER_OUTPUT = os.path.join(OUTPUT_FOLDER, "agent_action_master.xlsx")
P1_OUTPUT = os.path.join(OUTPUT_FOLDER, "p1_queue.xlsx")
P2_OUTPUT = os.path.join(OUTPUT_FOLDER, "p2_queue.xlsx")
P3_OUTPUT = os.path.join(OUTPUT_FOLDER, "p3_queue.xlsx")
SUMMARY_TXT = os.path.join(OUTPUT_FOLDER, "agent_summary.txt")
GEMINI_REPORT_TXT = os.path.join(OUTPUT_FOLDER, "gemini_agent_report.txt")

TODAY = datetime.today().date()

# Set this True if you want Gemini-generated report
USE_GEMINI = True

# If needed, you can hardcode temporarily
# GEMINI_API_KEY = "YOUR_REAL_GEMINI_KEY"
# Otherwise it will pick from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# =========================================================
# 2) READ INPUT
# =========================================================
df = pd.read_excel(INPUT_FILE, engine="openpyxl")

print("Input file loaded successfully.")
print("Rows:", len(df))
print("Columns:", list(df.columns))

# =========================================================
# 3) STANDARDIZE / VALIDATE COLUMN NAMES
# =========================================================
# Expected columns from your SAS export:
# customerID, tenure, Contract, MonthlyCharges, TechSupport, risk_score,
# risk_band, priority, recommended_action, Churn
#
# We will rename safely if needed.

rename_map = {}
for col in df.columns:
    clean = col.strip()
    if clean.lower() == "customerid":
        rename_map[col] = "customerID"
    elif clean.lower() == "contract":
        rename_map[col] = "Contract"
    elif clean.lower() == "monthlycharges":
        rename_map[col] = "MonthlyCharges"
    elif clean.lower() == "techsupport":
        rename_map[col] = "TechSupport"
    elif clean.lower() == "risk_score":
        rename_map[col] = "risk_score"
    elif clean.lower() == "risk_band":
        rename_map[col] = "risk_band"
    elif clean.lower() == "priority":
        rename_map[col] = "priority"
    elif clean.lower() == "recommended_action":
        rename_map[col] = "recommended_action"
    elif clean.lower() == "churn":
        rename_map[col] = "Churn"

df = df.rename(columns=rename_map)

required_cols = [
    "customerID", "Contract", "MonthlyCharges", "TechSupport",
    "risk_score", "risk_band", "priority", "recommended_action", "Churn"
]

missing = [c for c in required_cols if c not in df.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")

# =========================================================
# 4) AGENTIC WORKFLOW RULES
# =========================================================
# Agent decisions:
# - Assign queue owner
# - Assign due date
# - Assign action status
# - Assign escalation flag

def assign_owner(priority, action):
    action = str(action).lower()
    if priority == "P1":
        return "Retention Manager"
    elif "tech support" in action:
        return "Support Team"
    elif "onboarding" in action:
        return "Customer Success Team"
    else:
        return "Retention Analyst"

def assign_due_days(priority):
    if priority == "P1":
        return 1
    elif priority == "P2":
        return 3
    else:
        return 7

def assign_escalation(priority, churn):
    if priority == "P1" and str(churn).strip().lower() == "yes":
        return "Escalate Immediately"
    elif priority == "P1":
        return "Monitor Closely"
    elif priority == "P2":
        return "Standard Follow-up"
    else:
        return "Routine Monitoring"

df["owner"] = df.apply(lambda x: assign_owner(x["priority"], x["recommended_action"]), axis=1)
df["due_in_days"] = df["priority"].apply(assign_due_days)
df["due_date"] = df["due_in_days"].apply(lambda x: TODAY + timedelta(days=int(x)))
df["action_status"] = "Pending"
df["escalation_flag"] = df.apply(lambda x: assign_escalation(x["priority"], x["Churn"]), axis=1)

# =========================================================
# 5) SORT BY BUSINESS IMPORTANCE
# =========================================================
priority_order = {"P1": 1, "P2": 2, "P3": 3}
risk_band_order = {"Very High": 1, "High": 2, "Medium": 3, "Low": 4}

df["priority_rank"] = df["priority"].map(priority_order)
df["risk_rank"] = df["risk_band"].map(risk_band_order)

df = df.sort_values(
    by=["priority_rank", "risk_rank", "risk_score"],
    ascending=[True, True, False]
)

# =========================================================
# 6) CREATE PRIORITY QUEUES
# =========================================================
p1_df = df[df["priority"] == "P1"].copy()
p2_df = df[df["priority"] == "P2"].copy()
p3_df = df[df["priority"] == "P3"].copy()

# =========================================================
# 7) EXPORT EXCEL OUTPUTS
# =========================================================
df.to_excel(MASTER_OUTPUT, index=False)
p1_df.to_excel(P1_OUTPUT, index=False)
p2_df.to_excel(P2_OUTPUT, index=False)
p3_df.to_excel(P3_OUTPUT, index=False)

print(f"Master file saved: {MASTER_OUTPUT}")
print(f"P1 queue saved: {P1_OUTPUT}")
print(f"P2 queue saved: {P2_OUTPUT}")
print(f"P3 queue saved: {P3_OUTPUT}")

# =========================================================
# 8) CREATE RULE-BASED AGENT SUMMARY
# =========================================================
total_cases = len(df)
p1_count = len(p1_df)
p2_count = len(p2_df)
p3_count = len(p3_df)

very_high_count = (df["risk_band"] == "Very High").sum()
high_count = (df["risk_band"] == "High").sum()

churn_yes_count = (df["Churn"].astype(str).str.strip().str.lower() == "yes").sum()

summary_text = f"""
AGENTIC AI ACTION REPORT
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

1. Overall Queue Summary
- Total actionable high-risk customers: {total_cases}
- P1 customers: {p1_count}
- P2 customers: {p2_count}
- P3 customers: {p3_count}

2. Risk Summary
- Very High risk customers: {very_high_count}
- High risk customers: {high_count}

3. Actual Churn Indicator
- Customers already marked as churned in this high-risk output: {churn_yes_count}

4. Operational Decision Logic
- P1 customers require immediate retention action within 1 day
- P2 customers require follow-up within 3 days
- P3 customers should be monitored within 7 days

5. Action Routing
- Retention Manager handles top priority retention cases
- Support Team handles tech-support related actions
- Customer Success Team handles onboarding support actions
- Retention Analyst handles general monitoring and outreach

6. Output Files Created
- agent_action_master.xlsx
- p1_queue.xlsx
- p2_queue.xlsx
- p3_queue.xlsx
"""

with open(SUMMARY_TXT, "w", encoding="utf-8") as f:
    f.write(summary_text)

print(f"Rule-based summary saved: {SUMMARY_TXT}")

# =========================================================
# 9) OPTIONAL GEMINI REPORT (LLM WRITES MANAGER SUMMARY)
# =========================================================
if USE_GEMINI and GEMINI_AVAILABLE:
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY not found. Skipping Gemini report.")
    else:
        client = genai.Client(api_key=GEMINI_API_KEY)

        # Take a few sample rows for LLM context
        sample_rows = df.head(10)

        sample_text_lines = []
        for _, row in sample_rows.iterrows():
            sample_text_lines.append(
                f"CustomerID={row['customerID']}, "
                f"Priority={row['priority']}, "
                f"RiskBand={row['risk_band']}, "
                f"RiskScore={row['risk_score']}, "
                f"Owner={row['owner']}, "
                f"Action={row['recommended_action']}, "
                f"Escalation={row['escalation_flag']}, "
                f"DueDate={row['due_date']}"
            )

        sample_text = "\n".join(sample_text_lines)

        system_instruction = """
You are an AI operations manager assistant.
Your task is to write a concise action-oriented report for customer retention operations.

Your output must contain:
1. Executive Action Summary
2. Queue Prioritization Insight
3. Immediate Actions for P1
4. Recommended Follow-up Strategy
5. Business Impact Note

Keep the language professional and operational.
Do not invent counts beyond what is provided.
"""

        user_content = f"""
Here is the agentic churn action data:

Total actionable customers: {total_cases}
P1 count: {p1_count}
P2 count: {p2_count}
P3 count: {p3_count}
Very High risk count: {very_high_count}
High risk count: {high_count}
Customers already churned in current high-risk set: {churn_yes_count}

Sample routed records:
{sample_text}

Generate the final operations report.
"""

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            )
        )

        gemini_report = response.text

        with open(GEMINI_REPORT_TXT, "w", encoding="utf-8") as f:
            f.write(gemini_report)

        print("\n===== GEMINI AGENT REPORT =====\n")
        print(gemini_report)
        print(f"\nGemini agent report saved: {GEMINI_REPORT_TXT}")
else:
    print("Gemini step skipped (USE_GEMINI=False or package not installed).")

print("\nAgentic AI workflow completed successfully.")