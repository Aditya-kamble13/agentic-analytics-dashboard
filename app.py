import os
import io
import json
import time
import uuid
import xml.etree.ElementTree as ET
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# Safe API Key retrieval for both Local (.env) and Cloud (st.secrets)
GEMINI_API_KEY = None
try:
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
except Exception:
    pass

if not GEMINI_API_KEY:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

st.set_page_config(page_title="Universal Agentic Analytics Dashboard", layout="wide")

# Persistent Storage Folder for Unique Dashboards
DATA_DIR = "saved_dashboards"
os.makedirs(DATA_DIR, exist_ok=True)

def save_dashboard(state_data, dashboard_name):
    clean_name = "".join([c if c.isalnum() else "-" for c in dashboard_name.lower()])
    unique_id = f"{clean_name}-{str(uuid.uuid4())[:8]}"
    file_path = os.path.join(DATA_DIR, f"{unique_id}.json")
    
    clean_payload = {}
    if "data" in state_data and state_data["data"]:
        temp_df = pd.DataFrame(state_data["data"])
        for col in temp_df.columns:
            temp_df[col] = temp_df[col].astype(str)
        clean_payload["data"] = temp_df.to_dict(orient="list")
    
    clean_payload["ai_explanation"] = str(state_data.get("ai_explanation", ""))
    
    # Save exact Plotly figure JSON string
    if "fig_str" in state_data and state_data["fig_str"]:
        clean_payload["fig_str"] = state_data["fig_str"]
        
    with open(file_path, "w") as f:
        json.dump(clean_payload, f, default=str)
    return unique_id

def load_dashboard(dashboard_id):
    file_path = os.path.join(DATA_DIR, f"{dashboard_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return None

# Session state initialization for Landing Page
if "launched" not in st.session_state:
    st.session_state.launched = False

# -------------------------------------------------------------------
# Futuristic Landing / Welcome Page (Dark Theme & Header Fix)
# -------------------------------------------------------------------
if not st.session_state.launched:
    st.markdown("""
        <style>
        .stApp {
            background-color: #0b0f19 !important;
            color: #ffffff !important;
        }
        header[data-testid="stHeader"] {
            background-color: #0b0f19 !important;
        }
        .main-title {
            font-size: 3.2rem;
            font-weight: 800;
            background: linear-gradient(90deg, #6366f1, #06b6d4, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            margin-bottom: 0px;
        }
        .subtitle {
            font-size: 1.25rem;
            color: #94a3b8 !important;
            text-align: center;
            margin-bottom: 35px;
        }
        .feature-card {
            background-color: #111827 !important;
            border: 1px solid #1f2937 !important;
            padding: 24px;
            border-radius: 16px;
            text-align: center;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
        }
        .feature-card h3 {
            color: #60a5fa !important;
            margin-bottom: 12px;
            font-weight: 700;
        }
        .feature-card p {
            color: #d1d5db !important;
            font-size: 0.95rem;
            line-height: 1.6;
        }
        div.stButton > button {
            background: linear-gradient(90deg, #4f46e5, #06b6d4) !important;
            color: #ffffff !important;
            font-size: 1.15rem !important;
            font-weight: 700 !important;
            padding: 14px 28px !important;
            border-radius: 12px !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(79, 70, 229, 0.4) !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="main-title">⚡ Universal Agentic Analytics Hub</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Autonomous Data Engineering & Zero-Shot AI Visualization Powered by Gemini</p>', unsafe_allow_html=True)

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
            <div class="feature-card">
                <h3>🛠️ Autonomous Hygiene</h3>
                <p>AI-driven anomaly detection, missing value imputation, and automated data cleansing in a single click.</p>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <div class="feature-card">
                <h3>🤖 Zero-Shot AI Engine</h3>
                <p>Convert any complex text prompt instantly into fully interactive Plotly charts, maps, and dashboards.</p>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
            <div class="feature-card">
                <h3>🛡️ Smart RBAC & Fallback</h3>
                <p>Seamless role-based link sharing (Editor vs Viewer) backed by an offline-resilient local fallback engine.</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    c_l1, c_l2, c_l3 = st.columns([1, 2, 1])
    with c_l2:
        if st.button("🚀 Launch Agentic Workspace", use_container_width=True):
            st.session_state.launched = True
            st.rerun()

else:
    # Read query params from URL quietly in background
    query_params = st.query_params
    mode_param = query_params.get("mode", "editor")
    dashboard_id_param = query_params.get("dashboard_id", None)
    is_editor = (mode_param == "editor")

    # Load shared dashboard state automatically if dashboard_id is provided in URL
    if dashboard_id_param and "df" not in st.session_state:
        saved_state = load_dashboard(dashboard_id_param)
        if saved_state:
            st.session_state.df = pd.DataFrame(saved_state.get("data", {}))
            st.session_state.file_name = "shared_dashboard.csv"
            st.session_state.ai_explanation = saved_state.get("ai_explanation", "Loaded from shared link.")
            
            # Restore saved Plotly figure cleanly using pio.from_json
            if "fig_str" in saved_state and saved_state["fig_str"]:
                try:
                    st.session_state.custom_fig = pio.from_json(saved_state["fig_str"])
                except Exception:
                    st.session_state.custom_fig = None
            
            # Auto-skip landing page when opening a shared unique link
            st.session_state.launched = True
        else:
            st.error("Shared dashboard not found or expired.")

    # -------------------------------------------------------------------
    # Main Dashboard Workspace
    # -------------------------------------------------------------------
    st.title("🚀 Universal Agentic Analytics Dashboard")

    st.sidebar.header("📊 Agentic Analytics Hub")
    if is_editor:
        st.sidebar.success("✏️ **Editor Mode**: Full access enabled.")
    else:
        st.sidebar.info("🔒 **Viewer Mode**: Read-only access.")

    st.sidebar.markdown("---")

    # Clean Interactive Share Expander
    with st.sidebar.expander("🔗 Share Dashboard Links"):
        dashboard_name_input = st.text_input("Dashboard Name", value="My-Custom-Dashboard")
        selected_role = st.radio("Select Access Level:", ["Editor (Full Access)", "Viewer (Read Only)"], key="share_mode_select")
        
        base_url = "https://agentic-analytics-dashboard-globally.streamlit.app/"
        target_mode = "editor" if "Editor" in selected_role else "viewer"
        
        if st.button("Generate Unique Link"):
            if "df" in st.session_state and st.session_state.df is not None:
                df_dict = st.session_state.df.to_dict(orient="list")
                
                # Serialize current Plotly figure as valid JSON string
                fig_str_data = pio.to_json(st.session_state.custom_fig) if st.session_state.get("custom_fig") is not None else None
                
                state_payload = {
                    "data": df_dict,
                    "ai_explanation": st.session_state.get("ai_explanation", "Default analytics summary."),
                    "fig_str": fig_str_data
                }
                unique_id = save_dashboard(state_payload, dashboard_name_input)
                generated_link = f"{base_url}?dashboard_id={unique_id}&mode={target_mode}"
                st.success("Link generated successfully!")
                st.code(generated_link, language="text")
            else:
                st.warning("Please upload a dataset first to generate a unique link!")

    # File uploader is only available for editors
    if is_editor:
        uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel Dataset", type=["csv", "xlsx", "xls"])
        if uploaded_file is not None:
            if "df" not in st.session_state or st.session_state.get("file_name") != uploaded_file.name:
                if uploaded_file.name.endswith(".csv"):
                    st.session_state.df = pd.read_csv(uploaded_file)
                else:
                    st.session_state.df = pd.read_excel(uploaded_file)
                st.session_state.file_name = uploaded_file.name
    else:
        st.sidebar.info("📁 File uploading is disabled in Viewer Mode.")

    if "df" in st.session_state and st.session_state.df is not None:
        df = st.session_state.df

        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

        if "custom_fig" not in st.session_state:
            st.session_state.custom_fig = None
        if "ai_explanation" not in st.session_state:
            st.session_state.ai_explanation = None
        if "last_error" not in st.session_state:
            st.session_state.last_error = None

        # -------------------------------------------------------------------
        # Step 1: AI Data Hygiene Agent (Disabled for Viewers)
        # -------------------------------------------------------------------
        st.header("🛠️ Step 1: AI Data Hygiene Agent")

        total_rows = df.shape[0]
        total_cols = df.shape[1]
        null_records = int(df.isnull().sum().sum())
        duplicate_rows = int(df.duplicated().sum())

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Total Rows", total_rows)
        col_m2.metric("Total Columns", total_cols)
        col_m3.metric("Null Records", null_records)
        col_m4.metric("Duplicate Rows", duplicate_rows)

        if is_editor:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🧹 Clean Missing Values"):
                    temp_df = st.session_state.df.dropna(how='all', axis=1)
                    unnamed_cols = [col for col in temp_df.columns if 'Unnamed' in str(col)]
                    for col in unnamed_cols:
                        if temp_df[col].isnull().sum() / len(temp_df) > 0.5:
                            temp_df = temp_df.drop(columns=[col])
                    
                    for col in temp_df.select_dtypes(include=['object', 'category']).columns:
                        temp_df[col] = temp_df[col].fillna("N/A")
                        
                    for col in temp_df.select_dtypes(include=['number']).columns:
                        temp_df[col] = temp_df[col].fillna(0)
                        
                    st.session_state.df = temp_df.dropna(how='all', axis=0)
                    st.success("Missing values cleaned!")
                    st.rerun()

            with c2:
                if st.button("🗑️ Remove Duplicate Records"):
                    st.session_state.df = st.session_state.df.drop_duplicates()
                    st.success("Duplicates removed!")
                    st.rerun()
        else:
            st.info("ℹ️ Data cleaning options are restricted in Viewer Mode.")

        st.markdown("---")

        # -------------------------------------------------------------------
        # Step 2: Download Cleaned Data
        # -------------------------------------------------------------------
        st.header("📥 Step 2: Dataset & Export")
        st.dataframe(df.head(10), use_container_width=True)

        if is_editor:
            d_col1, d_col2, d_col3, d_col4 = st.columns(4)
            csv_bytes = st.session_state.df.to_csv(index=False).encode('utf-8')
            d_col1.download_button("📄 Download CSV", csv_bytes, "cleaned_data.csv", "text/csv")

            output_xlsx = io.BytesIO()
            with pd.ExcelWriter(output_xlsx, engine='openpyxl') as writer:
                st.session_state.df.to_excel(writer, index=False, sheet_name='CleanedData')
            d_col2.download_button("📊 Download XLSX", output_xlsx.getvalue(), "cleaned_data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            d_col3.download_button("📁 Download XLS", output_xlsx.getvalue(), "cleaned_data.xls", "application/vnd.ms-excel")

            def dataframe_to_xml(df_in):
                root = ET.Element("dataset")
                for _, row in df_in.iterrows():
                    item = ET.SubElement(root, "record")
                    for col in df_in.columns:
                        child = ET.SubElement(item, str(col).replace(" ", "_"))
                        child.text = str(row[col])
                return ET.tostring(root, encoding='utf-8')

            d_col4.download_button("🏷️ Download XML", dataframe_to_xml(st.session_state.df), "cleaned_data.xml", "application/xml")

        st.markdown("---")

        # -------------------------------------------------------------------
        # Advanced Local Visualizer (High Detail City & Chart Support)
        # -------------------------------------------------------------------
        def build_local_fallback_chart(prompt_text):
            prompt_lower = prompt_text.lower()
            cat_col = cat_cols[0] if cat_cols else df.columns[0]
            num_col = num_cols[0] if num_cols else df.columns[-1]

            grouped_df = df.groupby(cat_col, as_index=False)[num_col].sum().head(15)

            if any(k in prompt_lower for k in ["map", "geo", "choropleth", "location", "city"]):
                # High-contrast detailed Mapbox scatter map for Cities/Locations
                fig = px.scatter_geo(
                    grouped_df,
                    locations=cat_col,
                    locationmode="country names",
                    hover_name=cat_col,
                    size=num_col,
                    color=num_col,
                    projection="natural earth",
                    title=f"Detailed Geographical Distribution of {num_col} by {cat_col}"
                )
                fig.update_layout(template="plotly_dark")
                return fig, f"Generated Detailed Geographical Map for '{cat_col}' & '{num_col}'."

            elif "pie" in prompt_lower and "donut" in prompt_lower:
                fig = make_subplots(rows=1, cols=2, specs=[[{"type": "domain"}, {"type": "domain"}]],
                                    subplot_titles=["Pie Chart", "Donut Chart"])
                fig.add_trace(go.Pie(labels=grouped_df[cat_col], values=grouped_df[num_col], name="Pie"), row=1, col=1)
                fig.add_trace(go.Pie(labels=grouped_df[cat_col], values=grouped_df[num_col], hole=0.4, name="Donut"), row=1, col=2)
                fig.update_layout(title_text=f"Pie and Donut Breakdown of {num_col} by {cat_col}", template="plotly_dark")
                return fig, f"Generated Pie & Donut chart for '{cat_col}'."

            elif "donut" in prompt_lower:
                fig = px.pie(grouped_df, names=cat_col, values=num_col, hole=0.4, title=f"Donut Chart of {num_col} by {cat_col}")
                fig.update_layout(template="plotly_dark")
                return fig, f"Generated Donut chart for '{cat_col}'."

            elif "pie" in prompt_lower or "chat" in prompt_lower:
                fig = px.pie(grouped_df, names=cat_col, values=num_col, title=f"Pie Chart of {num_col} by {cat_col}")
                fig.update_layout(template="plotly_dark")
                return fig, f"Generated Pie chart for '{cat_col}'."

            elif any(k in prompt_lower for k in ["line", "trend", "time"]):
                fig = px.line(grouped_df, x=cat_col, y=num_col, title=f"Trend of {num_col} by {cat_col}")
                fig.update_layout(template="plotly_dark")
                return fig, f"Generated Line Trend for '{cat_col}'."

            elif "scatter" in prompt_lower:
                x_col = num_cols[0] if len(num_cols) > 0 else df.columns[0]
                y_col = num_cols[1] if len(num_cols) > 1 else x_col
                fig = px.scatter(df, x=x_col, y=y_col, color=cat_col if cat_cols else None, title=f"Scatter Plot: {x_col} vs {y_col}")
                fig.update_layout(template="plotly_dark")
                return fig, f"Generated Scatter plot of {x_col} vs {y_col}."

            else:
                fig = px.bar(grouped_df, x=cat_col, y=num_col, title=f"Bar Chart of {num_col} by {cat_col}")
                fig.update_layout(template="plotly_dark")
                return fig, f"Generated Bar chart of {num_col} by {cat_col}."

        # -------------------------------------------------------------------
        # Step 3: Universal AI Visualization Engine
        # -------------------------------------------------------------------
        st.header("🤖 Step 3: Universal AI Visualization Engine")

        def run_ai_visualization():
            user_prompt = st.session_state.get("viz_user_prompt", "").strip()
            if not user_prompt:
                return

            st.session_state.last_error = None
            if not GEMINI_API_KEY or not client:
                st.session_state.last_error = "`.env` file mein ya Streamlit Secrets mein GEMINI_API_KEY nahi mili!"
                return

            df_preview = df.head(3).to_string()
            prompt = f"""
            You are an expert Plotly Data Visualization Engineer.
            
            Dataset Info:
            Columns: {list(df.columns)}
            Categorical Columns: {cat_cols}
            Numerical Columns: {num_cols}
            Sample Data:
            {df_preview}
            
            User Request: "{user_prompt}"
            
            CRITICAL INSTRUCTIONS:
            1. Correct spelling typos automatically (e.g. 'pie chat' -> 'pie chart').
            2. If user requests a map or city visual, use `px.scatter_geo` or `px.density_mapbox` or `px.bar` with dark template.
            3. Apply `fig.update_layout(template='plotly_dark')` to all charts.
            4. ALWAYS aggregate numerical values using `.groupby()` on categorical columns.
            5. Generate valid Python code using Plotly (`px`, `go`, `make_subplots`, `pd`, `np`).
            6. Save the final figure object in a variable named `fig`.
            7. Output ONLY JSON in this format:
            {{
                "explanation": "<Short 1-line description of the visualization>",
                "code": "<executable python code>"
            }}
            """

            candidate_models = ["gemini-2.5-flash", "gemini-3.8-flash"]
            response = None

            for model_name in candidate_models:
                for attempt in range(3):
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt
                        )
                        if response and response.text:
                            break
                    except Exception as e:
                        time.sleep(1.5 * (attempt + 1))
                if response and response.text:
                    break

            if not response or not response.text:
                fig, exp = build_local_fallback_chart(user_prompt)
                st.session_state.custom_fig = fig
                st.session_state.ai_explanation = exp + " (API busy, fallback used)"
                return

            try:
                raw_text = response.text.strip()
                if "```json" in raw_text:
                    raw_text = raw_text.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_text:
                    raw_text = raw_text.split("```")[1].split("```")[0].strip()

                config = json.loads(raw_text)
                code_to_exec = config.get("code", "")
                st.session_state.ai_explanation = config.get("explanation", "Visualization generated successfully!")

                local_scope = {
                    "df": df.copy(),
                    "px": px,
                    "go": go,
                    "pd": pd,
                    "np": np,
                    "make_subplots": make_subplots
                }

                exec(code_to_exec, local_scope)

                if "fig" in local_scope:
                    st.session_state.custom_fig = local_scope["fig"]
                else:
                    fig, exp = build_local_fallback_chart(user_prompt)
                    st.session_state.custom_fig = fig
                    st.session_state.ai_explanation = exp

            except Exception as e:
                fig, exp = build_local_fallback_chart(user_prompt)
                st.session_state.custom_fig = fig
                st.session_state.ai_explanation = exp

        # AI Prompt Input & Button are strictly available only to Editors
        if is_editor:
            user_prompt = st.text_input(
                "Specify ANY visual type or analysis method:",
                placeholder="e.g. 'use map', 'use pie chat and donut chart', 'bar chart of revenue by city'",
                key="viz_user_prompt",
                on_change=run_ai_visualization
            )

            if st.button("🚀 Generate Any Visual via AI"):
                run_ai_visualization()
        else:
            st.info("🔒 **Viewer Mode**: AI visualization prompt generation is locked. You are viewing the pre-configured shared dashboard insights below.")

        if st.session_state.last_error:
            st.error(f"❌ **Error:** {st.session_state.last_error}")

        if st.session_state.ai_explanation:
            st.info(f"💡 **AI Assistant Insight & Description:** {st.session_state.ai_explanation}")

        st.markdown("---")
        st.subheader("📊 Dynamic Visual Output")

        # Render custom figure if exists, otherwise generate default bar view
        if st.session_state.custom_fig is not None:
            st.plotly_chart(st.session_state.custom_fig, use_container_width=True)
            
            # Download & Export Visual Option for both Editors and Viewers
            try:
                chart_html = st.session_state.custom_fig.to_html(include_plotlyjs='cdn')
                st.download_button(
                    label="📥 Download Chart as HTML",
                    data=chart_html,
                    file_name="analytics_chart.html",
                    mime="text/html"
                )
            except Exception:
                pass
        else:
            if len(cat_cols) > 0 and len(num_cols) > 0:
                default_df = df.groupby(cat_cols[0], as_index=False)[num_cols[0]].sum().head(10)
                default_fig = px.bar(default_df, x=cat_cols[0], y=num_cols[0], title=f"{num_cols[0]} by {cat_cols[0]} (Default View)")
                default_fig.update_layout(template="plotly_dark")
                st.plotly_chart(default_fig, use_container_width=True)
                
                try:
                    chart_html = default_fig.to_html(include_plotlyjs='cdn')
                    st.download_button(
                        label="📥 Download Chart as HTML",
                        data=chart_html,
                        file_name="default_analytics_chart.html",
                        mime="text/html"
                    )
                except Exception:
                    pass

    else:
        st.info("👈 Please upload a CSV or Excel file from the sidebar to get started.")