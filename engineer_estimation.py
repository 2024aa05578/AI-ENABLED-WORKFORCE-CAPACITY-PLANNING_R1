
import pandas as pd

# Load data

workorders = pd.read_csv('data/historical_workorders.csv')
pipeline = pd.read_csv('data/business_pipeline.csv')

# Business assumptions
AVG_WORKORDERS_PER_ENGINEER = 18
TARGET_UTILIZATION = 80

# Current workload
regional_load = workorders.groupby('Region')['WorkOrders'].mean().reset_index()

# Merge with future business
merged = regional_load.merge(pipeline, on='Region')

# Forecast future demand
merged['ForecastedWorkOrders'] = (
    merged['WorkOrders'] *
    (1 + merged['ExpectedGrowthPercent'] / 100)
)

# Extra boost from Data Center projects
merged['ForecastedWorkOrders'] += merged['DataCenterProjects'] * 25

# Engineer requirement
merged['RequiredEngineers'] = (
    merged['ForecastedWorkOrders'] /
    AVG_WORKORDERS_PER_ENGINEER
)

# Round values
merged['RequiredEngineers'] = merged['RequiredEngineers'].round(0)

print(merged[[
    'Region',
    'ForecastedWorkOrders',
    'RequiredEngineers'
]])
