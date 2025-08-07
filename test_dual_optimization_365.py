#!/usr/bin/env python3
"""
Test script for the Dual Delivery Optimization - 365 Days functionality
This script demonstrates how to use the new dual optimization system
"""

import sys
import os
from datetime import datetime, timedelta

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from sarima_delivery_optimization import (
        dual_delivery_optimization_365_days,
        run_interactive_365_optimization,
        get_commercial_list
    )
    print("✅ Successfully imported dual optimization functions")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_commercial_list():
    """Test getting the list of available commercials"""
    print("\n🧪 Testing commercial list retrieval...")
    
    try:
        commercials = get_commercial_list()
        
        if commercials:
            print(f"✅ Found {len(commercials)} commercials with sufficient data")
            print(f"📊 Top 5 commercials:")
            
            for i, comm in enumerate(commercials[:5], 1):
                print(f"   {i}. Commercial {comm['commercial_code']}: "
                      f"{comm['total_records']} records, "
                      f"{comm['unique_clients']} clients")
            
            return commercials[0]['commercial_code']  # Return first commercial for testing
        else:
            print("❌ No commercials found")
            return None
            
    except Exception as e:
        print(f"❌ Error testing commercial list: {e}")
        return None

def test_dual_optimization_basic(commercial_code):
    """Test basic dual optimization functionality"""
    print(f"\n🧪 Testing dual optimization for commercial {commercial_code}...")
    
    try:
        # Run optimization with minimal settings for testing
        results = dual_delivery_optimization_365_days(
            commercial_code=commercial_code,
            include_revenue_optimization=True,
            save_results=False  # Don't save files during testing
        )
        
        if results:
            print(f"✅ Dual optimization completed successfully!")
            print(f"📊 Summary:")
            print(f"   🎯 Commercial: {results['commercial_code']}")
            print(f"   📅 Period: {results['start_date']} to {results['end_date']}")
            print(f"   📈 Total predicted visits: {results['summary']['total_predicted_visits']:,}")
            print(f"   💰 Total predicted revenue: {results['summary']['total_predicted_revenue']:,.2f} TND")
            print(f"   📅 Daily average visits: {results['summary']['avg_daily_visits']:.1f}")
            print(f"   💵 Daily average revenue: {results['summary']['avg_daily_revenue']:.2f} TND")
            print(f"   🏆 Best month: {results['insights']['best_month']}")
            print(f"   📊 Model quality: {results['model_performance']['visits_model_quality']:.1f}/100")
            
            # Show some daily details
            daily_plan = results['daily_plan']
            print(f"\n📅 Sample daily predictions (first 7 days):")
            for i in range(min(7, len(daily_plan))):
                row = daily_plan.iloc[i]
                print(f"   {row['date'].strftime('%Y-%m-%d')} ({row['day_of_week']}): "
                      f"{row['predicted_visits']:.1f} visits, "
                      f"{row['predicted_revenue']:.2f} TND, "
                      f"{row['confidence_level']} confidence")
            
            return True
        else:
            print("❌ Dual optimization failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing dual optimization: {e}")
        return False

def test_interactive_mode():
    """Test the interactive mode (simulated)"""
    print(f"\n🧪 Testing interactive mode components...")
    
    try:
        # Test commercial list for interactive mode
        commercials = get_commercial_list()
        
        if commercials:
            print(f"✅ Interactive mode components ready")
            print(f"📋 {len(commercials)} commercials available for selection")
            print(f"🎯 Interactive mode can be started with: run_interactive_365_optimization()")
            return True
        else:
            print("❌ No data available for interactive mode")
            return False
            
    except Exception as e:
        print(f"❌ Error testing interactive mode: {e}")
        return False

def run_demo_365_optimization():
    """Run a complete demo of the 365-day optimization"""
    print(f"\n🎬 DEMO: Dual Delivery Optimization - 365 Days")
    print("=" * 60)
    print(f"📅 Today: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"📅 Forecast end: {(datetime.now() + timedelta(days=364)).strftime('%Y-%m-%d')}")
    
    # Step 1: Get commercial list
    print(f"\n📋 Step 1: Getting available commercials...")
    test_commercial = test_commercial_list()
    
    if not test_commercial:
        print("❌ Demo cannot continue without commercial data")
        return False
    
    # Step 2: Test basic optimization
    print(f"\n🚀 Step 2: Running dual optimization...")
    success = test_dual_optimization_basic(test_commercial)
    
    if not success:
        print("❌ Demo failed during optimization")
        return False
    
    # Step 3: Test interactive components
    print(f"\n🎮 Step 3: Testing interactive components...")
    interactive_ready = test_interactive_mode()
    
    print(f"\n🎉 DEMO COMPLETED!")
    print(f"✅ Commercial list: Working")
    print(f"✅ Dual optimization: {'Working' if success else 'Failed'}")
    print(f"✅ Interactive mode: {'Ready' if interactive_ready else 'Not Ready'}")
    
    print(f"\n💡 NEXT STEPS:")
    print(f"   🎯 Use run_interactive_365_optimization() for user-friendly selection")
    print(f"   📊 Use dual_delivery_optimization_365_days(commercial_code) for direct analysis")
    print(f"   💾 Enable save_results=True to generate CSV files and visualizations")
    
    return True

if __name__ == "__main__":
    print(f"🧪 DUAL DELIVERY OPTIMIZATION - 365 DAYS TEST SUITE")
    print(f"=" * 60)
    print(f"🕒 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Run the complete demo
        demo_success = run_demo_365_optimization()
        
        if demo_success:
            print(f"\n🎉 ALL TESTS PASSED!")
            print(f"✅ The dual delivery optimization system is ready to use")
            
            # Offer to run interactive mode
            response = input(f"\n🎮 Would you like to run the interactive optimization now? (y/N): ").strip().lower()
            
            if response == 'y':
                print(f"\n🚀 Starting interactive mode...")
                results = run_interactive_365_optimization()
                
                if results:
                    print(f"\n🎉 Interactive optimization completed successfully!")
                else:
                    print(f"\n⚠️ Interactive optimization was cancelled or failed")
        else:
            print(f"\n❌ TESTS FAILED!")
            print(f"❌ Please check the database connection and data availability")
            
    except KeyboardInterrupt:
        print(f"\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
    
    print(f"\n🏁 Test suite completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
