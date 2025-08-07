"""
Comprehensive test of the seasonal pattern enhancement integration
Tests the enhanced SARIMA forecasting with seasonal adjustments
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_realistic_test_data():
    """Create realistic test data with clear seasonal patterns"""
    
    print("📊 CREATING REALISTIC TEST DATA")
    print("=" * 50)
    
    # Generate 18 months of daily data
    dates = pd.date_range(start='2023-06-01', end='2024-12-31', freq='D')
    
    all_data = []
    
    # Create data for 3 different commercials with distinct patterns
    for commercial_id in ['1', '2', '3']:
        print(f"Generating data for commercial {commercial_id}...")
        
        for i, date in enumerate(dates):
            # Base level varies by commercial
            base_levels = {'1': 6, '2': 4, '3': 8}
            base_visits = base_levels[commercial_id]
            
            # Commercial-specific weekly patterns
            day_of_week = date.weekday()
            if commercial_id == '1':
                # Strong weekday pattern, low weekends
                weekly_multipliers = [1.2, 1.4, 1.5, 1.6, 1.3, 0.6, 0.4]
            elif commercial_id == '2':
                # More balanced but still lower weekends
                weekly_multipliers = [1.0, 1.1, 1.2, 1.3, 1.1, 0.8, 0.7]
            else:  # commercial_id == '3'
                # Different pattern - higher on Friday/Saturday
                weekly_multipliers = [0.9, 1.0, 1.1, 1.2, 1.5, 1.4, 0.8]
            
            # Monthly/seasonal patterns
            month = date.month
            if commercial_id == '1':
                # Higher in spring/fall, lower in summer/winter
                monthly_multipliers = [0.8, 0.9, 1.3, 1.2, 1.1, 1.0, 0.7, 0.6, 1.2, 1.1, 1.0, 0.8]
            elif commercial_id == '2':
                # Higher in summer, lower in winter
                monthly_multipliers = [0.7, 0.8, 1.0, 1.1, 1.2, 1.4, 1.5, 1.3, 1.1, 1.0, 0.9, 0.8]
            else:  # commercial_id == '3'
                # Business focused - higher at month ends and Q4
                base_monthly = [0.9, 0.9, 1.0, 1.0, 1.0, 1.0, 0.8, 0.9, 1.1, 1.2, 1.3, 1.4]
                monthly_multipliers = base_monthly
            
            weekly_factor = weekly_multipliers[day_of_week]
            monthly_factor = monthly_multipliers[month - 1]
            
            # Add month-end effect for business-oriented commercial
            month_end_factor = 1.0
            if commercial_id == '3' and date.day >= 25:
                month_end_factor = 1.3
            
            # Holiday effects (reduced activity)
            holiday_factor = 1.0
            if (month == 12 and date.day >= 24) or (month == 1 and date.day <= 2):
                holiday_factor = 0.3  # Christmas/New Year
            elif (month == 8 and 10 <= date.day <= 20):
                holiday_factor = 0.6  # Summer vacation
            elif (month == 7 and date.day == 14):
                holiday_factor = 0.2  # Bastille Day
            
            # Calculate final visits
            visits = base_visits * weekly_factor * monthly_factor * month_end_factor * holiday_factor
            
            # Add some random noise
            noise = np.random.normal(0, 0.3)
            visits = max(0, visits + noise)
            
            # Simulate quantities (correlated with visits but different patterns)
            quantity = visits * np.random.uniform(8, 15) + np.random.normal(0, 2)
            quantity = max(0, quantity)
            
            all_data.append({
                'date': date,
                'commercial_code': commercial_id,
                'nombre_visites': round(visits, 1),
                'quantite': round(quantity, 1),
                'client_code': f'CLIENT_{i % 10 + int(commercial_id) * 10}',
                'net_a_payer': round(quantity * np.random.uniform(50, 150), 2)
            })
    
    df = pd.DataFrame(all_data)
    
    print(f"✓ Generated {len(df)} records")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"   Commercials: {df['commercial_code'].nunique()}")
    print(f"   Average visits per day: {df['nombre_visites'].mean():.2f}")
    print(f"   Average quantity per day: {df['quantite'].mean():.2f}")
    
    # Show sample patterns
    print(f"\n📈 SAMPLE PATTERNS:")
    for commercial in df['commercial_code'].unique():
        commercial_data = df[df['commercial_code'] == commercial]
        print(f"   Commercial {commercial}:")
        print(f"     Avg visits: {commercial_data['nombre_visites'].mean():.2f}")
        print(f"     Visit range: {commercial_data['nombre_visites'].min():.1f} - {commercial_data['nombre_visites'].max():.1f}")
        
        # Show weekly pattern
        weekly_avg = commercial_data.copy()
        weekly_avg['day_of_week'] = pd.to_datetime(weekly_avg['date']).dt.dayofweek
        weekly_pattern = weekly_avg.groupby('day_of_week')['nombre_visites'].mean()
        print(f"     Weekly pattern: {[f'{v:.1f}' for v in weekly_pattern.values]}")
    
    return df


def test_seasonal_enhancement_integration():
    """Test the seasonal enhancement integration with the SARIMA system"""
    
    print("\n🧪 TESTING SEASONAL ENHANCEMENT INTEGRATION")
    print("=" * 60)
    
    try:
        # Import the enhanced SARIMA system
        from sarima_delivery_optimization import (
            enhanced_sarima_prediction_with_seasonality,
            enhanced_predictor
        )
        
        print("✓ Enhanced SARIMA system imported successfully")
        
        # Create test data
        test_data = create_realistic_test_data()
        
        # Test for each commercial
        results = {}
        
        for commercial in ['1', '2', '3']:
            print(f"\n🔬 TESTING COMMERCIAL {commercial}")
            print("-" * 40)
            
            # Test enhanced prediction
            result = enhanced_sarima_prediction_with_seasonality(
                test_data, 
                commercial, 
                forecast_steps=30,
                prediction_type='visits'
            )
            
            if result:
                results[commercial] = result
                
                print(f"✓ Prediction successful for commercial {commercial}")
                print(f"   Quality score: {result['quality_score']:.1f}/100")
                print(f"   Average prediction: {result['summary']['mean_prediction']:.2f}")
                print(f"   Prediction range: {result['summary']['prediction_range']}")
                print(f"   Seasonal adjustments: {'Yes' if result['seasonal_adjustments_applied'] else 'No'}")
                
                # Check for seasonal patterns
                if result['seasonal_info']:
                    print(f"   Seasonal patterns detected: {len(result['seasonal_info'])}")
                    
            else:
                print(f"❌ Prediction failed for commercial {commercial}")
        
        # Summary report
        print(f"\n📋 COMPREHENSIVE TEST SUMMARY")
        print("=" * 45)
        
        successful_predictions = len(results)
        print(f"Successful predictions: {successful_predictions}/3")
        
        if successful_predictions > 0:
            avg_quality = np.mean([r['quality_score'] for r in results.values()])
            print(f"Average quality score: {avg_quality:.1f}/100")
            
            # Check enhancement features
            constraints_applied = sum(1 for r in results.values() if r['constraints_applied'])
            seasonal_applied = sum(1 for r in results.values() if r['seasonal_adjustments_applied'])
            
            print(f"Constraints applied: {constraints_applied}/{successful_predictions}")
            print(f"Seasonal adjustments: {seasonal_applied}/{successful_predictions}")
            
            # Realism check
            print(f"\nRealism Check:")
            for commercial, result in results.items():
                mean_pred = result['summary']['mean_prediction']
                max_pred = result['summary']['max_prediction']
                min_pred = result['summary']['min_prediction']
                
                realistic = 0 <= min_pred <= 25 and 0 <= mean_pred <= 25 and 0 <= max_pred <= 25
                print(f"  Commercial {commercial}: {'✓ Realistic' if realistic else '⚠️ Check needed'} "
                      f"(range: {min_pred:.1f}-{max_pred:.1f})")
            
            print(f"\n🎯 Enhancement Status:")
            if enhanced_predictor.seasonal_enhancement_enabled:
                print("  ✓ Seasonal pattern enhancement: ACTIVE")
                print("  ✓ Business constraints: ACTIVE")
                print("  ✓ Quality scoring: ACTIVE")
            else:
                print("  ⚠️ Seasonal pattern enhancement: INACTIVE")
                
        return results
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_seasonal_pattern_detection():
    """Test the seasonal pattern detection capabilities"""
    
    print(f"\n🎭 TESTING SEASONAL PATTERN DETECTION")
    print("=" * 50)
    
    try:
        from seasonal_pattern_enhancement import SeasonalPatternEnhancer
        
        # Create enhancer
        enhancer = SeasonalPatternEnhancer()
        
        # Create test data
        test_data = create_realistic_test_data()
        
        # Run pattern analysis
        print(f"Running comprehensive pattern analysis...")
        report = enhancer.analyze_all_patterns(test_data)
        
        print(f"\n✅ PATTERN DETECTION RESULTS:")
        print(f"   Commercials analyzed: {report['commercials_analyzed']}")
        print(f"   Strong weekly patterns: {report['patterns_detected']['strong_weekly_patterns']}")
        print(f"   Seasonal patterns: {report['patterns_detected']['seasonal_patterns']}")
        print(f"   Trend patterns: {report['patterns_detected']['trend_patterns']}")
        
        # Test parameter enhancement
        print(f"\n🛠️ PARAMETER ENHANCEMENT TEST:")
        base_params = {'p': 1, 'd': 1, 'q': 1, 'P': 0, 'D': 0, 'Q': 0, 's': 0}
        
        for commercial in ['1', '2', '3']:
            enhanced_params = enhancer.get_enhanced_forecast_params(commercial)
            print(f"   Commercial {commercial}: {enhanced_params}")
        
        return enhancer, report
        
    except Exception as e:
        print(f"❌ Pattern detection test failed: {e}")
        return None, None


def run_comprehensive_test():
    """Run comprehensive test of all seasonal enhancement features"""
    
    print("🚀 COMPREHENSIVE SEASONAL ENHANCEMENT TEST")
    print("=" * 70)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Seasonal pattern detection
    enhancer, pattern_report = test_seasonal_pattern_detection()
    
    # Test 2: Integration test
    prediction_results = test_seasonal_enhancement_integration()
    
    # Final summary
    print(f"\n🏁 FINAL TEST SUMMARY")
    print("=" * 35)
    
    pattern_success = enhancer is not None and pattern_report is not None
    integration_success = prediction_results is not None and len(prediction_results) > 0
    
    print(f"Pattern Detection: {'✅ PASS' if pattern_success else '❌ FAIL'}")
    print(f"Integration Test: {'✅ PASS' if integration_success else '❌ FAIL'}")
    
    if pattern_success and integration_success:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"Seasonal enhancement system is fully operational")
        
        # Performance summary
        if prediction_results:
            avg_quality = np.mean([r['quality_score'] for r in prediction_results.values()])
            realistic_count = sum(1 for r in prediction_results.values() 
                                if 0 <= r['summary']['mean_prediction'] <= 20)
            
            print(f"\nPerformance Metrics:")
            print(f"  Average quality score: {avg_quality:.1f}/100")
            print(f"  Realistic predictions: {realistic_count}/{len(prediction_results)}")
            
        if pattern_report:
            strong_patterns = pattern_report['patterns_detected']['strong_weekly_patterns']
            total_commercials = pattern_report['commercials_analyzed']
            pattern_rate = (strong_patterns / total_commercials * 100) if total_commercials > 0 else 0
            
            print(f"  Pattern detection rate: {pattern_rate:.1f}%")
            
    else:
        print(f"\n⚠️ SOME TESTS FAILED")
        print(f"Please check the error messages above")
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    run_comprehensive_test()
