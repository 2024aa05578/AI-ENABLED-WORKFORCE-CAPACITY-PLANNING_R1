import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import io
import base64

# --- STREAMLIT CONFIGURATION ---
st.set_page_config(
    page_title="AI-Enabled Workforce & Capacity Planner",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INLINE DESIGN STYLING ---
st.markdown("""
    <style>
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .main-title {
        color: #1E3A8A;
        font-weight: 700;
    }
    </style>
""", unsafe_with_html=True)


# --- DATA LOADING & GITHUB INTEGRATION LAYER ---
@st.cache_data(show_spinner=False)
def load_mock_data():
    """Generates fallback baseline datasets structured exactly like the user's manual simulation files."""
    products = ['UPS', 'Cooling', 'Power Products', 'Power System', 'Industrial Automation']
    regions = ['North', 'West', 'South', 'East']
    
    # 1. Replicating the Work File Structure
    rows = []
    for prod in products:
        for reg in regions:
            # Set baseline scale variations
            base_val = 5000 if prod == 'UPS' else (3500 if prod == 'Cooling' else 500)
            rows.append({
                'Product': prod, 'Region': reg, 'Metric': 'Active Install Base',
                '2023': base_val, '2024': int(base_val * 1.08), '2025': int(base_val * 1.15)
            })
            rows.append({
                'Product': prod, 'Region': reg, 'Metric': 'Work Orders Repair/PM',
                '2023': base_val * 2, '2024': int(base_val * 2.1), '2025': int(base_val * 2.2)
            })
            rows.append({
                'Product': prod, 'Region': reg, 'Metric': 'Work Orders StartUp',
                '2023': base_val // 4, '2024': int(base_val // 3.8), '2025': int(base_val // 3.5)
            })
            rows.append({
                'Product': prod, 'Region': reg, 'Metric': 'Current SR Count',
                '2023': base_val // 200, '2024': int(base_val // 180), '2025': int(base_val // 160)
            })
    work_df = pd.DataFrame(rows)
    
    # 2. Replicating the Data Center Project pipeline
    dc_data = [
        {"Customer": "RIL AI DC", "Region": "West", "Project Type": "Cooling", "Qty": 80, "Per Year Hrs required for PM": 2880, "Startup Hours": 4800},
        {"Customer": "RIL AI DC", "Region": "West", "Project Type": "UPS", "Qty": 40, "Per Year Hrs required for PM": 640, "Startup Hours": 1600},
        {"Customer": "Google India", "Region": "South", "Project Type": "Cooling", "Qty": 120, "Per Year Hrs required for PM": 4320, "Startup Hours": 7200},
        {"Customer": "PDG-DC4", "Region": "West", "Project Type": "Cooling", "Qty": 96, "Per Year Hrs required for PM": 3456, "Startup Hours": 5760},
        {"Customer": "Capital Land", "Region": "North", "Project Type": "UPS", "Qty": 45, "Per Year Hrs required for PM": 720, "Startup Hours": 1800},
        {"Customer": "Equinix MB 3.2", "Region": "West", "Project Type": "Cooling", "Qty": 104, "Per Year Hrs required for PM": 3744, "Startup Hours": 6240}
    ]
    projects_df = pd.DataFrame(dc_data)
    return work_df, projects_df


def fetch_from_github(token, repo, branch, filepath):
    """Fetches CSV tables directly from a private or public target GitHub repository."""
    url = f"https://raw.githubusercontent.com/{repo}/{branch}/{filepath}"
    headers = {"Authorization": f"token {token}"} if token else {}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return pd.read_csv(io.StringIO(response.text))
        else:
            st.error(f"GitHub Error ({response.status_code}): Unable to find '{filepath}'")
            return None
    except Exception as e:
        st.error(f"Connection Failed: {e}")
        return None


def commit_to_github(token, repo, branch, filepath, dataframe, message="Update capacity forecast scenario"):
    """Saves planned metrics back into the GitHub backend via the GitHub Contents API."""
    url = f"https://api.github.com/repos/{repo}/contents/{filepath}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Check if the target file already exists to retrieve its commit sha
    res = requests.get(url, headers=headers)
    sha = res.json().get("sha") if res.status_code == 200 else None
    
    csv_content = dataframe.to_csv(index=False)
    encoded_content = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
    
    payload = {
        "message": message,
        "content": encoded_content,
        "branch": branch
    }
    if sha:
        payload["sha"] = sha
        
    put_res = requests.put(url, headers=headers, json=payload)
    return put_res.status_code in [200, 201]


# --- SIDEBAR & SIMULATION CONTROLS ---
st.sidebar.title("🛠️ Configuration Center")

# Global Capacity Sliders
st.sidebar.subheader("Capacity Coefficients")
hours_per_sr = st.sidebar.slider("Productive Hours / Engineer / Year", 1200, 2400, 1800, 50)
attrition_rate = st.sidebar.slider("Expected Attrition Rate (%)", 0.0, 25.0, 8.0, 0.5) / 100.0

# Dynamic Growth Modifiers
st.sidebar.subheader("Regional BAU Growth Multipliers")
growth_modifiers = {}
for r in ['North', 'West', 'South', 'East']:
    growth_modifiers[r] = st.sidebar.slider(f"{r} Region Baseline Growth factor", 0.5, 2.0, 1.0, 0.05)

# GitHub Backend Configurations
st.sidebar.subheader("🔒 GitHub Backend Link")
use_github = st.sidebar.checkbox("Link live GitHub Repository", value=False)
gh_token = st.sidebar.text_input("GitHub Personal Access Token", type="password")
gh_repo = st.sidebar.text_input("Repository (User/Repo-Name)", placeholder="e.g., bits-user/wfp-project")
gh_branch = st.sidebar.text_input("Branch Name", value="main")

# Load baseline operational files
work_df, projects_df = load_mock_data()
if use_github and gh_repo:
    with st.spinner("Synchronizing data arrays with GitHub repository..."):
        gh_work = fetch_from_github(gh_token, gh_repo, gh_branch, "Work_File.csv")
        gh_proj = fetch_from_github(gh_token, gh_repo, gh_branch, "Major_Projects.csv")
        if gh_work is not None and gh_proj is not None:
            work_df, projects_df = gh_work, gh_proj
            st.sidebar.success("Successfully synchronized data with GitHub repository!")


# --- MAIN APPLICATION WORKSPACE ---
st.title("📊 AI-Enabled Workforce & Capacity Planning Framework")
st.markdown("### BITS Pilani M.Tech Capstone Project — Service Operations Capacity Optimization Cockpit")

tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Executive Forecasting Dashboard", 
    "🤖 AI Baseline Projections (BAU)", 
    "🏢 Data Center Surge Assessment", 
    "💾 Scenario Synchronization & Commit"
])

# --- TAB 1: EXECUTIVE FORECASTING DASHBOARD ---
with tab1:
    st.subheader("2026 Resource Optimization Framework")
    
    # 1. AI-Powered BAU Core Calculations
    forecast_rows = []
    unique_combinations = work_df[['Product', 'Region']].drop_duplicates()
    
    for _, row in unique_combinations.iterrows():
        p, r = row['Product'], row['Region']
        
        # Calculate trend slope via Linear Regression modeling across historical years (2023-2025)
        sub = work_df[(work_df['Product'] == p) & (work_df['Region'] == r) & (work_df['Metric'] == 'Work Orders Repair/PM')]
        if not sub.empty:
            y_hist = np.array([sub['2023'].values[0], sub['2024'].values[0], sub['2025'].values[0]])
            x_hist = np.array([2023, 2024, 2025])
            slope, intercept = np.polyfit(x_hist, y_hist, 1)
            
            # Predict baseline BAU work volume for 2026 adjusted by regional growth modifiers
            predicted_bau_2026 = max(0, int((slope * 2026 + intercept) * growth_modifiers[r]))
            
            # Fetch current headcount from latest baseline period (2025)
            curr_sr_sub = work_df[(work_df['Product'] == p) & (work_df['Region'] == r) & (work_df['Metric'] == 'Current SR Count')]
            current_srs = curr_sr_sub['2025'].values[0] if not curr_sr_sub.empty else 0
            
            forecast_rows.append({
                'Product': p, 'Region': r, 'Current SRs': current_srs, 
                'Predicted BAU Work Orders': predicted_bau_2026
            })
            
    base_forecast_df = pd.DataFrame(forecast_rows)
    
    # Calibrate baseline engineer capacity values (historical work orders handled per active SR)
    base_forecast_df['Historical Efficiency Ratio'] = base_forecast_df['Predicted BAU Work Orders'] / (base_forecast_df['Current SRs'] + 1)
    base_forecast_df['BAU SR Demand'] = base_forecast_df['Predicted BAU Work Orders'] / base_forecast_df['Historical Efficiency Ratio']
    
    # 2. Integrate Project Surge Adjustments
    # Compute bottom-up resource demand values from the pipeline of major projects
    projects_df['Total Calculated Hours'] = projects_df['Per Year Hrs required for PM'] + projects_df['Startup Hours']
    projects_df['Surge SR Demand'] = projects_df['Total Calculated Hours'] / hours_per_sr
    
    project_summary = projects_df.groupby(['Project Type', 'Region'])['Surge SR Demand'].sum().reset_index()
    project_summary.rename(columns={'Project Type': 'Product'}, inplace=True)
    
    # Consolidate baseline business demand and project shock demand
    consolidated_df = pd.merge(base_forecast_df, project_summary, on=['Product', 'Region'], how='left').fillna(0)
    consolidated_df['Total Target SR Capacity'] = consolidated_df['BAU SR Demand'] + consolidated_df['Surge SR Demand']
    
    # Factor in organizational attrition risk formulas
    consolidated_df['Gross Required SRs'] = np.ceil(consolidated_df['Total Target SR Capacity'] / (1 - attrition_rate)).astype(int)
    consolidated_df['Net Recruitment Requirement'] = consolidated_df['Gross Required SRs'] - consolidated_df['Current SRs']
    consolidated_df['Net Recruitment Requirement'] = consolidated_df['Net Recruitment Requirement'].apply(lambda x: max(0, x))

    # Top-Level KPIs Dashboard
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f"<div class='metric-card'><h4>Active Capacity (2025)</h4><h2>{consolidated_df['Current SRs'].sum()} SRs</h2></div>", unsafe_with_html=True)
    with kpi2:
        st.markdown(f"<div class='metric-card'><h4>BAU Operational Target</h4><h2>{int(consolidated_df['BAU SR Demand'].sum())} SRs</h2></div>", unsafe_with_html=True)
    with kpi3:
        st.markdown(f"<div class='metric-card'><h4>Project Shock Requirement</h4><h2>{int(consolidated_df['Surge SR Demand'].sum())} SRs</h2></div>", unsafe_with_html=True)
    with kpi4:
        st.markdown(f"<div class='metric-card'><h4>Gross Hiring Mandate</h4><h2>{consolidated_df['Net Recruitment Requirement'].sum()} Engineers</h2></div>", unsafe_with_html=True)

    # Performance Visualization Panels
    st.markdown("---")
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Resource Deficit Assessment by Segment")
        fig_prod = px.bar(
            consolidated_df.groupby('Product')[['Current SRs', 'Gross Required SRs', 'Net Recruitment Requirement']].sum().reset_index(),
            x='Product', y=['Current SRs', 'Gross Required SRs'], barmode='group',
            title="Current Headcount vs Gross 2026 Demand",
            color_discrete_sequence=['#4F46E5', '#EF4444']
        )
        st.plotly_chart(fig_prod, use_container_width=True)
        
    with c2:
        st.subheader("Geographic Allocation Profiling")
        fig_reg = px.pie(
            consolidated_df.groupby('Region')['Net Recruitment Requirement'].sum().reset_index(),
            values='Net Recruitment Requirement', names='Region', hole=0.4,
            title='Net New Hiring Allocation Across Regions',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_reg, use_container_width=True)


# --- TAB 2: AI BASELINE PROJECTIONS (BAU) ---
with tab2:
    st.subheader("Statistical Core: BAU Historical Trends & Trend Regressions")
    st.markdown("This model maps historical demand metrics across sequential standard operational horizons (2023-2025) to derive standard baseline volume trends.")
    
    selected_prod = st.selectbox("Select Target Product Line for Deep-Dive Analysis:", work_df['Product'].unique())
    sub_wf = work_df[(work_df['Product'] == selected_prod) & (work_df['Metric'] == 'Work Orders Repair/PM')]
    
    melted_wf = sub_wf.melt(id_vars=['Product', 'Region', 'Metric'], value_vars=['2023', '2024', '2025'],
                            var_name='Year', value_name='Work Order Count')
    
    fig_trend = px.line(
        melted_wf, x='Year', y='Work Order Count', color='Region', markers=True,
        title=f"Historical Baseline Growth Vectors - {selected_prod} Segment",
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # Detailed Data Reference Table
    st.dataframe(sub_wf, use_container_width=True)


# --- TAB 3: DATA CENTER SURGE ASSESSMENT ---
with tab3:
    st.subheader("Deterministic Capacity Engine: Project-Driven Surge")
    st.markdown("Unlike traditional BAU forecasting models, incoming localized data center deployments introduce sudden structural demand shifts. Use this panel to audit or selectively factor in individual infrastructure developments.")
    
    # Interactive filtering framework for active pipeline projects
    search_query = st.text_input("Filter Pipeline Projects by Customer Name:", "")
    filtered_proj = projects_df.copy()
    if search_query:
        filtered_proj = filtered_proj[filtered_proj['Customer'].str.contains(search_query, case=False)]
        
    st.markdown("#### Incoming Project Allocation Pipeline")
    st.dataframe(filtered_proj.style.format({'Surge SR Demand': '{:.2f}', 'Total Calculated Hours': '{:,.0f}'}), use_container_width=True)
    
    # Project Workload Breakdown Charts
    fig_dc_breakdown = px.bar(
        filtered_proj.groupby('Project Type')[['Per Year Hrs required for PM', 'Startup Hours']].sum().reset_index(),
        x='Project Type', y=['Per Year Hrs required for PM', 'Startup Hours'],
        title="Incremental Labor Hours Induced by Data Center Deployments",
        labels={'value': 'Total Hours Required', 'Project Type': 'Product Domain'},
        barmode='stack'
    )
    st.plotly_chart(fig_dc_breakdown, use_container_width=True)


# --- TAB 4: SCENARIO SYNCHRONIZATION & COMMIT ---
with tab4:
    st.subheader("Scenario Administration Cockpit")
    st.markdown("Export simulation configurations, model weights, and gross output results to establish clear version-controlled audit trails.")
    
    st.markdown("#### Preview of Exportable Simulation State")
    scenario_export_df = consolidated_df[['Product', 'Region', 'Current SRs', 'Predicted BAU Work Orders', 'BAU SR Demand', 'Surge SR Demand', 'Gross Required SRs', 'Net Recruitment Requirement']].copy()
    st.dataframe(scenario_export_df.style.format({'BAU SR Demand': '{:.2f}', 'Surge SR Demand': '{:.2f}'}), use_container_width=True)
    
    st.markdown("---")
    st.markdown("#### Push Configuration State to GitHub Backend")
    
    commit_filename = st.text_input("Target Sub-folder Filepath:", value="forecast_outputs/scenario_june_2026.csv")
    commit_msg = st.text_area("Commit Log Message:", value="Automated model execution: Adjusted growth multipliers for hyper-scale data center projects.")
    
    if st.button("🚀 Commit Changes to Repo"):
        if not use_github or not gh_token or not gh_repo:
            st.warning("Action Required: Please enable the 'Link live GitHub Repository' configuration and fill in your access credentials in the left sidebar menu.")
        else:
            with st.spinner("Pushing serialized dataframe to target repository branch..."):
                success = commit_to_github(gh_token, gh_repo, gh_branch, commit_filename, scenario_export_df, commit_msg)
                if success:
                    st.success(f"Success! Scenario metrics committed to repo folder: `{commit_filename}` on branch `{gh_branch}`.")
                else:
                    st.error("Write Operation Failed: Please verify repository permissions, API rate limits, or file path definitions.")
