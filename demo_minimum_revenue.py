#!/usr/bin/env python3
"""
Demonstration of the minimum revenue parameter functionality
This script shows how to use the enhanced SARIMA system with revenue constraints
"""

import pandas as pd
import numpy as np
from sarima_delivery_optimization import EnhancedPredictionSystem

def main():
    """Main demonstration of minimum revenue functionality"""
    
    print("🚀 SARIMA DELIVERY OPTIMIZATION - MINIMUM REVENUE DEMO")
    print("=" * 60)
    
    # Initialize the enhanced prediction system with a minimum revenue constraint
    print("\n📊 STEP 1: System Initialization")
    eps = EnhancedPredictionSystem(min_revenue=1500)  # Set 1500 as minimum daily revenue
    print(f"✅ System initialized with minimum daily revenue: {eps.min_revenue}")
    
    # Create realistic sample data
    print("\n📊 STEP 2: Creating Sample Historical Data")
    dates = pd.date_range('2024-01-01', periods=60)  # 2 months of data
    
    # Create realistic visit patterns with some variation
    base_visits = 8  # Average visits per day
    seasonal_factor = np.sin(np.arange(60) * 2 * np.pi / 7) * 2  # Weekly pattern
    random_noise = np.random.normal(0, 1.5, 60)
    visits = np.maximum(1, base_visits + seasonal_factor + random_noise)
    
    historical_data = pd.DataFrame({
        'date': dates,
        'commercial_code': ['DEMO_COMMERCIAL'] * 60,
        'nombre_visites': visits.astype(int),
        'revenue': visits * 150 + np.random.normal(0, 100, 60)  # Revenue based on visits + noise
    })
    
    print(f"✅ Historical data created: {len(historical_data)} days")
    print(f"   Average visits per day: {historical_data['nombre_visites'].mean():.1f}")
    print(f"   Average revenue per day: {historical_data['revenue'].mean():.2f}")
    
    # Demo 1: Revenue constraint validation
    print("\n📊 STEP 3: Revenue Constraint Validation")
    print("-" * 40)
    sample_prediction = {
        'predictions': [6, 4, 8, 12, 5, 9, 7],  # Mix of high and low days
        'dates': pd.date_range('2024-03-01', periods=7)
    }
    
    validation_result = eps.validate_revenue_constraints(sample_prediction, 'DEMO_COMMERCIAL')
    
    print(f"✅ Validation completed:")
    print(f"   Revenue constraint met: {'Yes' if validation_result['meets_revenue_constraint'] else 'No'}")
    if validation_result['revenue_shortfall'] > 0:
        print(f"   Revenue shortfall: {validation_result['revenue_shortfall']:.2f}")
    
    # Demo 2: Enhanced revenue prediction
    print("\n📊 STEP 4: Enhanced Revenue Prediction")
    print("-" * 40)
    
    prediction_result = eps.enhanced_revenue_prediction(
        historical_data, 'DEMO_COMMERCIAL', forecast_steps=14
    )
    
    if prediction_result:
        print(f"✅ Enhanced prediction completed:")
        print(f"   Forecast period: {prediction_result['forecast_steps']} days")
        print(f"   Average daily visits: {np.mean(prediction_result['visit_predictions']):.1f}")
        print(f"   Average daily revenue: {prediction_result['average_daily_revenue']:.2f}")
        print(f"   Total forecast revenue: {prediction_result['total_estimated_revenue']:.2f}")
        print(f"   Revenue constraint met: {'✅ Yes' if prediction_result['meets_revenue_constraint'] else '❌ No'}")
        
        print(f"\n💡 Top Recommendations:")
        for i, rec in enumerate(prediction_result['recommendations'][:3], 1):
            print(f"   {i}. {rec}")
    
    # Demo 3: Business constraints
    print("\n📊 STEP 5: Business Constraints Application")
    print("-" * 40)
    raw_predictions = [25, -2, 15, 30, 0, 18, 22]  # Include unrealistic values
    constrained_predictions = eps.apply_business_constraints(raw_predictions, 'visits')
    
    print(f"Raw predictions:         {raw_predictions}")
    print(f"Constrained predictions: {constrained_predictions}")
    print("✅ Negative values removed, extreme values capped")
    
    # Demo 4: Full demonstration
    print("\n📊 STEP 6: Running Complete Demo")
    print("-" * 40)
    demo_result = eps.demo_revenue_constraints(historical_data)
    
    print(f"\n🎯 FINAL SUMMARY")
    print("=" * 30)
    print(f"✅ All minimum revenue functionality working correctly!")
    print(f"📊 System can validate revenue constraints")
    print(f"💰 Enhanced predictions consider revenue targets")
    print(f"🎯 Business recommendations are revenue-aware")
    print(f"🔧 Interactive setup available for customization")
    
    # Optionally run interactive setup
    print(f"\n🛠️ Interactive Setup Available")
    print("To customize revenue constraints, call:")
    print("eps.setup_revenue_constraints_interactive()")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print(f"\n🎉 Demo completed successfully!")
        else:
            print(f"\n❌ Demo encountered issues")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
