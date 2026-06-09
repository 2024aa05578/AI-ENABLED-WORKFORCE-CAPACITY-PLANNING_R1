
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title='AI Workforce Planning', layout='wide')

st.title('AI Enabled Workforce & Capacity Planning')

# Load data

df = pd.read_csv('data/historical_workorders.csv')

# KPI Metrics

col1, col2, col3 = st.columns(3)

col1.metric('Total Work Orders', int(df['WorkOrders'].sum()))
col2.metric('Total Engineers', int(df['EngineersAvailable'].sum()))
col3.metric('Average Utilization',
            round(df['UtilizationPercent'].mean(), 2))

# Work order trend

trend = df.groupby('Date')['WorkOrders'].sum().reset_index()

fig = px.line(
    trend,
    x='Date',
    y='WorkOrders',
    title='Work Order Trend'
)

st.plotly_chart(fig, use_container_width=True)

# Regional utilization

util = df.groupby('Region')['UtilizationPercent'].mean().reset_index()

fig2 = px.bar(
    util,
    x='Region',
    y='UtilizationPercent',
    color='UtilizationPercent',
    title='Regional Utilization'
)

st.plotly_chart(fig2, use_container_width=True)
