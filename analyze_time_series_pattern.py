import pandas as pd
from sqlalchemy import create_engine
import mysql.connector
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

def get_db_connection():
    """Établit une connexion à la base de données MySQL"""
    db_config = {
        'host': '127.0.0.1',
        'database': 'pfe1',
        'user': 'root',
        'password': ''
    }
    
    connection_url = f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"
    engine = create_engine(connection_url, pool_recycle=3600, pool_pre_ping=True)
    return engine

def analyze_time_series_pattern():
    print("🔍 ANALYZING TIME SERIES PATTERN")
    print("=" * 50)
    
    # Connect to database
    conn = get_db_connection()
    
    # Fetch data for commercial analysis using real MySQL data
    query = """
    SELECT 
        ec.date,
        ec.commercial_code,
        COUNT(ec.code) AS nombre_visites,
        COUNT(DISTINCT ec.client_code) AS nb_clients_visites,
        SUM(ec.net_a_payer) AS chiffre_affaires
    FROM entetecommercials ec
    WHERE ec.commercial_code = %s
    GROUP BY ec.date, ec.commercial_code
    ORDER BY ec.date
    """
    
    # Use a commercial code that exists in the database
    commercial_code = '1'
    data = pd.read_sql(query, conn, params=[commercial_code])    data['date'] = pd.to_datetime(data['date'])
    
    print(f"📊 Raw data: {len(data)} records")
    print(f"   Date range: {data['date'].min()} to {data['date'].max()}")
    
    # Create time series with proper aggregation
    data['date_only'] = data['date'].dt.date
    daily_aggregated = data.groupby('date_only').agg({
        'nombre_visites': 'sum',
        'nb_clients_visites': 'sum', 
        'chiffre_affaires': 'sum'
    }).reset_index()
    
    daily_aggregated['date_only'] = pd.to_datetime(daily_aggregated['date_only'])
    
    print(f"\n📈 Daily aggregated data: {len(daily_aggregated)} days")
    print(f"   Visit stats: min={daily_aggregated['nombre_visites'].min()}, max={daily_aggregated['nombre_visites'].max()}, mean={daily_aggregated['nombre_visites'].mean():.2f}")
    print(f"   Revenue stats: min={daily_aggregated['chiffre_affaires'].min():.2f}, max={daily_aggregated['chiffre_affaires'].max():.2f}, mean={daily_aggregated['chiffre_affaires'].mean():.2f}")
    
    # Create full date range
    start_date = data['date'].min().date()
    end_date = data['date'].max().date()
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Create time series with zero-filling
    ts_visits = daily_aggregated.set_index('date_only')['nombre_visites'].reindex(date_range).fillna(0)
    ts_revenue = daily_aggregated.set_index('date_only')['chiffre_affaires'].reindex(date_range).fillna(0)
    
    print(f"\n⏰ Full time series: {len(ts_visits)} days")
    print(f"   Visit distribution:")
    print(f"     Zero days: {(ts_visits == 0).sum()} ({(ts_visits == 0).mean()*100:.1f}%)")
    print(f"     Non-zero days: {(ts_visits > 0).sum()} ({(ts_visits > 0).mean()*100:.1f}%)")
    print(f"     Max visits per day: {ts_visits.max()}")
    
    # Analyze patterns
    print(f"\n📊 Pattern Analysis:")
    print(f"   Variance: {ts_visits.var():.6f}")
    print(f"   Standard deviation: {ts_visits.std():.6f}")
    print(f"   Average visits on active days: {ts_visits[ts_visits > 0].mean():.2f}")
    
    # Show distribution of visit counts
    visit_counts = ts_visits.value_counts().sort_index()
    print(f"\n📈 Visit count distribution:")
    for visits, days in visit_counts.items():
        print(f"   {visits} visits: {days} days ({days/len(ts_visits)*100:.1f}%)")
    
    # Weekly pattern analysis
    ts_df = pd.DataFrame({'visits': ts_visits, 'revenue': ts_revenue})
    ts_df['weekday'] = ts_df.index.day_name()
    
    weekly_stats = ts_df.groupby('weekday')['visits'].agg(['mean', 'sum', 'count']).round(2)
    print(f"\n📅 Weekly pattern:")
    print(weekly_stats)
    
    # Monthly pattern
    ts_df['month'] = ts_df.index.month_name()
    monthly_stats = ts_df.groupby('month')['visits'].agg(['mean', 'sum', 'count']).round(2)
    print(f"\n📆 Monthly pattern:")
    print(monthly_stats)
    
    # Look at recent activity
    recent_data = ts_df.tail(30)
    print(f"\n🕐 Last 30 days activity:")
    print(f"   Total visits: {recent_data['visits'].sum()}")
    print(f"   Active days: {(recent_data['visits'] > 0).sum()}")
    print(f"   Total revenue: {recent_data['revenue'].sum():.2f}")
    
    # Check for trends
    print(f"\n📈 Trend Analysis:")
    first_half = ts_visits[:len(ts_visits)//2]
    second_half = ts_visits[len(ts_visits)//2:]
      print(f"   First half mean: {first_half.mean():.4f}")
    print(f"   Second half mean: {second_half.mean():.4f}")
    print(f"   Trend: {'Increasing' if second_half.mean() > first_half.mean() else 'Decreasing'}")
    
    conn.dispose()
    
    return ts_visits, ts_revenue

if __name__ == "__main__":
    ts_visits, ts_revenue = analyze_time_series_pattern()
