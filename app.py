
import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.linear_model import LinearRegression
import numpy as np

st.set_page_config(page_title="AI Workforce Planning", layout="wide")

st.title("AI Enabled Workforce & Capacity Planning")

# Load data
df = pd.read_csv('data/historical_workorders.csv')

# Convert date
df['Date'] = pd.to_datetime(df['Date'])

# KPI metrics
col1, col2, col3 = st.columns(3)

col1.metric("Total Work Orders", int(df['WorkOrders'].sum()))
col2.metric("Total Engineers", int(df['EngineersAvailable'].sum()))
col3.metric("Average Utilization",
            round(df['UtilizationPercent'].mean(),2))

# Trend chart
trend = df.groupby('Date')['WorkOrders'].sum().reset_index()

fig = px.line(
    trend,
    x='Date',
    y='WorkOrders',
    markers=True,
    title='Historical Work Order Trend'
)

st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# FUTURE FORECAST
# ---------------------------

st.subheader("Future Work Order Forecast")

trend['MonthIndex'] = np.arange(len(trend))

X = trend[['MonthIndex']]
y = trend['WorkOrders']

model = LinearRegression()
model.fit(X, y)

future_index = np.arange(len(trend), len(trend)+6).reshape(-1,1)

future_predictions = model.predict(future_index)

future_dates = pd.date_range(
    trend['Date'].max(),
    periods=7,
    freq='M'
)[1:]

forecast_df = pd.DataFrame({
    'Date': future_dates,
    'ForecastWorkOrders': future_predictions
})

forecast_fig = px.line(
    forecast_df,
    x='Date',
    y='ForecastWorkOrders',
    markers=True,
    title='6-Month Future Forecast'
)

st.plotly_chart(forecast_fig, use_container_width=True)

# ---------------------------
# UTILIZATION
# ---------------------------

st.subheader("Regional Utilization")

util = df.groupby('Region')['UtilizationPercent'].mean().reset_index()

fig2 = px.bar(
    util,
    x='Region',
    y='UtilizationPercent',
    color='UtilizationPercent',
    title='Regional Utilization'
)

st.plotly_chart(fig2, use_container_width=True)

# ---------------------------
# OPTIMIZATION RECOMMENDATION
# ---------------------------

st.subheader("Location Optimization Recommendations")

location_summary = df.groupby('Location').agg({
    'WorkOrders':'mean',
    'TravelHours':'mean',
    'Revenue':'mean',
    'UtilizationPercent':'mean'
}).reset_index()

def recommendation(row):

    if (
        row['WorkOrders'] > 450 and
        row['UtilizationPercent'] > 90
    ):
        return "Deploy Additional Engineers"

    elif row['TravelHours'] > 250:
        return "Open New Service Hub"

    elif row['UtilizationPercent'] < 70:
        return "Redistribute Resources"

    else:
        return "No Action"

location_summary['Recommendation'] = (
    location_summary.apply(recommendation, axis=1)
)

st.dataframe(location_summary)
