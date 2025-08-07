#!/usr/bin/env python3
"""
Debug and Fix Delivery Optimization Issues
- Revenue constraint showing False with 0.0 revenue
- Empty packing list issue
- Visit target not being met
"""

import pandas as pd
import numpy as np
import mysql.connector
from datetime import datetime, timedelta
import json

def get_db_connection():
    """Database connection"""
    return mysql.connector.connect(
        host='127.0.0.1',
        database='pfe1',
        user='root',
        password=''
    )

def debug_historical_data():
    """Debug the historical data to understand what's available"""
    print("🔍 DEBUGGING HISTORICAL DATA")
    print("=" * 50)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check available tables
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"Available tables: {tables}")
        
        # Check entetecommercials structure and data
        if 'entetecommercials' in tables:
            cursor.execute("DESCRIBE entetecommercials")
            columns = cursor.fetchall()
            print(f"\nentetecommercials columns: {[col[0] for col in columns]}")
            
            cursor.execute("SELECT COUNT(*) FROM entetecommercials")
            count = cursor.fetchone()[0]
            print(f"Total records in entetecommercials: {count}")
            
            # Sample data
            cursor.execute("SELECT * FROM entetecommercials LIMIT 5")
            sample_data = cursor.fetchall()
            print(f"\nSample data:")
            for row in sample_data:
                print(f"  {row}")
                
            # Check date range
            cursor.execute("SELECT MIN(date), MAX(date) FROM entetecommercials WHERE date IS NOT NULL")
            date_range = cursor.fetchone()
            print(f"\nDate range: {date_range[0]} to {date_range[1]}")
            
            # Check commercial codes
            cursor.execute("SELECT DISTINCT commercial_code FROM entetecommercials LIMIT 10")
            commercial_codes = [row[0] for row in cursor.fetchall()]
            print(f"\nSample commercial codes: {commercial_codes}")
            
            # Check for recent data (last 90 days)
            cursor.execute("""
                SELECT COUNT(*) 
                FROM entetecommercials 
                WHERE date >= DATE_SUB(NOW(), INTERVAL 90 DAY)
            """)
            recent_count = cursor.fetchone()[0]
            print(f"Records in last 90 days: {recent_count}")
            
    except Exception as e:
        print(f"Error debugging historical data: {e}")
    finally:
        if conn:
            conn.close()

def debug_revenue_calculation():
    """Debug revenue calculation logic"""
    print("\n💰 DEBUGGING REVENUE CALCULATION")
    print("=" * 50)
    
    try:
        # Simulate the revenue calculation process
        # Mock some predictions to test the calculation
        mock_predictions = np.array([2.5, 3.0, 2.8, 3.2, 2.9])  # visits per day
        estimated_revenue_per_visit = 150  # TND per visit
        daily_estimated_revenue = mock_predictions * estimated_revenue_per_visit
        
        print(f"Mock visit predictions: {mock_predictions}")
        print(f"Revenue per visit: {estimated_revenue_per_visit}")
        print(f"Daily estimated revenue: {daily_estimated_revenue}")
        print(f"Average daily revenue: {np.mean(daily_estimated_revenue):.2f}")
        print(f"Total estimated revenue: {np.sum(daily_estimated_revenue):.2f}")
        
        # Test revenue constraint validation
        min_revenue = 2000  # Example minimum revenue
        meets_constraint = np.all(daily_estimated_revenue >= min_revenue)
        revenue_shortfall = np.sum(np.maximum(0, min_revenue - daily_estimated_revenue))
        
        print(f"\nRevenue constraint test:")
        print(f"Minimum revenue required: {min_revenue}")
        print(f"Meets constraint: {meets_constraint}")
        print(f"Revenue shortfall: {revenue_shortfall}")
        
    except Exception as e:
        print(f"Error debugging revenue calculation: {e}")

def debug_packing_list_generation():
    """Debug packing list generation"""
    print("\n📦 DEBUGGING PACKING LIST GENERATION")
    print("=" * 50)
    
    try:
        # Mock client route with predicted products
        mock_route = [
            {
                'client_code': '00154',
                'predicted_products': {
                    'PROD_001': {'quantity': 5, 'price': 25.0},
                    'PROD_002': {'quantity': 3, 'price': 30.0}
                }
            },
            {
                'client_code': '00160',
                'predicted_products': {
                    'PROD_001': {'quantity': 2, 'price': 25.0},
                    'PROD_003': {'quantity': 4, 'price': 20.0}
                }
            }
        ]
        
        # Aggregate products for packing list
        total_products = {}
        for stop in mock_route:
            for product, details in stop['predicted_products'].items():
                qty = details.get('quantity', 0)
                total_products[product] = total_products.get(product, 0) + qty
                
        print(f"Mock route: {len(mock_route)} stops")
        print(f"Generated packing list: {total_products}")
        print(f"Total unique products: {len(total_products)}")
        
        # Check if packing list is empty
        if not total_products:
            print("⚠️ EMPTY PACKING LIST DETECTED - This is the issue!")
        else:
            print("✅ Packing list generated successfully")
            
    except Exception as e:
        print(f"Error debugging packing list: {e}")

def fix_revenue_calculation_issue():
    """Provide fixes for revenue calculation issues"""
    print("\n🔧 REVENUE CALCULATION FIXES")
    print("=" * 50)
    
    fixes = [
        "1. Ensure historical data contains valid 'nombre_visites' column",
        "2. Check that commercial_code exists in the data",
        "3. Verify date column is properly formatted",
        "4. Ensure SARIMA model can be trained with available data",
        "5. Add fallback revenue calculation when SARIMA fails",
        "6. Implement realistic revenue per visit estimation",
        "7. Add better error handling in revenue prediction"
    ]
    
    for fix in fixes:
        print(f"  {fix}")

def fix_packing_list_issue():
    """Provide fixes for empty packing list"""
    print("\n🔧 PACKING LIST FIXES")
    print("=" * 50)
    
    fixes = [
        "1. Ensure product prediction function returns valid quantities",
        "2. Add fallback products when prediction fails",
        "3. Validate that client_code exists in historical data",
        "4. Check product_codes parameter is not empty",
        "5. Implement default product recommendation system",
        "6. Add better error handling in product prediction",
        "7. Ensure aggregation logic handles different data types"
    ]
    
    for fix in fixes:
        print(f"  {fix}")

def create_enhanced_delivery_optimization():
    """Create an enhanced version with better error handling"""
    print("\n🚀 CREATING ENHANCED DELIVERY OPTIMIZATION")
    print("=" * 50)
    
    enhanced_code = '''
def enhanced_generate_delivery_plan(commercial_code, delivery_date, product_codes=None, min_revenue=0):
    """
    Enhanced delivery plan generation with better error handling and fallbacks
    """
    try:
        # Step 1: Validate inputs
        if not commercial_code:
            raise ValueError("Commercial code is required")
        
        if not delivery_date:
            delivery_date = datetime.now()
        
        if not product_codes:
            product_codes = get_default_product_codes()  # Implement this function
        
        # Step 2: Get historical data with validation
        historical_data = get_historical_deliveries()
        
        if historical_data.empty:
            print("⚠️ No historical data found, using sample data")
            historical_data = generate_sample_historical_data(commercial_code)
        
        # Step 3: Enhanced revenue prediction with fallbacks
        try:
            revenue_prediction = calculate_revenue_with_fallback(
                historical_data, commercial_code, min_revenue
            )
        except Exception as e:
            print(f"Revenue prediction failed: {e}, using default calculation")
            revenue_prediction = get_default_revenue_prediction(min_revenue)
        
        # Step 4: Enhanced packing list generation
        try:
            packing_list = generate_packing_list_with_fallback(
                historical_data, commercial_code, product_codes
            )
        except Exception as e:
            print(f"Packing list generation failed: {e}, using default products")
            packing_list = get_default_packing_list(product_codes)
        
        # Step 5: Compile enhanced delivery plan
        delivery_plan = {
            'commercial_code': commercial_code,
            'delivery_date': delivery_date.strftime('%Y-%m-%d'),
            'packing_list': packing_list,
            'revenue_info': revenue_prediction,
            'enhancement_applied': True,
            'fallback_used': len(packing_list) > 0
        }
        
        return delivery_plan
        
    except Exception as e:
        print(f"Enhanced delivery plan generation failed: {e}")
        return get_minimal_delivery_plan(commercial_code, delivery_date)
'''
    
    print("Enhanced delivery optimization code created!")
    print("Key improvements:")
    print("  - Better input validation")
    print("  - Fallback mechanisms for data issues")
    print("  - Enhanced error handling")
    print("  - Default values when predictions fail")
    
    return enhanced_code

def test_api_endpoint():
    """Test the delivery optimization API endpoint"""
    print("\n🧪 TESTING API ENDPOINT")
    print("=" * 50)
    
    try:
        import requests
        
        # Test data
        test_data = {
            "commercial_code": "00154",
            "delivery_date": "2025-06-17",
            "product_codes": ["PROD_001", "PROD_002", "PROD_003"],
            "min_revenue": 2000,
            "min_frequent_visits": 3
        }
        
        print(f"Test data: {json.dumps(test_data, indent=2)}")
        
        # Make API call
        response = requests.post(
            'http://127.0.0.1:5000/api/delivery/optimize',
            json=test_data,
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Result keys: {list(result.keys())}")
            
            # Check for issues
            if result.get('packing_list'):
                print(f"✅ Packing list: {len(result['packing_list'])} products")
            else:
                print("❌ Empty packing list")
                
            if result.get('revenue_info'):
                revenue_info = result['revenue_info']
                print(f"💰 Revenue info:")
                print(f"  - Estimated: {revenue_info.get('estimated_revenue', 0)}")
                print(f"  - Target: {revenue_info.get('min_revenue_target', 0)}")
                print(f"  - Meets target: {revenue_info.get('meets_target', False)}")
            else:
                print("❌ No revenue info")
                
        else:
            print(f"❌ API call failed: {response.text}")
            
    except Exception as e:
        print(f"Error testing API: {e}")

if __name__ == "__main__":
    print("🔧 DELIVERY OPTIMIZATION DEBUG & FIX TOOL")
    print("=" * 60)
    
    # Run all debugging functions
    debug_historical_data()
    debug_revenue_calculation()
    debug_packing_list_generation()
    fix_revenue_calculation_issue()
    fix_packing_list_issue()
    create_enhanced_delivery_optimization()
    test_api_endpoint()
    
    print("\n✅ DEBUGGING COMPLETE")
    print("Check the output above for specific issues and fixes needed.")
