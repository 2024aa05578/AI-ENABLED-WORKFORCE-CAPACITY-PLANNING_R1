# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from engines import WorkforceCapacityEngine

# Initialize system views and configuration
st.set_page_config(page_title="Schneider Electric Workforce AI", layout="wide", page_icon="⚡")

st.title("⚡ AI-Enabled Workforce & Capacity Planning Engine")
st.markdown("### Schneider Electric India Services Automation — Capstone Analytics Interface")
st.caption("Developed by Satish Kumar Pathak (BITS Pilani ID: 2025AA05578)")

# Interactive Sidebar for Operational Variables
st.sidebar.header("🔧 Baseline Operational Parameters")
annual_operational_hours = st.sidebar.slider(
    "Standard Productive Working Hours/Year per Engineer", 
    min_value=1500, max_value=2400, value=2000, step=50
)
attrition_coefficient = st.sidebar.slider(
    "National Structural Attrition Rate Buffer (%)", 
    min_value=0.0, max_value=20.0, value=8.0, step=0.5
) / 100.0

# Document Upload Handlers
st.markdown("---")
col_a, col_b = st.columns(2)
with col_a:
    uploaded_work_file = st.file_uploader("Upload Master Workspace File (CSV Format)", type=['csv'])
with col_b:
    uploaded_project_file = st.file_uploader("Upload Data Center Project Raw File (CSV Format)", type=['csv'])

# Static Growth Mapping Dictionary matching your workbook structure
growth_matrix = {
    'SP UPS': {'North': 0.20, 'West': 0.35, 'South': 0.22, 'East': 0.15},
    'SP Cooling': {'North': 0.20, 'West': 0.35, 'South': 0.22, 'East': 0.15},
    'Power Products': {'North': 0.15, 'West': 0.30, 'South': 0.20, 'East': 0.15},
    'Power System': {'North': 0.15, 'West': 0.30, 'South': 0.20, 'East': 0.20},
    'Industiral Automation': {'North': 0.15, 'West': 0.30, 'South': 0.20, 'East': 0.15}
}

if uploaded_work_file and uploaded_project_file:
    # Initialize Engine pipelines using uploaded file contexts
    engine = WorkforceCapacityEngine(uploaded_work_file, uploaded_project_file)
    
    with st.spinner("Processing optimization matrices..."):
        df_raw_projects = engine.load_clean_data()
        df_proj_demand = engine.extract_project_demand()
        df_optimization = engine.optimize_allocations(growth_matrix, standard_capacity=annual_operational_hours)
    
    # Dashboard KPI Cards
    st.markdown("### 📊 Operational Headcount Summary Metrics")
    kpi1, kpi2, kpi3 = st.columns(3)
    
    total_pm_hours = df_raw_projects['Per Year Hrs required for PM'].sum()
    total_startup_hours = df_raw_projects['Total Starup Man Hrs required'].sum()
    aggregate_se_needed = (total_pm_hours + total_startup_hours) / annual_operational_hours
    
    with kpi1:
        st.metric(label="Aggregated Data Center Pipeline Volume (MINR)", 
                  value=f"{df_raw_projects['Value in MINR'].dropna().sum():,.2f}")
    with kpi2:
        st.metric(label="Total Workload Hours Identified (PM + Startup)", 
                  value=f"{int(total_pm_hours + total_startup_hours):,}")
    with kpi3:
        st.metric(label="Net Data Center Technical Headcount Needed", 
                  value=f"{aggregate_se_needed:.2f} FTE")

    # Layout Data Visualizations
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📊 Regional Load Analytics", "🗺️ Strategic Location Optimization", "📋 Structured Project Datasets"])
    
    with tab1:
        st.subheader("Workload Burden Profiling across Regions & Asset Portfolios")
        fig = px.bar(
            df_proj_demand, 
            x='Region', 
            y='Total Headcount Needed', 
            color='Product Type',
            title="Incremental Field Engineers (FTE) Needed by Tech Domain",
            barmode='group',
            template='plotly_white'
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with tab2:
        st.subheader("AI Optimization Model: Regional Headquarters Location Guidance")
        st.dataframe(df_optimization, use_container_width=True)
        
        # Actionable insight for the South Region hub
        st.info(
            "💡 **Strategic Operational Insight:** The West and North areas show concentrated growth due to large-scale data center projects. "
            "To support these high-demand regions, look into shifting underutilized resources from your primary Bangalore hub."
        )
        
    with tab3:
        st.subheader("Raw Data View (Cleaned Major Project Pipeline Data)")
        st.dataframe(df_raw_projects, use_container_width=True)

else:
    st.warning("⚠️ High-performance execution requires uploading both your operational workspace and project CSV files to begin data aggregation.")
    
    # Instantiating User Experience Walkthrough Guidance
    with st.expander("📌 Project Documentation & File Mapping Schema Help"):
        st.markdown("""
        ### Document Mapping Alignment Manual:
        Ensure that your inputs match the structured columns used in your manual planning spreadsheets:
        1. **Workspace CSV Header Maps:** Must include row classifications matching `Active Install Base`, `Work Orders`, and product definitions.
        2. **Project Raw Column Maps:** Processes structural columns such as `Region`, `Product Type`, `Per Year Hrs required for PM`, and `Total Starup Man Hrs required`.
        """)
