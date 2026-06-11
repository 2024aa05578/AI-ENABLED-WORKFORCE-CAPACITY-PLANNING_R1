import streamlit as st
import pandas as pd
import numpy as np
import datetime
from sklearn.linear_model import LinearRegression
import plotly.express as px
import plotly.graph_objects as go
Bash
pip install streamlit pandas numpy scikit-learn plotly

# -------------------------------------------------------------------------
# 1. PAGE SETUP & CONFIGURATION
# -------------------------------------------------------------------------
st.set_page_config(
    page_title="Schneider Electric AI Workforce Planner",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Schneider Electric Brand Vibe (Eco-Green accents)
st.markdown("""
    <style>
    .main-title { font-size:32px; font-weight:bold; color:#3DCD58; margin-bottom:5px; }
    .subtitle { font-size:16px; color:#555555; margin-bottom:25px; }
    .metric-box { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid #3DCD58; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">AI-Enabled Workforce & Capacity Planning</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">M.Tech Final Semester Project - Schneider Electric India Operations</div>', unsafe_allow_html=True)
st.sidebar.image("https://www.se.com/assets/images/logo/schneider-electric-logo.svg", width=180)
st.sidebar.markdown("## Control Panel")

# -------------------------------------------------------------------------
# 2. DATA LAYER (MOCK DATA GENERATION / IN-MEMORY DATABASE)
# -------------------------------------------------------------------------
@st.cache_data
def generate_historical_data():
    """Generates 36 months of historical workload, Installed Base (IB) data, and DC impacts."""
    dates = pd.date_range(start="2023-01-01", end="2026-05-01", freq="MS")
    np.random.seed(42)
    
    # Core variables
    bau_tickets = [150 + i*2 + np.random.randint(-15, 15) for i in range(len(dates))]
    dc_tickets = [10 + int(i**1.5) + np.random.randint(-5, 5) for i in range(len(dates))]
    installed_base_mw = [500 + i*15 for i in range(len(dates))]
    
    df = pd.DataFrame({
        "Month": dates,
        "BAU_Workload": bau_tickets,
        "DataCenter_Workload": dc_tickets,
        "Installed_Base_MW": installed_base_mw
    })
    df["Total_Workload"] = df["BAU_Workload"] + df["DataCenter_Workload"]
    return df

hist_df = generate_historical_data()

# Current Workforce Data Matrix
initial_workforce = pd.DataFrame([
    {"Location": "Bangalore", "Current_Engineers": 14, "Avg_Utilization": 0.88, "Skills": "DC Expert"},
    {"Location": "Chennai", "Current_Engineers": 10, "Avg_Utilization": 0.72, "Skills": "Industrial Automation"},
    {"Location": "Hyderabad", "Current_Engineers": 8, "Avg_Utilization": 0.65, "Skills": "Power Management"},
    {"Location": "Mumbai", "Current_Engineers": 12, "Avg_Utilization": 0.82, "Skills": "DC Expert"},
    {"Location": "Delhi NCR", "Current_Engineers": 11, "Avg_Utilization": 0.78, "Skills": "Power Management"}
])

# Initialize session states to track live adjustments
if "workforce_db" not in st.session_state:
    st.session_state.workforce_db = initial_workforce.copy()

# -------------------------------------------------------------------------
# 3. SIDEBAR CONTROLS & BUSINESS INPUTS
# -------------------------------------------------------------------------
st.sidebar.header("Scenario Constraints")
capacity_per_engineer = st.sidebar.slider(
    "Engineer Capacity (Tickets/Month)", 
    min_value=10, max_value=30, value=15, step=1
)
dc_growth_multiplier = st.sidebar.slider(
    "Data Center Demand Multiplier (Market Surge)", 
    min_value=1.0, max_value=3.0, value=1.5, step=0.1
)
forecast_horizon = st.sidebar.selectbox("Forecast Window", [6, 12, 18, 24], index=1)

# -------------------------------------------------------------------------
# 4. PREDICTIVE ENGINE (AI MODELING)
# -------------------------------------------------------------------------
# Prepare features for simple regression (Trend tracking over time indices)
hist_df['Time_Index'] = np.arange(len(hist_df))

X = hist_df[['Time_Index']]
y_bau = hist_df['BAU_Workload']
y_dc = hist_df['DataCenter_Workload']

# Fit AI/Regression models
model_bau = LinearRegression().fit(X, y_bau)
model_dc = LinearRegression().fit(X, y_dc)

# Future Forecasting
future_indices = np.arange(len(hist_df), len(hist_df) + forecast_horizon)
future_dates = pd.date_range(
    start=hist_df['Month'].max() + pd.DateOffset(months=1), 
    periods=forecast_horizon, freq="MS"
)

pred_bau = model_bau.predict(future_indices.reshape(-1, 1))
pred_dc = model_dc.predict(future_indices.reshape(-1, 1)) * dc_growth_multiplier

forecast_df = pd.DataFrame({
    "Month": future_dates,
    "Predicted_BAU": np.maximum(0, pred_bau),
    "Predicted_DC": np.maximum(0, pred_dc)
})
forecast_df["Predicted_Total_Workload"] = forecast_df["Predicted_BAU"] + forecast_df["Predicted_DC"]
forecast_df["Required_Workforce"] = np.ceil(forecast_df["Predicted_Total_Workload"] / capacity_per_engineer).astype(int)

# -------------------------------------------------------------------------
# 5. TABS INTERFACE (UX Workflow)
# -------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Executive Dashboard", 
    "📈 Demand Forecasting Engine", 
    "🎯 Resource Optimization", 
    "⚙️ Workforce Database"
])

# --- TAB 1: EXECUTIVE DASHBOARD ---
with tab1:
    st.subheader("Operations Overview")
    
    # KPIs Top Rows
    c1, c2, c3, c4 = st.columns(4)
    total_current_staff = st.session_state.workforce_db["Current_Engineers"].sum()
    avg_system_util = st.session_state.workforce_db["Avg_Utilization"].mean() * 100
    peak_future_staff = forecast_df["Required_Workforce"].max()
    hiring_gap = max(0, peak_future_staff - total_current_staff)
    
    with c1:
        st.markdown(f"<div class='metric-box'><b>Current Active Engineers</b><h2>{total_current_staff}</h2></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-box'><b>Average System Utilization</b><h2>{avg_system_util:.1f}%</h2></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='metric-box'><b>Peak Required Engineers</b><h2>{peak_future_staff}</h2></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='metric-box'><b>Net Resource Gap</b><h2>{hiring_gap} Engineers</h2></div>", unsafe_allow_html=True)
        
    st.write("")
    
    # Primary Dashboard Visualization
    fig_overview = go.Figure()
    fig_overview.add_trace(go.Scatter(x=hist_df['Month'], y=hist_df['Total_Workload'], name='Historical Workload', line=dict(color='#1f77b4', width=3)))
    fig_overview.add_trace(go.Scatter(x=forecast_df['Month'], y=forecast_df['Predicted_Total_Workload'], name='AI Forecasted Workload', line=dict(color='#3DCD58', width=3, dash='dash')))
    
    fig_overview.update_layout(
        title="Consolidated Workload Lifecycle (Historical vs Prediction Window)",
        xaxis_title="Timeline", yaxis_title="Monthly Tickets / Incidents",
        legend_placement="top"
    )
    st.plotly_chart(fig_overview, use_container_width=True)

# --- TAB 2: DEMAND FORECASTING ENGINE ---
with tab2:
    st.subheader("Data Center Explosion vs BAU Growth Vectors")
    
    col_f1, col_f2 = st.columns([3, 1])
    
    with col_f1:
        fig_split = go.Figure()
        fig_split.add_trace(go.Bar(x=forecast_df['Month'], y=forecast_df['Predicted_BAU'], name='Forecasted Business-As-Usual', marker_color='#A3E4D7'))
        fig_split.add_trace(go.Bar(x=forecast_df['Month'], y=forecast_df['Predicted_DC'], name='Forecasted Data Center Surge', marker_color='#239B56'))
        fig_split.update_layout(barmode='stack', title="Stacked Demand Growth Vector", xaxis_title="Month", yaxis_title="Load Profile")
        st.plotly_chart(fig_split, use_container_width=True)
        
    with col_f2:
        st.markdown("#### Forecast Summary Data")
        display_forecast = forecast_df.copy()
        display_forecast['Month'] = display_forecast['Month'].dt.strftime('%b %Y')
        st.dataframe(
            display_forecast[['Month', 'Predicted_Total_Workload', 'Required_Workforce']].rename(
                columns={"Predicted_Total_Workload": "Total Load Forecast", "Required_Workforce": "Target Staff Count"}
            ), height=350
        )

# --- TAB 3: RESOURCE OPTIMIZATION ---
with tab3:
    st.subheader("Location Intelligence & Recommendations")
    st.info("Optimization Logic: Allocates hiring metrics and matches resources proportional to current local utilization rates and expected regional Industrial/DC asset clusters.")
    
    # Simple Heuristic Rule-Based Optimizer Engine
    opt_df = st.session_state.workforce_db.copy()
    
    # Calculating delta based on historical utilization stress
    opt_df["Stress_Factor"] = opt_df["Avg_Utilization"] / 0.80  # Target threshold baseline at 80%
    total_stress = opt_df["Stress_Factor"].sum()
    
    # Distribute the gaps based on proportional algorithmic allocation rules
    if hiring_gap > 0:
        opt_df["Recommended_New_Hires"] = np.round((opt_df["Stress_Factor"] / total_stress) * hiring_gap).astype(int)
    else:
        opt_df["Recommended_New_Hires"] = 0
        
    opt_df["Target_Total_Staff"] = opt_df["Current_Engineers"] + opt_df["Recommended_New_Hires"]
    
    # Display Chart
    fig_opt = px.bar(
        opt_df, x="Location", y=["Current_Engineers", "Recommended_New_Hires"],
        title="Optimized Staff Allocation Roadmap per Regional Hub",
        color_discrete_sequence=["#2E4053", "#3DCD58"]
    )
    st.plotly_chart(fig_opt, use_container_width=True)
    
    # Recommendations Summary table
    st.dataframe(opt_df[["Location", "Skills", "Current_Engineers", "Avg_Utilization", "Recommended_New_Hires", "Target_Total_Staff"]], use_container_width=True)

# --- TAB 4: WORKFORCE DATABASE SYSTEM ---
with tab4:
    st.subheader("Manage Enterprise Asset Records")
    st.warning("Any data modification below recalibrates the analytical and deployment recommendation engines instantly across all tabs.")
    
    # Editable Dataframe to update records
    edited_df = st.data_editor(
        st.session_state.workforce_db,
        num_rows="dynamic",
        key="workforce_editor"
    )
    
    if st.button("Commit Database Matrix Changes"):
        st.session_state.workforce_db = edited_df
        st.success("State engine updated successfully!")
        st.rerun()
