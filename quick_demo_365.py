#!/usr/bin/env python3
"""
Quick Demo Script for Dual Delivery Optimization - 365 Days
Run this script to see a working example of the optimization system
"""

import sys
import os
from datetime import datetime, timedelta

def quick_demo():
    """Quick demonstration of the dual optimization system"""
    
    print("🎬 QUICK DEMO: Dual Delivery Optimization - 365 Days")
    print("=" * 60)
    print(f"📅 Today: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"📅 Forecast Period: 365 days starting from today")
    print()
    
    try:
        # Import the optimization function
        from sarima_delivery_optimization import dual_delivery_optimization_365_days, get_commercial_list
        print("✅ Successfully loaded optimization system")
        
        # Get the first available commercial for demo
        print("\n📋 Finding available commercials...")
        commercials = get_commercial_list()
        
        if not commercials:
            print("❌ No commercials found in database")
            print("💡 Please ensure your database has data in the 'entetecommercials' table")
            return False
        
        # Use the first commercial with most data
        demo_commercial = commercials[0]['commercial_code']
        print(f"🎯 Using commercial: {demo_commercial}")
        print(f"📊 Commercial stats: {commercials[0]['total_records']} records, {commercials[0]['unique_clients']} clients")
        
        # Run the optimization
        print(f"\n🚀 Running 365-day optimization analysis...")
        print("⏳ This may take a few minutes...")
        
        results = dual_delivery_optimization_365_days(
            commercial_code=demo_commercial,
            include_revenue_optimization=True,
            save_results=True  # This will create CSV and PNG files
        )
        
        if results:
            print(f"\n🎉 SUCCESS! Dual optimization completed!")
            print(f"\n📊 RESULTS SUMMARY:")
            print(f"   🎯 Commercial: {results['commercial_code']}")
            print(f"   📅 Analysis period: {results['start_date']} to {results['end_date']}")
            print(f"   📈 Total predicted visits (365 days): {results['summary']['total_predicted_visits']:,}")
            print(f"   💰 Total predicted revenue (365 days): {results['summary']['total_predicted_revenue']:,.2f} TND")
            print(f"   📊 Daily average visits: {results['summary']['avg_daily_visits']:.1f}")
            print(f"   💵 Daily average revenue: {results['summary']['avg_daily_revenue']:.2f} TND")
            print(f"   🏆 Best performing month: {results['insights']['best_month']}")
            print(f"   📉 Lowest performing month: {results['insights']['worst_month']}")
            print(f"   ⭐ Best day of week: {results['insights']['best_day_of_week']}")
            print(f"   📊 Prediction quality score: {results['model_performance']['visits_model_quality']:.1f}/100")
            
            # Show sample daily predictions
            daily_plan = results['daily_plan']
            print(f"\n📅 SAMPLE DAILY PREDICTIONS (Next 10 days):")
            print("-" * 90)
            print(f"{'Date':<12} {'Day':<10} {'Visits':<8} {'Revenue':<10} {'Confidence':<12} {'Status':<20}")
            print("-" * 90)
            
            for i in range(min(10, len(daily_plan))):
                row = daily_plan.iloc[i]
                print(f"{row['date'].strftime('%Y-%m-%d'):<12} "
                      f"{row['day_of_week'][:9]:<10} "
                      f"{row['predicted_visits']:.1f:<8} "
                      f"{row['predicted_revenue']:.0f:<10} "
                      f"{row['confidence_level']:<12} "
                      f"{row['revenue_status'][:19]:<20}")
            
            # Show monthly summary
            monthly_summary = results['monthly_summary']
            print(f"\n📈 MONTHLY PREDICTIONS SUMMARY:")
            print("-" * 60)
            print(f"{'Month':<12} {'Total Visits':<12} {'Total Revenue':<15} {'Avg Daily':<10}")
            print("-" * 60)
            
            for month in monthly_summary.index:
                total_visits = monthly_summary.loc[month, ('predicted_visits', 'sum')]
                total_revenue = monthly_summary.loc[month, ('predicted_revenue', 'sum')]
                avg_daily = monthly_summary.loc[month, ('predicted_visits', 'mean')]
                
                print(f"{month[:11]:<12} {total_visits:.0f:<12} {total_revenue:.0f} TND {avg_daily:.1f:<10}")
            
            # Show files created
            today_str = datetime.now().strftime('%Y%m%d')
            csv_file = f"dual_optimization_365_days_{demo_commercial}_{today_str}.csv"
            summary_file = f"optimization_summary_{demo_commercial}_{today_str}.txt"
            plot_file = f"dual_optimization_365_visualization_{demo_commercial}_{today_str}.png"
            
            print(f"\n📁 FILES CREATED:")
            print(f"   📊 Detailed daily plan: {csv_file}")
            print(f"   📋 Summary report: {summary_file}")
            print(f"   📈 Visualization chart: {plot_file}")
            
            print(f"\n💡 KEY INSIGHTS:")
            
            # Revenue analysis
            revenue_target_days = results['summary']['revenue_target_met_days']
            if revenue_target_days >= 300:
                print(f"   ✅ Excellent performance: {revenue_target_days}/365 days meet revenue target")
            elif revenue_target_days >= 200:
                print(f"   ⚠️ Good performance: {revenue_target_days}/365 days meet revenue target")
                print(f"   💡 Consider strategies to improve {365 - revenue_target_days} underperforming days")
            else:
                print(f"   ❌ Needs improvement: Only {revenue_target_days}/365 days meet revenue target")
                print(f"   🚨 Urgent action required to improve daily revenue performance")
            
            # Seasonal insights
            best_month = results['insights']['best_month']
            worst_month = results['insights']['worst_month']
            print(f"   🌟 Peak season: {best_month} - plan for increased capacity")
            print(f"   📉 Low season: {worst_month} - focus on efficiency and cost control")
            
            # Day of week insights
            best_day = results['insights']['best_day_of_week']
            worst_day = results['insights']['worst_day_of_week']
            print(f"   📅 Best day: {best_day} - optimal for important client visits")
            print(f"   📅 Slowest day: {worst_day} - good for administrative tasks")
            
            print(f"\n🎯 NEXT STEPS:")
            print(f"   1. Review the detailed daily plan in the CSV file")
            print(f"   2. Use the visualization to identify patterns and trends")
            print(f"   3. Adjust resource allocation based on predicted peak/low periods")
            print(f"   4. Monitor actual performance against predictions")
            print(f"   5. Re-run analysis monthly with updated data")
            
            return True
            
        else:
            print(f"❌ Demo failed - unable to generate optimization results")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print(f"💡 Please ensure all required packages are installed:")
        print(f"   pip install pandas numpy matplotlib statsmodels mysql-connector-python sqlalchemy")
        return False
    except Exception as e:
        print(f"❌ Demo error: {e}")
        print(f"💡 Please check your database connection and ensure you have historical data")
        return False

def show_system_requirements():
    """Show system requirements and setup instructions"""
    print("📋 SYSTEM REQUIREMENTS:")
    print("-" * 40)
    print("🐍 Python 3.7+")
    print("🗄️ MySQL database with 'pfe1' database")
    print("📊 Table 'entetecommercials' with delivery data")
    print()
    print("📦 Required packages:")
    print("   - pandas")
    print("   - numpy") 
    print("   - matplotlib")
    print("   - statsmodels")
    print("   - mysql-connector-python")
    print("   - sqlalchemy")
    print("   - seaborn (optional)")
    print()
    print("💾 Database connection:")
    print("   - Host: 127.0.0.1")
    print("   - Database: pfe1")
    print("   - User: root")
    print("   - Password: (empty)")

if __name__ == "__main__":
    print("🎬 DUAL DELIVERY OPTIMIZATION - QUICK DEMO")
    print("=" * 50)
    
    print("\nChoose an option:")
    print("1. 🚀 Run Quick Demo")
    print("2. 📋 Show System Requirements")
    print("3. ❌ Exit")
    
    try:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            print(f"\n🚀 Starting Quick Demo...")
            success = quick_demo()
            
            if success:
                print(f"\n🎉 Demo completed successfully!")
                print(f"💡 You can now use the full system with dual_optimization_interface.py")
            else:
                print(f"\n❌ Demo failed. Please check requirements and try again.")
                
        elif choice == '2':
            print()
            show_system_requirements()
            
        elif choice == '3':
            print("\n👋 Goodbye!")
            
        else:
            print("\n❌ Invalid choice")
            
    except KeyboardInterrupt:
        print(f"\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
