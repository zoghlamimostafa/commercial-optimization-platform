#!/usr/bin/env python3
"""
Quick Demo: 365-Day Prediction Flask Integration
Demonstrates the new web-based 365-day prediction system
"""

import webbrowser
import time
import subprocess
import sys
from threading import Thread

def start_flask_app():
    """Start the Flask application in a separate thread"""
    try:
        subprocess.run([sys.executable, "app.py"], 
                      cwd=r"c:\Users\mostafa zoghlami\Desktop\souha")
    except Exception as e:
        print(f"Error starting Flask app: {e}")

def demo_365_prediction_system():
    """Demonstrate the 365-day prediction system"""
    
    print("🚀 365-Day Prediction System Demo")
    print("=" * 50)
    
    print("\n📋 Features:")
    print("   • Dual optimization engine for visits and revenue")
    print("   • 365-day forecasting with SARIMA models")
    print("   • Interactive web interface with real-time charts")
    print("   • Excel export with comprehensive reporting")
    print("   • Mobile-responsive design with Bootstrap 5")
    
    print("\n🔧 Features Included:")
    print("   ✅ Commercial selection with statistics")
    print("   ✅ Revenue optimization toggle")
    print("   ✅ Real-time 365-day analysis")
    print("   ✅ Interactive charts and visualizations")
    print("   ✅ Monthly and weekly pattern analysis")
    print("   ✅ Downloadable Excel reports")
    print("   ✅ Model performance metrics")
    print("   ✅ Key business insights")
    
    print("\n📊 Analysis Capabilities:")
    print("   • Total visits prediction (365 days)")
    print("   • Revenue forecasting with optimization")
    print("   • Seasonal pattern detection")
    print("   • Peak and low activity identification")
    print("   • Day-of-week performance analysis")
    print("   • Confidence interval calculations")
    print("   • Historical trend analysis")
    
    print("\n🌐 Web Interface Features:")
    print("   • Modern, responsive design")
    print("   • Real-time loading indicators")
    print("   • Interactive Chart.js visualizations")
    print("   • Detailed data tables")
    print("   • One-click Excel downloads")
    print("   • Dashboard integration")
    
    print("\n🎯 Business Value:")
    print("   • Improved delivery planning")
    print("   • Revenue optimization")
    print("   • Resource allocation insights")
    print("   • Seasonal trend awareness")
    print("   • Performance benchmarking")
    print("   • Data-driven decision making")
    
    print("\n" + "=" * 50)
    print("🔗 How to Access:")
    print("1. Start the Flask application")
    print("2. Open: http://localhost:5000")
    print("3. Click 'Prédiction 365 Jours' on dashboard")
    print("4. Select a commercial and generate predictions")
    
    print("\n💡 Quick Start Guide:")
    print("1. Select Commercial: Choose from dropdown with stats")
    print("2. Enable Optimization: Toggle revenue optimization")
    print("3. Generate Analysis: Click 'Generate 365-Day Plan'")
    print("4. Review Results: View metrics, charts, and insights")
    print("5. Download Report: Get comprehensive Excel file")
    
    # Ask if user wants to start the demo
    print("\n" + "=" * 50)
    response = input("🚀 Would you like to start the Flask app now? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        print("\n🔄 Starting Flask application...")
        print("   • Loading modules and dependencies...")
        print("   • Initializing database connections...")
        print("   • Setting up prediction engines...")
        print("   • Starting web server...")
        
        # Start Flask app in background
        flask_thread = Thread(target=start_flask_app, daemon=True)
        flask_thread.start()
        
        # Wait a moment for server to start
        print("\n⏳ Waiting for server to initialize...")
        time.sleep(3)
        
        # Open browser
        print("🌐 Opening web browser...")
        try:
            webbrowser.open('http://localhost:5000/365_prediction')
            print("\n✅ Demo launched successfully!")
            print("\n📌 Navigation:")
            print("   • Dashboard: http://localhost:5000")
            print("   • 365 Prediction: http://localhost:5000/365_prediction")
            print("\n🔧 To stop the server: Press Ctrl+C in terminal")
            
            # Keep the demo running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\n🛑 Demo stopped by user")
                
        except Exception as e:
            print(f"❌ Failed to open browser: {e}")
            print("   Please manually navigate to: http://localhost:5000/365_prediction")
    else:
        print("\n📝 Manual Start Instructions:")
        print("   1. cd \"c:\\Users\\mostafa zoghlami\\Desktop\\souha\"")
        print("   2. python app.py")
        print("   3. Open: http://localhost:5000/365_prediction")
    
    print("\n" + "=" * 50)
    print("🎉 365-Day Prediction System Ready!")
    print("📚 See README_365_FLASK_INTEGRATION.md for full documentation")

if __name__ == "__main__":
    demo_365_prediction_system()
