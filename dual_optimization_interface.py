#!/usr/bin/env python3
"""
Simple interface for running the Dual Delivery Optimization - 365 Days
This script provides an easy way to analyze delivery optimization for any commercial
"""

import sys
import os
from datetime import datetime

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main function to run the dual delivery optimization"""
    
    print("🚀 DUAL DELIVERY OPTIMIZATION - 365 DAYS FROM TODAY")
    print("=" * 60)
    print(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 This tool analyzes delivery optimization for 365 days starting from today")
    print()
    
    try:
        # Import the required functions
        from sarima_delivery_optimization import (
            dual_delivery_optimization_365_days,
            run_interactive_365_optimization,
            get_commercial_list
        )
        print("✅ System loaded successfully")
    except ImportError as e:
        print(f"❌ Error loading system: {e}")
        print("📋 Please ensure all required packages are installed:")
        print("   - pandas, numpy, matplotlib, statsmodels, mysql-connector-python, sqlalchemy")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    print("\n🎮 CHOOSE YOUR OPTION:")
    print("1. 🎯 Interactive Mode (Recommended) - Select commercial from list")
    print("2. 📊 Direct Mode - Enter specific commercial code")
    print("3. 📋 List Available Commercials - View all available options")
    print("4. ❌ Exit")
    
    while True:
        try:
            choice = input("\n🔹 Enter your choice (1-4): ").strip()
            
            if choice == '1':
                # Interactive mode
                print("\n🎮 Starting Interactive Mode...")
                results = run_interactive_365_optimization()
                
                if results:
                    print("\n🎉 Analysis completed successfully!")
                    print("📁 Check the generated CSV files for detailed daily plans")
                    print("📈 Check the PNG file for visualizations")
                else:
                    print("\n⚠️ Analysis was cancelled or failed")
                break
                
            elif choice == '2':
                # Direct mode
                print("\n📊 Direct Mode Selected")
                commercial_code = input("🎯 Enter commercial code: ").strip()
                
                if not commercial_code:
                    print("❌ Please enter a valid commercial code")
                    continue
                
                print(f"\n🚀 Starting analysis for commercial {commercial_code}...")
                
                # Ask for options
                include_revenue = input("💰 Include revenue optimization? (Y/n): ").strip().lower() != 'n'
                save_files = input("💾 Save results to files? (Y/n): ").strip().lower() != 'n'
                
                results = dual_delivery_optimization_365_days(
                    commercial_code=commercial_code,
                    include_revenue_optimization=include_revenue,
                    save_results=save_files
                )
                
                if results:
                    print("\n🎉 Analysis completed successfully!")
                    if save_files:
                        print("📁 Check the generated files for detailed results")
                else:
                    print("\n❌ Analysis failed. Please check the commercial code and try again")
                break
                
            elif choice == '3':
                # List commercials
                print("\n📋 Loading available commercials...")
                try:
                    commercials = get_commercial_list()
                    
                    if commercials:
                        print(f"\n📊 Found {len(commercials)} commercials with sufficient data:")
                        print("-" * 80)
                        print(f"{'Code':<15} {'Records':<10} {'Clients':<8} {'First Record':<12} {'Last Record':<12}")
                        print("-" * 80)
                        
                        for comm in commercials[:20]:  # Show top 20
                            print(f"{str(comm['commercial_code']):<15} "
                                  f"{comm['total_records']:<10} "
                                  f"{comm['unique_clients']:<8} "
                                  f"{str(comm['first_record'])[:10]:<12} "
                                  f"{str(comm['last_record'])[:10]:<12}")
                        
                        if len(commercials) > 20:
                            print(f"... and {len(commercials) - 20} more commercials available")
                        
                        print(f"\n💡 You can use any of these commercial codes with option 2 (Direct Mode)")
                    else:
                        print("❌ No commercials found with sufficient data")
                        print("📋 Please check your database connection and data")
                        
                except Exception as e:
                    print(f"❌ Error retrieving commercials: {e}")
                
                print("\n🔄 Returning to main menu...")
                continue
                
            elif choice == '4':
                print("\n👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1, 2, 3, or 4")
                continue
                
        except KeyboardInterrupt:
            print("\n\n👋 Operation cancelled by user. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            print("🔄 Returning to main menu...")
            continue
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Program interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("💡 Please check your installation and try again")
