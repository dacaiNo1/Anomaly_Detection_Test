import streamlit as st
import pandas as pd
import plotly.express as px
import boto3
from io import StringIO
from utils.anomaly import run_anomaly_detection
from utils.excel_export import generate_excel_report
from utils.plotting import generate_chart

st.set_page_config(page_title="📊 Anomaly Detection Dashboard", layout="wide")
st.title("📊 Anomaly Detection Dashboard")

# Step 1: File Source
file_source = st.radio("Step 1: Choose File Source", ["Manual Upload", "Load from S3 (Secrets)"], horizontal=True)
df_raw = None

# --- Manual Upload ---
if file_source == "Manual Upload":
    uploaded_file = st.file_uploader("Upload your CSV file", type="csv")
    if uploaded_file:
        st.session_state["file_name"] = uploaded_file.name
        df_raw = pd.read_csv(uploaded_file, header=0)

# --- Load from S3 (using secrets) ---
elif file_source == "Load from S3 (Secrets)":
    bucket_name = st.text_input("S3 Bucket Name", value="hannahtest12345")
    file_key = st.text_input("S3 File Key", value="Anomaly Testing - Amount.csv.csv")

    if st.button("🔄 Load CSV from S3"):
        try:
            s3 = boto3.client(
                's3',
                region_name=st.secrets["aws_region"],
                aws_access_key_id=st.secrets["aws_access_key"],
                aws_secret_access_key=st.secrets["aws_secret_key"]
            )
            response = s3.get_object(Bucket=bucket_name, Key=file_key)
            content = response['Body'].read().decode('utf-8')
            df_raw = pd.read_csv(StringIO(content))
            st.session_state["file_name"] = file_key
            st.success(f"✅ Loaded file: {file_key}")
        except Exception as e:
            st.error(f"Failed to load file from S3: {e}")

# --- Data Preview ---
if df_raw is not None:
    st.subheader("🧾 Data Preview")
    st.dataframe(df_raw, use_container_width=True)

    # Step 2: Isolation Forest Settings
    st.subheader("⚙️ Step 2: Configure Isolation Forest")
    with st.form("isolation_forest_form"):
        n_estimators = st.slider("Number of Trees (n_estimators)", 50, 300, 100)
        contamination = st.slider("Contamination", 0.01, 0.5, 0.05, step=0.01)
        max_samples = st.number_input("Max Samples", min_value=10, max_value=10000, value=64, step=1)
        random_state = st.number_input("Random State", min_value=0, value=42, step=1)
        run_analysis = st.form_submit_button("▶️ Run Anomaly Detection")

    # Step 3: Run Detection
    if run_analysis:
        st.subheader("🧪 Running Anomaly Detection...")
        with st.spinner("Running Isolation Forest... Please wait."):
            df_results, highlight_flags, explanations, dimension_cols = run_anomaly_detection(
                df_raw.copy(), n_estimators, contamination, max_samples, random_state
            )
        st.session_state.df_results = df_results
        st.session_state.highlight_flags = highlight_flags
        st.session_state.explanations = explanations
        st.session_state.dimension_cols = dimension_cols
        st.success("✅ Anomaly Detection Completed")

# --- Results & Chart ---
if "df_results" in st.session_state:
    df_results = st.session_state.df_results

    st.subheader("📌 Anomaly Explanation Breakdown")
    explanation_df = pd.DataFrame({"Explanation": st.session_state.explanations})
    explanation_df["Explanation"].fillna("Normal", inplace=True)
    explanation_counts = explanation_df["Explanation"].value_counts().reset_index()
    explanation_counts.columns = ["Explanation", "Count"]
    total_explanations = explanation_counts["Count"].sum()
    explanation_counts["Percentage"] = (explanation_counts["Count"] / total_explanations * 100).round(1)

    col1, col2 = st.columns(2)
    with col1:
        fig_bar = px.bar(
            explanation_counts,
            x="Explanation",
            y="Count",
            text=explanation_counts["Percentage"].astype(str) + "%",
            title="Frequency of Anomaly Explanations"
        )
        fig_bar.update_traces(textposition="outside", textfont_size=14)
        fig_bar.update_layout(yaxis_title=None, xaxis_title=None)
        st.plotly_chart(fig_bar, use_container_width=True)
    with col2:
        fig_pie = px.pie(
            explanation_counts,
            names="Explanation",
            values="Count",
            title="Anomaly Explanation Breakdown (Pie)"
        )
        fig_pie.update_traces(textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)

    # Step 5: Chart Grouping
    st.subheader("📈 Step 3: Customize Grouping for Chart")
    with st.form("chart_grouping_form"):
        available_cols = list(st.session_state.dimension_cols)
        selected_group_cols = st.multiselect("Select Group By (for Chart)", options=available_cols, default=available_cols[:1])
        top_n = st.number_input("Top X Groups by Count", min_value=1, max_value=100, value=5)
        result_filter = st.selectbox("Filter by Result", ["All", "Anomaly", "Normal", "Insufficient Data"])
        generate_chart_button = st.form_submit_button("📊 Generate Chart")

    if generate_chart_button:
        st.subheader("📊 Anomaly Summary Chart")
        chart_fig = generate_chart(df_results, selected_group_cols, top_n, result_filter)
        st.plotly_chart(chart_fig, use_container_width=True)

    # Step 6: Download
    st.subheader("📥 Step 4: Download Results")
    excel_data = generate_excel_report(
        df_results,
        st.session_state.highlight_flags,
        st.session_state.explanations
    )
    st.download_button("📁 Download Excel Report", excel_data, file_name="anomaly_analysis_output.xlsx", key="excel-download")
