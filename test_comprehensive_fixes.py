#!/usr/bin/env python3
"""
Comprehensive test of the fixed revenue constraints and frequent visits conditions
"""

import requests
import json
from datetime import datetime, timedelta

def test_revenue_and_visits_comprehensive():
    """Test multiple scenarios for revenue and visits conditions"""
    
    base_url = "http://localhost:5000/api/delivery/optimize"
    
    test_scenarios = [
        {
            "name": "Low Revenue, Low Visits",
            "data": {
                'commercial_code': '1',
                'delivery_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'min_revenue': 2000,  # High threshold
                'min_frequent_visits': 5  # High threshold
            }
        },
        {
            "name": "Met Revenue, Low Visits", 
            "data": {
                'commercial_code': '1',
                'delivery_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'min_revenue': 500,   # Low threshold
                'min_frequent_visits': 5  # High threshold
            }
        },
        {
            "name": "Low Revenue, Met Visits",
            "data": {
                'commercial_code': '1',
                'delivery_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'min_revenue': 2000,  # High threshold
                'min_frequent_visits': 1  # Low threshold
            }
        },
        {
            "name": "Both Met",
            "data": {
                'commercial_code': '1',
                'delivery_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'min_revenue': 500,   # Low threshold
                'min_frequent_visits': 1  # Low threshold
            }
        },
        {
            "name": "No Constraints",
            "data": {
                'commercial_code': '1',
                'delivery_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                # No min_revenue or min_frequent_visits
            }
        }
    ]
    
    print("🧪 COMPREHENSIVE REVENUE & VISITS CONDITIONS TEST")
    print("=" * 60)
    
    for scenario in test_scenarios:
        print(f"\n📋 Test: {scenario['name']}")
        print("-" * 40)
        
        try:
            response = requests.post(base_url, json=scenario['data'], timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # Check revenue info
                if 'revenue_info' in result:
                    revenue_info = result['revenue_info']
                    print(f"💰 Revenue Analysis:")
                    print(f"   Target: {revenue_info.get('min_revenue_target', 'N/A')}")
                    print(f"   Estimated: {revenue_info.get('estimated_revenue', 'N/A')}")
                    print(f"   Meets Target: {'✅' if revenue_info.get('meets_target') else '❌'}")
                    print(f"   Gap: {revenue_info.get('revenue_gap', 'N/A')}")
                else:
                    print(f"💰 Revenue Analysis: Not requested")
                
                # Check visits info
                if 'visits_info' in result:
                    visits_info = result['visits_info']
                    print(f"👥 Visits Analysis:")
                    print(f"   Target: {visits_info.get('min_visits_target', 'N/A')}")
                    print(f"   Average: {visits_info.get('average_visits', 'N/A')}")
                    print(f"   Meets Target: {'✅' if visits_info.get('meets_target') else '❌'}")
                    print(f"   Gap: {visits_info.get('visits_gap', 'N/A')}")
                    print(f"   Frequent Clients: {visits_info.get('total_frequent_clients', 'N/A')}")
                else:
                    print(f"👥 Visits Analysis: Not requested")
                
                # Check route
                if 'route' in result:
                    print(f"🗺️  Route: {len(result['route'])} stops generated")
                
                print(f"✅ {scenario['name']}: SUCCESS")
                
            else:
                print(f"❌ {scenario['name']}: FAILED - Status {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ {scenario['name']}: ERROR - {str(e)}")
    
    print(f"\n🎯 COMPREHENSIVE TEST COMPLETED!")
    print("=" * 60)

if __name__ == "__main__":
    test_revenue_and_visits_comprehensive()
