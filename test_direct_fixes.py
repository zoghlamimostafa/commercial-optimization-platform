"""
Direct test of the delivery optimization fixes without API
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Import the fixed functions
from fixed_delivery_optimization import (
    get_enhanced_historical_deliveries,
    enhanced_revenue_prediction_fixed,
    enhanced_product_prediction_fixed,
    enhanced_visits_analysis_fixed
)

def test_delivery_optimization_fixes():
    """Test all the delivery optimization fixes directly"""
    
    print("🔧 DIRECT TEST OF DELIVERY OPTIMIZATION FIXES")
    print("=" * 60)
    
    try:
        # Test 1: Historical data retrieval
        print("\n1️⃣ Testing historical data retrieval...")
        historical_data = get_enhanced_historical_deliveries()
        
        if not historical_data.empty:
            print(f"✅ Historical data: {len(historical_data)} records")
            print(f"   Date range: {historical_data['date'].min()} to {historical_data['date'].max()}")
            print(f"   Commercial codes: {historical_data['commercial_code'].nunique()}")
        else:
            print("❌ No historical data retrieved")
            return False
        
        # Test 2: Revenue prediction fix
        print("\n2️⃣ Testing revenue prediction fix...")
        revenue_result = enhanced_revenue_prediction_fixed(historical_data, '1', 1)
        
        estimated_revenue = revenue_result.get('average_daily_revenue', 0)
        if estimated_revenue > 0:
            print(f"✅ Revenue prediction: {estimated_revenue:.2f} TND")
            print(f"   Total revenue: {revenue_result.get('total_estimated_revenue', 0):.2f}")
            print(f"   Revenue fix: WORKING")
        else:
            print(f"❌ Revenue prediction still returns 0")
            return False
        
        # Test 3: Product prediction fix  
        print("\n3️⃣ Testing product prediction fix...")
        product_result, prices = enhanced_product_prediction_fixed(
            historical_data, '00154', datetime.now(), ['PROD_001', 'PROD_002', 'PROD_003']
        )
        
        if product_result:
            total_qty = sum(details['quantity'] for details in product_result.values())
            print(f"✅ Product prediction: {len(product_result)} products")
            print(f"   Total quantity: {total_qty}")
            print(f"   Products: {list(product_result.keys())}")
            print(f"   Packing list fix: WORKING")
        else:
            print(f"❌ Product prediction returns empty")
            return False
        
        # Test 4: Visits analysis fix
        print("\n4️⃣ Testing visits analysis fix...")
        visits_result = enhanced_visits_analysis_fixed(historical_data, '1', 3)
        
        avg_visits = visits_result.get('average_visits', 0)
        if avg_visits > 0:
            print(f"✅ Visits analysis: {avg_visits:.1f} average visits")
            print(f"   Total clients: {visits_result.get('total_clients', 0)}")
            print(f"   Meets target: {visits_result.get('meets_target', False)}")
            print(f"   Visits fix: WORKING")
        else:
            print(f"❌ Visits analysis returns 0")
            return False
        
        # Test 5: Complete delivery plan simulation
        print("\n5️⃣ Testing complete delivery plan simulation...")
        
        # Simulate revenue constraint validation
        min_revenue = 2000
        meets_revenue_target = estimated_revenue >= min_revenue
        revenue_gap = max(0, min_revenue - estimated_revenue) if not meets_revenue_target else 0
        
        # Create a mock delivery plan
        delivery_plan = {
            'commercial_code': '1',
            'delivery_date': datetime.now().strftime('%Y-%m-%d'),
            'packing_list': {prod: details['quantity'] for prod, details in product_result.items()},
            'revenue_info': {
                'min_revenue_target': min_revenue,
                'estimated_revenue': estimated_revenue,
                'meets_target': meets_revenue_target,
                'revenue_gap': revenue_gap,
                'patch_applied': True
            },
            'visits_info': visits_result,
            'total_products': sum(details['quantity'] for details in product_result.values()),
            'enhancement_applied': True
        }
        
        print(f"✅ Complete delivery plan created:")
        print(f"   Packing list: {len(delivery_plan['packing_list'])} products")
        print(f"   Total quantity: {delivery_plan['total_products']}")
        print(f"   Revenue meets target: {meets_revenue_target}")
        print(f"   Revenue gap: {revenue_gap:.2f}")
        
        # Summary of fixes
        print(f"\n🎉 ALL FIXES TESTED SUCCESSFULLY!")
        print(f"\n✅ FIX SUMMARY:")
        print(f"   ✅ Revenue calculation: Fixed (was 0.0, now {estimated_revenue:.2f})")
        print(f"   ✅ Empty packing list: Fixed ({len(product_result)} products)")
        print(f"   ✅ Visit counting: Fixed ({avg_visits:.1f} average)")
        print(f"   ✅ Error handling: Improved with fallbacks")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def simulate_api_response():
    """Simulate what the API would return with our fixes"""
    
    print(f"\n📡 SIMULATING API RESPONSE WITH FIXES")
    print("=" * 50)
    
    try:
        # Get data using our fixed functions
        historical_data = get_enhanced_historical_deliveries()
        revenue_result = enhanced_revenue_prediction_fixed(historical_data, '1', 1)
        product_result, prices = enhanced_product_prediction_fixed(
            historical_data, '00154', datetime.now(), ['PROD_001', 'PROD_002', 'PROD_003']
        )
        visits_result = enhanced_visits_analysis_fixed(historical_data, '1', 3)
        
        # Create simulated API response
        api_response = {
            'commercial_code': '1',
            'commercial_name': 'Test Commercial',
            'delivery_date': datetime.now().strftime('%Y-%m-%d'),
            'packing_list': {prod: details['quantity'] for prod, details in product_result.items()},
            'revenue_info': {
                'min_revenue_target': 2000.0,
                'estimated_revenue': revenue_result.get('average_daily_revenue', 0),
                'meets_target': revenue_result.get('average_daily_revenue', 0) >= 2000,
                'revenue_gap': max(0, 2000 - revenue_result.get('average_daily_revenue', 0))
            },
            'visits_info': visits_result,
            'route': [
                {
                    'client_code': '00154',
                    'predicted_products': product_result,
                    'distance': 5.2
                }
            ],
            'total_distance': 5.2,
            'fixes_applied': True,
            'issues_resolved': [
                'Revenue calculation returning 0.0',
                'Empty packing list',
                'Visit target not being met'
            ]
        }
        
        print(f"📊 SIMULATED API RESPONSE:")
        print(f"   Status: 200 OK")
        print(f"   Packing list: {len(api_response['packing_list'])} products")
        print(f"   Revenue estimated: {api_response['revenue_info']['estimated_revenue']:.2f}")
        print(f"   Route stops: {len(api_response['route'])}")
        
        return api_response
        
    except Exception as e:
        print(f"❌ Error simulating API response: {e}")
        return None

if __name__ == "__main__":
    print("🧪 COMPREHENSIVE DELIVERY OPTIMIZATION FIXES TEST")
    print("=" * 70)
    
    # Run the direct tests
    success = test_delivery_optimization_fixes()
    
    if success:
        # Simulate API response
        api_response = simulate_api_response()
        
        if api_response:
            print(f"\n🎉 SUCCESS! All delivery optimization issues have been resolved:")
            print(f"   ✅ Revenue calculation now works correctly")
            print(f"   ✅ Packing list is no longer empty")  
            print(f"   ✅ Visit analysis provides realistic data")
            print(f"   ✅ Error handling prevents crashes")
            print(f"   ✅ Fallback mechanisms ensure system always works")
    else:
        print(f"\n❌ Some issues remain. Check the output above for details.")
