#!/usr/bin/env python3
"""
Prediction Accuracy Diagnostic Script
This script will run diagnostic tests on the forecasting algorithms to identify prediction accuracy issues.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def run_prediction_diagnostics():
    """Run comprehensive diagnostics on prediction algorithms"""
    
    print("=" * 60)
    print("PREDICTION ACCURACY DIAGNOSTIC REPORT")
    print("=" * 60)
    
    # Test 1: Check if core prediction modules can be imported
    print("\n1. TESTING MODULE IMPORTS:")
    print("-" * 30)
    
    try:
        from commercial_visits_analysis import predict_future_visits_sarima, train_sarima_model
        print("✓ Commercial visits SARIMA module imported successfully")
    except Exception as e:
        print(f"✗ Error importing commercial visits SARIMA: {e}")
    
    try:
        from demand_prediction import predict_client_demand, generate_demand_predictions
        print("✓ Demand prediction module imported successfully")
    except Exception as e:
        print(f"✗ Error importing demand prediction: {e}")
    
    try:
        from product_analysis import forecast_sales_for_2025
        print("✓ Product analysis Prophet module imported successfully")
    except Exception as e:
        print(f"✗ Error importing product analysis: {e}")
    
    # Test 2: Generate sample data and test predictions
    print("\n2. TESTING PREDICTION ALGORITHMS WITH SAMPLE DATA:")
    print("-" * 50)
    
    # Create sample historical data
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    sample_data = pd.DataFrame({
        'date': dates,
        'commercial_code': '1',
        'nombre_visites': np.random.poisson(5, len(dates)),  # Realistic visit counts
        'client_code': 'CLIENT001',
        'produit_code': 'PROD001',
        'quantite': np.random.poisson(10, len(dates))  # Realistic quantities
    })
    
    print(f"Created sample dataset with {len(sample_data)} records")
    print(f"Date range: {sample_data['date'].min()} to {sample_data['date'].max()}")
    print(f"Average visits per day: {sample_data['nombre_visites'].mean():.2f}")
    print(f"Average quantity per day: {sample_data['quantite'].mean():.2f}")
    
    # Test 3: SARIMA Predictions for Commercial Visits
    print("\n3. TESTING SARIMA COMMERCIAL VISITS PREDICTIONS:")
    print("-" * 50)
    
    try:
        from commercial_visits_analysis import predict_future_visits_sarima
        
        # Test with sample data
        predictions = predict_future_visits_sarima(sample_data, days_to_predict=30)
        
        if predictions:
            print("✓ SARIMA predictions generated successfully")
            for commercial, pred in predictions.items():
                stats = pred['stats']
                print(f"  Commercial {commercial}:")
                print(f"    - Average predicted visits: {stats['moyenne_visites_predites']:.2f}")
                print(f"    - Min predicted visits: {stats['min_visites_predites']:.2f}")
                print(f"    - Max predicted visits: {stats['max_visites_predites']:.2f}")
                print(f"    - Model AIC: {stats.get('aic', 'N/A')}")
                
                # Check for unrealistic predictions
                if stats['max_visites_predites'] > 50:
                    print(f"    ⚠️  WARNING: Unrealistically high predictions (max: {stats['max_visites_predites']})")
                if stats['min_visites_predites'] < 0:
                    print(f"    ⚠️  WARNING: Negative predictions detected (min: {stats['min_visites_predites']})")
        else:
            print("✗ No SARIMA predictions generated")
            
    except Exception as e:
        print(f"✗ Error in SARIMA predictions: {e}")
    
    # Test 4: Demand Predictions
    print("\n4. TESTING DEMAND PREDICTIONS:")
    print("-" * 35)
    
    try:
        from demand_prediction import predict_client_demand
        
        prediction_date = datetime(2025, 1, 15)
        predicted_qty = predict_client_demand(
            sample_data, 'CLIENT001', 'PROD001', prediction_date
        )
        
        print(f"✓ Demand prediction generated: {predicted_qty} units")
        
        if predicted_qty > 1000:
            print(f"⚠️  WARNING: Unrealistically high demand prediction: {predicted_qty}")
        elif predicted_qty < 0:
            print(f"⚠️  WARNING: Negative demand prediction: {predicted_qty}")
        else:
            print("✓ Demand prediction appears realistic")
            
    except Exception as e:
        print(f"✗ Error in demand predictions: {e}")
    
    # Test 5: Check for Common Issues
    print("\n5. CHECKING FOR COMMON PREDICTION ISSUES:")
    print("-" * 45)
    
    issues_found = []
    
    # Check for data quality issues
    if sample_data['nombre_visites'].std() == 0:
        issues_found.append("Zero variance in visit data")
    
    if sample_data['quantite'].isnull().any():
        issues_found.append("Missing values in quantity data")
    
    # Check for seasonal patterns (should exist for realistic data)
    sample_data['day_of_week'] = sample_data['date'].dt.dayofweek
    weekly_pattern = sample_data.groupby('day_of_week')['nombre_visites'].mean()
    if weekly_pattern.std() < 0.5:
        issues_found.append("Lack of weekly seasonality in visit patterns")
    
    if issues_found:
        print("⚠️  ISSUES DETECTED:")
        for issue in issues_found:
            print(f"    - {issue}")
    else:
        print("✓ No obvious data quality issues detected")
    
    # Test 6: Recommendations
    print("\n6. RECOMMENDATIONS FOR IMPROVING PREDICTION ACCURACY:")
    print("-" * 55)
    
    recommendations = [
        "Add data validation to ensure realistic input ranges",
        "Implement cross-validation for model selection",
        "Add business logic constraints (e.g., max visits per day)",
        "Include seasonal decomposition analysis",
        "Add outlier detection and handling",
        "Implement ensemble methods for more robust predictions",
        "Add confidence intervals with realistic bounds",
        "Include external factors (holidays, weather, etc.)",
        "Implement incremental learning for model updates",
        "Add prediction accuracy monitoring and alerts"
    ]
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i:2d}. {rec}")
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    run_prediction_diagnostics()
