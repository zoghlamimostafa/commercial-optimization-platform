# Debug script to investigate SARIMA prediction data flow
import pandas as pd
import numpy as np
from sarima_delivery_optimization import EnhancedPredictionSystem, predict_future_visits_sarima, get_commercial_visits
from datetime import datetime, timedelta

def debug_sarima_predictions():
    """Debug the SARIMA prediction pipeline to find why predictions are [0.]"""
    
    print("🔍 DEBUGGING SARIMA PREDICTION PIPELINE")
    print("=" * 50)
    
    # Step 1: Get real data from database
    try:
        print("\n1. FETCHING DATA FROM DATABASE:")
        print("-" * 30)
        
        historical_data = get_commercial_visits(
            date_debut='2024-01-01',
            date_fin='2024-12-31',
            commercial_code='1'
        )
        
        print(f"✓ Data fetched: {len(historical_data)} records")
        print(f"  Columns: {list(historical_data.columns)}")
        print(f"  Date range: {historical_data['date'].min()} to {historical_data['date'].max()}")
        
        # Show sample data structure
        print(f"\n📊 SAMPLE DATA (first 5 rows):")
        print(historical_data.head())
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return
    
    # Step 2: Check if 'nombre_visites' column exists and analyze it
    print(f"\n2. ANALYZING 'nombre_visites' COLUMN:")
    print("-" * 35)
    
    if 'nombre_visites' in historical_data.columns:
        visits_data = historical_data['nombre_visites']
        print(f"✓ Column exists with {len(visits_data)} values")
        print(f"  Data type: {visits_data.dtype}")
        print(f"  Min: {visits_data.min()}, Max: {visits_data.max()}")
        print(f"  Mean: {visits_data.mean():.2f}")
        print(f"  Non-zero values: {(visits_data > 0).sum()}/{len(visits_data)}")
        print(f"  Sample values: {visits_data.head(10).tolist()}")
    else:
        print(f"❌ 'nombre_visites' column not found!")
        print(f"  Available columns: {list(historical_data.columns)}")
        
        # Try to create the column from available data
        if 'quantite' in historical_data.columns:
            print("  Attempting to use 'quantite' as proxy for visits...")
            historical_data['nombre_visites'] = np.where(historical_data['quantite'] > 0, 1, 0)
            print(f"  Created 'nombre_visites' from 'quantite'")
        else:
            print("  No suitable proxy found for visit counts")
            return
    
    # Step 3: Test time series creation
    print(f"\n3. TESTING TIME SERIES CREATION:")
    print("-" * 35)
    
    try:
        commercial_data = historical_data[historical_data['commercial_code'] == '1'].copy()
        print(f"✓ Commercial '1' data: {len(commercial_data)} records")
        
        # Create date range
        date_range = pd.date_range(
            start=commercial_data['date'].min(),
            end=commercial_data['date'].max(),
            freq='D'
        )
        print(f"  Date range created: {len(date_range)} days")
        
        # Create time series
        ts_data = commercial_data.set_index('date')['nombre_visites'].reindex(date_range).fillna(0)
        print(f"  Time series created: {len(ts_data)} values")
        print(f"  TS Min: {ts_data.min()}, Max: {ts_data.max()}, Mean: {ts_data.mean():.2f}")
        print(f"  Sample TS values: {ts_data.head(10).tolist()}")
        
    except Exception as e:
        print(f"❌ Error creating time series: {e}")
        return
    
    # Step 4: Test SARIMA model training
    print(f"\n4. TESTING SARIMA MODEL TRAINING:")
    print("-" * 35)
    
    try:
        from sarima_delivery_optimization import train_sarima_model
        
        print(f"  Training SARIMA model on {len(ts_data)} data points...")
        model = train_sarima_model(ts_data)
        print(f"✓ Model trained successfully")
        print(f"  Model AIC: {model.aic:.2f}")
        print(f"  Model BIC: {model.bic:.2f}")
        
        # Test forecast
        print(f"\n  Testing 7-day forecast...")
        forecast = model.get_forecast(steps=7)
        predicted_mean = forecast.predicted_mean
        print(f"  Forecast values: {predicted_mean.values}")
        print(f"  Min prediction: {predicted_mean.min():.4f}")
        print(f"  Max prediction: {predicted_mean.max():.4f}")
        print(f"  Mean prediction: {predicted_mean.mean():.4f}")
        
    except Exception as e:
        print(f"❌ Error in SARIMA training/forecasting: {e}")
        return
    
    # Step 5: Test full prediction pipeline
    print(f"\n5. TESTING FULL PREDICTION PIPELINE:")
    print("-" * 40)
    
    try:
        predictions = predict_future_visits_sarima(historical_data, days_to_predict=7)
        
        if predictions:
            for commercial, pred in predictions.items():
                print(f"\n  Commercial {commercial}:")
                print(f"    Predictions: {pred['predictions']}")
                print(f"    Stats: {pred['stats']}")
        else:
            print("❌ No predictions generated")
            
    except Exception as e:
        print(f"❌ Error in full prediction pipeline: {e}")
    
    # Step 6: Test enhanced prediction system
    print(f"\n6. TESTING ENHANCED PREDICTION SYSTEM:")
    print("-" * 40)
    
    try:
        eps = EnhancedPredictionSystem(min_revenue=1000)
        enhanced_pred = eps.enhanced_sarima_prediction(historical_data, days_to_predict=7)
        
        if enhanced_pred:
            for commercial, pred in enhanced_pred.items():
                print(f"\n  Enhanced Commercial {commercial}:")
                print(f"    Predictions: {pred['predictions']}")
                print(f"    Stats: {pred['stats']}")
        else:
            print("❌ No enhanced predictions generated")
            
    except Exception as e:
        print(f"❌ Error in enhanced prediction system: {e}")

if __name__ == "__main__":
    debug_sarima_predictions()
