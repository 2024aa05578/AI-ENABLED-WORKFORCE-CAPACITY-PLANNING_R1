
import pandas as pd
from prophet import Prophet
import joblib

# Load historical data

df = pd.read_csv('historical_workorders.csv')

# Prepare data for Prophet
forecast_df = df.groupby('Date')['WorkOrders'].sum().reset_index()
forecast_df.columns = ['ds', 'y']

# Build forecasting model
model = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=False
)

model.fit(forecast_df)

# Future prediction
future = model.make_future_dataframe(periods=180)
forecast = model.predict(future)

# Save model
joblib.dump(model, 'models/forecast_model.pkl')

print(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail())
