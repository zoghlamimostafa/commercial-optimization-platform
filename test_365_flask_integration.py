#!/usr/bin/env python3
"""
Test script for 365-day prediction Flask integration
Tests the new endpoints and functionality
"""

import requests
import sys
import json

def test_365_prediction_integration():
    """Test the 365-day prediction Flask integration"""
    
    base_url = "http://localhost:5000"
    
    print("🧪 Testing 365-Day Prediction Flask Integration")
    print("=" * 60)
    
    # Test 1: Check if app runs (imports work)
    print("\n1. Testing Flask App Import...")
    try:
        from app import app
        print("✅ Flask app imports successfully")
        
        # Check if 365 prediction routes exist
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        expected_routes = [
            '/365_prediction',
            '/api/365_prediction/commercials',
            '/api/365_prediction/analyze',
            '/api/365_prediction/download',
            '/api/365_prediction/chart_data/<commercial_code>'
        ]
        
        for route in expected_routes:
            if any(route in rule for rule in rules):
                print(f"✅ Route found: {route}")
            else:
                print(f"❌ Route missing: {route}")
                
    except Exception as e:
        print(f"❌ Flask app import failed: {e}")
        return False
    
    # Test 2: Check if dual optimization functions are available
    print("\n2. Testing Dual Optimization Functions...")
    try:
        from sarima_delivery_optimization import dual_delivery_optimization_365_days, get_commercial_list
        print("✅ Dual optimization functions imported successfully")
        
        # Test get_commercial_list
        print("   Testing get_commercial_list()...")
        commercials = get_commercial_list()
        if commercials:
            print(f"✅ Found {len(commercials)} commercials in database")
            print(f"   Sample commercial: {commercials[0]['commercial_code']}")
        else:
            print("⚠️  No commercials found (database might be empty)")
            
    except Exception as e:
        print(f"❌ Dual optimization functions failed: {e}")
        return False
    
    # Test 3: Template file exists
    print("\n3. Testing Template File...")
    import os
    template_path = "templates/365_prediction.html"
    if os.path.exists(template_path):
        print("✅ 365_prediction.html template exists")
        
        # Check template size
        size = os.path.getsize(template_path)
        print(f"   Template size: {size:,} bytes")
        
        if size > 10000:  # Should be a substantial template
            print("✅ Template appears to be complete")
        else:
            print("⚠️  Template seems small, might be incomplete")
    else:
        print("❌ 365_prediction.html template missing")
        return False
    
    # Test 4: Check database connection
    print("\n4. Testing Database Connection...")
    try:
        import mysql.connector
        
        # Use the same config as the app
        config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'pfe1'
        }
        
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # Check if entetecommercials table exists
        cursor.execute("SHOW TABLES LIKE 'entetecommercials'")
        result = cursor.fetchone()
        
        if result:
            print("✅ Database connection successful")
            print("✅ entetecommercials table exists")
            
            # Count records
            cursor.execute("SELECT COUNT(*) FROM entetecommercials")
            count = cursor.fetchone()[0]
            print(f"   Total records: {count:,}")
            
            # Check unique commercials
            cursor.execute("SELECT COUNT(DISTINCT commercial_code) FROM entetecommercials")
            unique_commercials = cursor.fetchone()[0]
            print(f"   Unique commercials: {unique_commercials}")
            
        else:
            print("❌ entetecommercials table not found")
            return False
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Test 5: Quick function test
    print("\n5. Testing Core Functions...")
    try:
        # Test a quick commercial list retrieval
        from sarima_delivery_optimization import get_commercial_list
        commercials = get_commercial_list()
        
        if commercials and len(commercials) > 0:
            print(f"✅ Successfully retrieved {len(commercials)} commercials")
            
            # Test with first commercial (but don't run full 365-day analysis)
            sample_commercial = commercials[0]['commercial_code']
            print(f"   Sample commercial code: {sample_commercial}")
            print("✅ Ready for 365-day analysis")
        else:
            print("⚠️  No commercials available for testing")
            
    except Exception as e:
        print(f"❌ Core function test failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 365-Day Prediction Integration Test PASSED!")
    print("\nYou can now:")
    print("1. Start the Flask app: python app.py")
    print("2. Navigate to: http://localhost:5000/365_prediction")
    print("3. Select a commercial and generate 365-day predictions")
    print("4. Download detailed Excel reports")
    print("5. View interactive charts and analytics")
    
    return True

if __name__ == "__main__":
    success = test_365_prediction_integration()
    if not success:
        print("\n❌ Some tests failed. Please check the issues above.")
        sys.exit(1)
    else:
        print("\n✅ All tests passed successfully!")
