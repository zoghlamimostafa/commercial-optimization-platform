#!/usr/bin/env python3
"""
Test script for the minimum revenue parameter functionality
"""

import numpy as np
import pandas as pd
from sarima_delivery_optimization import EnhancedPredictionSystem

def test_minimum_revenue_functionality():
    """Test the minimum revenue parameter functionality"""
    
    print("=== Test 1: Initialization with minimum revenue ===")
    eps = EnhancedPredictionSystem(min_revenue=1000)
    print(f"Minimum revenue set to: {eps.min_revenue}")
    
    print("\n=== Test 2: Revenue constraint validation ===")
    sample_predictions = {
        'predictions': [5, 7, 8, 6, 9],
        'dates': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05']
    }
      # Simulate some historical data for context
    sample_historical_data = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=5),
        'commercial_code': ['TEST_COMMERCIAL'] * 5,
        'nombre_visites': [5, 7, 8, 6, 9],
        'visits': [5, 7, 8, 6, 9],
        'revenue': [800, 1200, 1400, 900, 1600]
    })
    
    try:
        validation_result = eps.validate_revenue_constraints(sample_predictions, sample_historical_data)
        print("Validation completed successfully")
        print(f"Revenue compliant days: {validation_result.get('revenue_compliant_days', 'N/A')}")
        print(f"Recommendations: {len(validation_result.get('recommendations', []))} generated")
    except Exception as e:
        print(f"Validation error: {e}")
    
    print("\n=== Test 3: Enhanced revenue prediction ===")
    try:
        enhanced_pred = eps.enhanced_revenue_prediction(sample_historical_data, 'TEST_COMMERCIAL', 30)
        print("Enhanced prediction completed successfully")
        print(f"Predictions adjusted: {enhanced_pred.get('adjusted', False) if enhanced_pred else False}")
        print(f"Quality score: {enhanced_pred.get('quality_score', 'N/A') if enhanced_pred else 'N/A'}")
    except Exception as e:
        print(f"Enhanced prediction error: {e}")
    
    print("\n=== Test 4: Business constraints application ===")
    try:
        constrained_pred = eps.apply_business_constraints(sample_predictions['predictions'])
        print("Business constraints applied successfully")
        print(f"Original predictions: {sample_predictions['predictions']}")
        print(f"Constrained predictions: {constrained_pred}")
    except Exception as e:
        print(f"Business constraints error: {e}")
    
    print("\n=== Test 5: Interactive setup test ===")
    print("Testing interactive setup function availability...")
    if hasattr(eps, 'setup_revenue_constraints_interactive'):
        print("✓ Interactive setup function available")
    else:
        print("✗ Interactive setup function not found")
    
    print("\n=== All tests completed! ===")

if __name__ == "__main__":
    test_minimum_revenue_functionality()
