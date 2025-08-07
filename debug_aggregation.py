# Debug script to investigate and fix the data aggregation issue
import pandas as pd
import numpy as np
from sarima_delivery_optimization import get_commercial_visits

def analyze_data_aggregation():
    """Analyze how data should be properly aggregated for SARIMA"""
    
    print("🔍 ANALYZING DATA AGGREGATION FOR SARIMA")
    print("=" * 50)
    
    # Get raw data
    historical_data = get_commercial_visits(
        date_debut='2024-01-01',
        date_fin='2024-12-31',
        commercial_code='1'
    )
    
    print(f"Raw data: {len(historical_data)} records")
    print(f"Date range: {historical_data['date'].min()} to {historical_data['date'].max()}")
    
    # Convert to date only (remove time)
    historical_data['date_only'] = historical_data['date'].dt.date
    
    # Group by date to see daily visit patterns
    daily_aggregation = historical_data.groupby('date_only').agg({
        'nombre_visites': 'sum',  # Total visits per day
        'chiffre_affaires': 'sum'  # Total revenue per day
    }).reset_index()
    
    print(f"\n📊 DAILY AGGREGATION:")
    print(f"  Unique days with visits: {len(daily_aggregation)}")
    print(f"  Max visits per day: {daily_aggregation['nombre_visites'].max()}")
    print(f"  Min visits per day: {daily_aggregation['nombre_visites'].min()}")
    print(f"  Average visits per day: {daily_aggregation['nombre_visites'].mean():.2f}")
    
    print(f"\n📈 SAMPLE DAILY DATA:")
    print(daily_aggregation.head(10))
    
    # Check data distribution
    visit_distribution = daily_aggregation['nombre_visites'].value_counts().sort_index()
    print(f"\n📊 VISIT DISTRIBUTION (visits per day):")
    print(visit_distribution.head(10))
    
    # Create proper time series for SARIMA
    print(f"\n🔧 CREATING PROPER TIME SERIES:")
    
    # Create full date range
    start_date = daily_aggregation['date_only'].min()
    end_date = daily_aggregation['date_only'].max()
    
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    print(f"  Full date range: {len(date_range)} days")
    
    # Create complete time series
    daily_aggregation['date_only'] = pd.to_datetime(daily_aggregation['date_only'])
    ts_complete = daily_aggregation.set_index('date_only')['nombre_visites'].reindex(date_range, fill_value=0)
    
    print(f"  Complete time series: {len(ts_complete)} days")
    print(f"  Non-zero days: {(ts_complete > 0).sum()}")
    print(f"  Zero days: {(ts_complete == 0).sum()}")
    print(f"  Max visits: {ts_complete.max()}")
    print(f"  Mean visits: {ts_complete.mean():.2f}")
    
    print(f"\n📊 SAMPLE TIME SERIES VALUES:")
    print(f"First 20 days: {ts_complete.head(20).tolist()}")
    
    # Test SARIMA with proper data
    print(f"\n🧪 TESTING SARIMA WITH PROPER DATA:")
    try:
        from sarima_delivery_optimization import train_sarima_model
        
        # Use a subset of data that has reasonable variation
        model = train_sarima_model(ts_complete)
        
        # Test forecast
        forecast = model.get_forecast(steps=7)
        predicted_mean = forecast.predicted_mean
        
        print(f"  SARIMA predictions: {predicted_mean.values}")
        print(f"  Min: {predicted_mean.min():.4f}, Max: {predicted_mean.max():.4f}")
        print(f"  Mean: {predicted_mean.mean():.4f}")
        
    except Exception as e:
        print(f"  ❌ Error in SARIMA: {e}")

if __name__ == "__main__":
    analyze_data_aggregation()
