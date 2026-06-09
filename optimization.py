
import pandas as pd

# Load data

df = pd.read_csv('data/historical_workorders.csv')

# Aggregate by location
location_summary = df.groupby('Location').agg({
    'WorkOrders': 'mean',
    'TravelHours': 'mean',
    'Revenue': 'mean',
    'UtilizationPercent': 'mean'
}).reset_index()

# Recommendation logic

def recommend_location(row):
    if (
        row['WorkOrders'] > 250 and
        row['TravelHours'] > 150 and
        row['UtilizationPercent'] > 85
    ):
        return 'New Hub Recommended'

    elif row['UtilizationPercent'] < 60:
        return 'Resource Redistribution'

    return 'No Action'

location_summary['Recommendation'] = (
    location_summary.apply(recommend_location, axis=1)
)

print(location_summary)
