import os
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Optional Gemini support
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="Customer Churn Copilot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent
AGENT_OUTPUTS_DIR = BASE_DIR / "agent_outputs"
PROJECT_SUMMARY_FILE = BASE_DIR / "project_summary.xlsx"
HIGH_RISK_FILE = BASE_DIR / "high_risk_actions.xlsx"
CHURN_SCORED_FILE = BASE_DIR / "churn_scored.xlsx"
GENAI_SUMMARY_FILE = BASE_DIR / "executive_summary_gemini.txt"
AGENT_SUMMARY_FILE = AGENT_OUTPUTS_DIR / "agent_summary.txt"
GEMINI_AGENT_REPORT_FILE = AGENT_OUTPUTS_DIR / "gemini_agent_report.txt"

# ------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------

def safe_read_excel(path: Path):
    if path.exists():
        return pd.read_excel(path, engine="openpyxl")
    return None


def load_text_file(path: Path, default_text: str = ""):
    if path.exists():
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return default_text
    return default_text


def format_int(x):
    try:
        return f"{int(x):,}"
    except Exception:
        return str(x)


def infer_queues(df: pd.DataFrame):
    if df is None or df.empty or "priority" not in df.columns:
        return {"P1": 0, "P2": 0, "P3": 0}
    counts = df["priority"].astype(str).value_counts().to_dict()
    return {"P1": counts.get("P1", 0), "P2": counts.get("P2", 0), "P3": counts.get("P3", 0)}


def get_default_summary():
    return (
        "The customer churn analysis shows a churn rate of 26.54%. "
        "Month-to-month customers are the most vulnerable segment. "
        "High and Very High-risk customers should be prioritized with immediate retention actions, "
        "including discount offers, tech support assistance, and onboarding follow-ups."
    )


def build_sample_data():
    metrics = {
        "total_customers": 7043,
        "churned_customers": 1869,
        "churn_rate": 26.54,
        "high_risk_customers": 1650,
        "very_high_risk_customers": 1294,
    }
    risk_df = pd.DataFrame([
        {"risk_band": "Low", "count": 2299},
        {"risk_band": "Medium", "count": 1800},
        {"risk_band": "High", "count": 1650},
        {"risk_band": "Very High", "count": 1294},
    ])
    contract_df = pd.DataFrame([
        {"Contract": "Month-to-month", "Churn": "No", "count": 2220},
        {"Contract": "Month-to-month", "Churn": "Yes", "count": 1655},
        {"Contract": "One year", "Churn": "No", "count": 1307},
        {"Contract": "One year", "Churn": "Yes", "count": 166},
        {"Contract": "Two year", "Churn": "No", "count": 1647},
        {"Contract": "Two year", "Churn": "Yes", "count": 48},
    ])
    actions_df = pd.DataFrame([
        {"customerID": "0004-TLHLJ", "risk_band": "Very High", "priority": "P1", "owner": "Retention Manager", "recommended_action": "Immediate retention call + discount offer", "due_date": "1 day", "risk_score": 80, "Churn": "Yes"},
        {"customerID": "0011-IGKFF", "risk_band": "Very High", "priority": "P1", "owner": "Retention Manager", "recommended_action": "Immediate retention call + discount offer", "due_date": "1 day", "risk_score": 65, "Churn": "Yes"},
        {"customerID": "0013-EXCHZ", "risk_band": "High", "priority": "P2", "owner": "Retention Analyst", "recommended_action": "Onboarding support follow-up", "due_date": "3 days", "risk_score": 60, "Churn": "Yes"},
        {"customerID": "0015-UOCOJ", "risk_band": "High", "priority": "P2", "owner": "Support Team", "recommended_action": "Offer tech support assistance", "due_date": "3 days", "risk_score": 60, "Churn": "No"},
        {"customerID": "0023-HGHWL", "risk_band": "High", "priority": "P3", "owner": "Retention Analyst", "recommended_action": "Monitor and send engagement message", "due_date": "7 days", "risk_score": 60, "Churn": "Yes"},
    ])
    return metrics, risk_df, contract_df, actions_df


@st.cache_data(show_spinner=False)
def load_data():
    project_summary = safe_read_excel(PROJECT_SUMMARY_FILE)
    high_risk = safe_read_excel(HIGH_RISK_FILE)
    churn_scored = safe_read_excel(CHURN_SCORED_FILE)

    if project_summary is not None and not project_summary.empty:
        row = project_summary.iloc[0]
        metrics = {
            "total_customers": int(row.get("total_customers", 0)),
            "churned_customers": int(row.get("churned_customers", 0)),
            "churn_rate": float(row.get("churn_rate", 0.0)),
            "high_risk_customers": int(row.get("high_risk_customers", 0)),
            "very_high_risk_customers": int(row.get("very_high_risk_customers", 0)),
        }
    else:
        metrics, risk_df, contract_df, actions_df = build_sample_data()
        return {
            "metrics": metrics,
            "risk_df": risk_df,
            "contract_df": contract_df,
            "high_risk_df": actions_df,
            "churn_scored_df": None,
            "using_sample_data": True,
        }

    if churn_scored is not None and not churn_scored.empty and "risk_band" in churn_scored.columns:
        risk_df = churn_scored["risk_band"].astype(str).value_counts().reset_index()
        risk_df.columns = ["risk_band", "count"]
    else:
        risk_df = pd.DataFrame([
            {"risk_band": "Low", "count": 2299},
            {"risk_band": "Medium", "count": 1800},
            {"risk_band": "High", "count": 1650},
            {"risk_band": "Very High", "count": 1294},
        ])

    if churn_scored is not None and not churn_scored.empty and set(["Contract", "Churn"]).issubset(churn_scored.columns):
        contract_df = churn_scored.groupby(["Contract", "Churn"]).size().reset_index(name="count")
    else:
        contract_df = pd.DataFrame([
            {"Contract": "Month-to-month", "Churn": "No", "count": 2220},
            {"Contract": "Month-to-month", "Churn": "Yes", "count": 1655},
            {"Contract": "One year", "Churn": "No", "count": 1307},
            {"Contract": "One year", "Churn": "Yes", "count": 166},
            {"Contract": "Two year", "Churn": "No", "count": 1647},
            {"Contract": "Two year", "Churn": "Yes", "count": 48},
        ])

    if high_risk is None or high_risk.empty:
        _, _, _, high_risk = build_sample_data()

    return {
        "metrics": metrics,
        "risk_df": risk_df,
        "contract_df": contract_df,
        "high_risk_df": high_risk,
        "churn_scored_df": churn_scored,
        "using_sample_data": False,
    }


def local_grounded_answer(question: str, data_bundle: dict):
    q = (question or "").strip().lower()
    metrics = data_bundle["metrics"]
    risk_df = data_bundle["risk_df"]
    contract_df = data_bundle["contract_df"]
    high_risk_df = data_bundle["high_risk_df"]

    if not q:
        return "Please enter a churn-related question."

    if "churn rate" in q or ("overall" in q and "churn" in q):
        return (
            f"The overall churn rate is {metrics['churn_rate']:.2f}%, with "
            f"{format_int(metrics['churned_customers'])} churned customers out of "
            f"{format_int(metrics['total_customers'])} total customers."
        )

    if "highest churn" in q or ("segment" in q and "churn" in q):
        if not contract_df.empty:
            churn_yes = contract_df[contract_df["Churn"].astype(str).str.lower() == "yes"].copy()
            if not churn_yes.empty:
                top = churn_yes.sort_values("count", ascending=False).iloc[0]
                return (
                    f"{top['Contract']} customers have the highest churn volume in the current analysis, "
                    f"with {format_int(top['count'])} churned customers."
                )
        return "Month-to-month customers have the highest churn in the current analysis."

    if "high risk" in q and "how many" in q:
        high_count = int(risk_df[risk_df["risk_band"] == "High"]["count"].sum()) if not risk_df.empty else metrics["high_risk_customers"]
        very_high_count = int(risk_df[risk_df["risk_band"] == "Very High"]["count"].sum()) if not risk_df.empty else metrics["very_high_risk_customers"]
        return f"There are {format_int(high_count)} High-risk customers and {format_int(very_high_count)} Very High-risk customers."

    if "team do first" in q or "what should the team do" in q or "first action" in q:
        return (
            "The retention team should prioritize P1 customers first—especially those in the Very High-risk band—"
            "with immediate retention calls, discount offers, and support intervention where required."
        )

    if "p1" in q or "priority" in q:
        queues = infer_queues(high_risk_df)
        return (
            f"The current action queues contain P1={queues['P1']}, P2={queues['P2']}, and P3={queues['P3']} customers. "
            "P1 customers should be actioned within 1 day."
        )

    if "why" in q and "month-to-month" in q:
        return (
            "Month-to-month customers are more vulnerable because they are not locked into longer contracts, "
            "which makes them more likely to leave when they face dissatisfaction, support issues, or better competitor offers."
        )

    if "customer" in q and high_risk_df is not None and not high_risk_df.empty:
        words = q.replace(",", " ").replace("?", " ").split()
        possible_ids = [w.upper() for w in words if "-" in w or any(ch.isdigit() for ch in w)]
        if possible_ids and "customerID" in high_risk_df.columns:
            ids_series = high_risk_df["customerID"].astype(str).str.upper()
            for cid in possible_ids:
                matches = high_risk_df[ids_series == cid]
                if not matches.empty:
                    row = matches.iloc[0]
                    action = row.get("recommended_action", "No action available")
                    risk_band = row.get("risk_band", "Unknown")
                    priority = row.get("priority", "Unknown")
                    score = row.get("risk_score", "NA")
                    return (
                        f"Customer {cid} is in the {risk_band} risk band with priority {priority} and risk score {score}. "
                        f"Recommended action: {action}."
                    )

    return (
        "I can answer churn-specific business questions grounded in the project outputs. "
        "Try asking about churn rate, highest churn segment, High/Very High-risk counts, P1 queues, or a specific customer ID."
    )


def ask_gemini(question: str, data_bundle: dict):
    if not GEMINI_AVAILABLE:
        return None, "Gemini SDK is not installed. Run: pip install google-genai"

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None, "Gemini API key not found. Set GEMINI_API_KEY or GOOGLE_API_KEY in your environment."

    metrics = data_bundle["metrics"]
    contract_df = data_bundle["contract_df"]
    risk_df = data_bundle["risk_df"]
    high_risk_df = data_bundle["high_risk_df"]

    contract_insight = "Month-to-month customers show the highest churn."
    if contract_df is not None and not contract_df.empty and set(["Contract", "Churn", "count"]).issubset(contract_df.columns):
        churn_yes = contract_df[contract_df["Churn"].astype(str).str.lower() == "yes"].copy()
        if not churn_yes.empty:
            top = churn_yes.sort_values("count", ascending=False).iloc[0]
            contract_insight = f"{top['Contract']} customers show the highest churn with {int(top['count'])} churned customers."

    sample_rows = ""
    if high_risk_df is not None and not high_risk_df.empty:
        cols = [c for c in ["customerID", "risk_band", "priority", "recommended_action", "risk_score", "Churn"] if c in high_risk_df.columns]
        sample = high_risk_df[cols].head(8).to_dict(orient="records")
        sample_rows = str(sample)

    system_instruction = (
        "You are a churn analytics assistant. Answer only from the provided churn project context. "
        "If the answer is not supported by the context, clearly say that the current churn outputs do not provide enough information."
    )

    user_context = f"""
Project metrics:
- Total customers: {metrics['total_customers']}
- Churned customers: {metrics['churned_customers']}
- Churn rate: {metrics['churn_rate']:.2f}%
- High-risk customers: {metrics['high_risk_customers']}
- Very High-risk customers: {metrics['very_high_risk_customers']}

Contract insight:
- {contract_insight}

Risk distribution:
{risk_df.to_dict(orient='records') if risk_df is not None else []}

Sample high-risk customer rows:
{sample_rows}

Question:
{question}
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=user_context,
            config=types.GenerateContentConfig(system_instruction=system_instruction)
        )
        return response.text, None
    except Exception as e:
        return None, str(e)


# ------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------
with st.spinner("Loading churn project outputs..."):
    data_bundle = load_data()

metrics = data_bundle["metrics"]
risk_df = data_bundle["risk_df"]
contract_df = data_bundle["contract_df"]
high_risk_df = data_bundle["high_risk_df"]
using_sample_data = data_bundle["using_sample_data"]

# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------
st.sidebar.title("⚙️ Churn Copilot")
st.sidebar.caption("Base SAS + Gen AI + Agentic AI")

if using_sample_data:
    st.sidebar.warning("Excel files not found. Showing sample demo data.")
else:
    st.sidebar.success("Loaded project files from local folder.")

st.sidebar.markdown("### Files detected")
for file_path in [PROJECT_SUMMARY_FILE, HIGH_RISK_FILE, CHURN_SCORED_FILE, AGENT_SUMMARY_FILE, GENAI_SUMMARY_FILE, GEMINI_AGENT_REPORT_FILE]:
    st.sidebar.write(f"{'✅' if file_path.exists() else '❌'} {file_path.name}")

use_gemini_qna = st.sidebar.toggle("Use Gemini for Q&A", value=False)
show_raw_tables = st.sidebar.toggle("Show raw tables", value=False)

with st.sidebar.expander("How to run"):
    st.code("streamlit run streamlit_app.py", language="bash")

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
st.title("📊 Customer Churn Copilot")
st.caption("Customer Churn Analysis using Base SAS + Gen AI + Agentic AI")

# KPI CARDS
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Customers", format_int(metrics["total_customers"]))
k2.metric("Churned Customers", format_int(metrics["churned_customers"]))
k3.metric("Churn Rate", f"{metrics['churn_rate']:.2f}%")
k4.metric("High Risk", format_int(metrics["high_risk_customers"]))
k5.metric("Very High Risk", format_int(metrics["very_high_risk_customers"]))

# TABS

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Gen AI Summary", "Q&A Assistant", "Agent Queues"])

# ------------------------------------------------------------
# TAB 1: OVERVIEW
# ------------------------------------------------------------
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Risk Band Distribution")
        fig_pie = px.pie(
            risk_df,
            names="risk_band",
            values="count",
            hole=0.35,
            color="risk_band",
            color_discrete_map={
                "Low": "#8b5cf6",
                "Medium": "#06b6d4",
                "High": "#f59e0b",
                "Very High": "#ef4444",
            },
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.subheader("Contract-wise Churn")
        fig_contract = px.bar(
            contract_df,
            x="Contract",
            y="count",
            color="Churn",
            barmode="group",
            color_discrete_map={"No": "#94a3b8", "Yes": "#ef4444"},
        )
        st.plotly_chart(fig_contract, use_container_width=True)

    st.markdown("### Quick Insights")
    insight1, insight2, insight3 = st.columns(3)
    with insight1:
        st.info("**Top finding:** Month-to-month customers are the most vulnerable churn segment.")
    with insight2:
        st.info("**Recommended focus:** Prioritize P1 customers with retention calls and discount offers.")
    with insight3:
        st.info("**Business impact:** Reducing churn in high-risk queues can directly protect recurring revenue.")

    if show_raw_tables:
        st.markdown("### Raw chart data")
        st.dataframe(risk_df, use_container_width=True)
        st.dataframe(contract_df, use_container_width=True)

# ------------------------------------------------------------
# TAB 2: GEN AI SUMMARY
# ------------------------------------------------------------
with tab2:
    st.subheader("LLM-Generated Business Summary")
    summary_text = load_text_file(GENAI_SUMMARY_FILE, get_default_summary())
    edited_summary = st.text_area(
        "Executive explanation generated from SAS outputs",
        value=summary_text,
        height=260,
    )

    c1, c2, c3 = st.columns(3)
    c1.success("""**Top finding**

Month-to-month customers are the most vulnerable churn segment.""")
    c2.success("""**Recommended focus**

Prioritize P1 customers with retention calls and discount offers.""")
    c3.success("""**Business impact**

Reducing churn in high-risk queues can directly protect recurring revenue.""")

    st.download_button(
        label="Download Summary",
        data=edited_summary.encode("utf-8"),
        file_name="executive_summary.txt",
        mime="text/plain",
    )

# ------------------------------------------------------------
# TAB 3: Q&A ASSISTANT
# ------------------------------------------------------------
with tab3:
    st.subheader("Ask the Churn Assistant")
    st.caption("Grounded questions over churn outputs")

    quick_questions = [
        "What is the churn rate?",
        "Which segment has the highest churn?",
        "How many high risk customers are there?",
        "What should the team do first?",
        "Why are month-to-month customers more likely to churn?",
    ]

    qcols = st.columns(len(quick_questions))
    for i, qq in enumerate(quick_questions):
        if qcols[i].button(qq, use_container_width=True):
            st.session_state["question_box"] = qq

    question = st.text_input(
        "Enter your question",
        value=st.session_state.get("question_box", ""),
        placeholder="e.g. What is the churn rate?",
    )

    ask = st.button("Ask", type="primary")
    if ask:
        with st.spinner("Generating answer..."):
            if use_gemini_qna:
                response_text, err = ask_gemini(question, data_bundle)
                if err:
                    st.error(f"Gemini error: {err}")
                    st.write(local_grounded_answer(question, data_bundle))
                else:
                    st.write(response_text)
            else:
                st.write(local_grounded_answer(question, data_bundle))

        st.markdown("### Suggested query ideas")
        st.markdown(
        """s
    - What is the churn rate?
    - Which contract type has the highest churn?
    - How many High and Very High-risk customers are there?
    - What should the team do first?
    - Why is customer 0004-TLHLJ high risk?
    """
        )

# ------------------------------------------------------------
# TAB 4: AGENT QUEUES
# ------------------------------------------------------------
with tab4:
    st.subheader("Agentic AI Action Queues")
    queues = infer_queues(high_risk_df)

    q1, q2, q3 = st.columns(3)
    q1.metric("P1 Queue", format_int(queues["P1"]))
    q2.metric("P2 Queue", format_int(queues["P2"]))
    q3.metric("P3 Queue", format_int(queues["P3"]))

    p1_df = high_risk_df[high_risk_df["priority"].astype(str) == "P1"].copy() if "priority" in high_risk_df.columns else pd.DataFrame()
    p2_df = high_risk_df[high_risk_df["priority"].astype(str) == "P2"].copy() if "priority" in high_risk_df.columns else pd.DataFrame()
    p3_df = high_risk_df[high_risk_df["priority"].astype(str) == "P3"].copy() if "priority" in high_risk_df.columns else pd.DataFrame()

    st.markdown("### Sample Action Queue")
    display_cols = [c for c in ["customerID", "risk_band", "priority", "owner", "recommended_action", "due_date", "risk_score", "Churn"] if c in high_risk_df.columns]
    if display_cols:
        st.dataframe(high_risk_df[display_cols].head(20), use_container_width=True)

    with st.expander("Open queue tables"):
        subtab1, subtab2, subtab3 = st.tabs(["P1", "P2", "P3"])
        with subtab1:
            st.dataframe(p1_df, use_container_width=True)
        with subtab2:
            st.dataframe(p2_df, use_container_width=True)
        with subtab3:
            st.dataframe(p3_df, use_container_width=True)

    if AGENT_SUMMARY_FILE.exists():
        st.markdown("### Agent Summary")
        st.text_area("Rule-based operational summary", value=load_text_file(AGENT_SUMMARY_FILE), height=240)

    if GEMINI_AGENT_REPORT_FILE.exists():
        st.markdown("### Gemini Agent Report")
        st.text_area("LLM-generated operations report", value=load_text_file(GEMINI_AGENT_REPORT_FILE), height=240)

    # Download buttons
    d1, d2, d3 = st.columns(3)
    if not p1_df.empty:
        d1.download_button("Download P1 Queue", p1_df.to_csv(index=False).encode("utf-8"), "p1_queue.csv", "text/csv")
    if not p2_df.empty:
        d2.download_button("Download P2 Queue", p2_df.to_csv(index=False).encode("utf-8"), "p2_queue.csv", "text/csv")
    if not p3_df.empty:
        d3.download_button("Download P3 Queue", p3_df.to_csv(index=False).encode("utf-8"), "p3_queue.csv", "text/csv")

st.markdown("---")
st.caption("Built with Base SAS + Python + Gen AI + Agentic AI")
