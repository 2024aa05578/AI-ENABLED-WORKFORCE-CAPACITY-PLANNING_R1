
import pandas as pd

# Load data

df = pd.read_csv('data/historical_workorders.csv')

# Productivity assumptions
AVAILABLE_HOURS_PER_MONTH = 160
AVG_HOURS_PER_WORKORDER = 6

# Calculate utilization

df['RequiredHours'] = df['WorkOrders'] * AVG_HOURS_PER_WORKORDER

df['AvailableHours'] = (
    df['EngineersAvailable'] * AVAILABLE_HOURS_PER_MONTH
)

df['CalculatedUtilization'] = (
    df['RequiredHours'] /
    df['AvailableHours']
) * 100

# Recommendation

def workload_flag(util):
    if util > 90:
        return 'Overloaded'
    elif util < 60:
        return 'Underutilized'
    else:
        return 'Optimal'


df['Status'] = df['CalculatedUtilization'].apply(workload_flag)

print(df[[
    'Location',
    'CalculatedUtilization',
    'Status'
]])
