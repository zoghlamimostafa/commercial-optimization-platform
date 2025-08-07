import pandas as pd
import mysql.connector
from datetime import datetime

def quick_export():
    """Quick export of commercial calendar data"""
    
    # Database connection
    conn = mysql.connector.connect(
        host='127.0.0.1',
        database='pfe1',
        user='root',
        password=''
    )
    
    # Your SQL query
    query = """
    WITH RECURSIVE calendar AS (
      SELECT DATE('2023-01-01') AS jour
      UNION ALL
      SELECT DATE_ADD(jour, INTERVAL 1 DAY)
      FROM calendar
      WHERE jour < DATE('2025-02-11')
    ),
    commerciaux AS (
      SELECT DISTINCT commercial_code FROM entetecommercials
    ),
    factures AS (
      SELECT 
        DATE(date) AS jour,
        commercial_code,
        COUNT(*) AS total_factures
      FROM entetecommercials
      WHERE date >= '2023-01-01' AND date <= '2025-02-11'
      GROUP BY DATE(date), commercial_code
    )
    SELECT 
      c.jour,
      m.commercial_code,
      COALESCE(f.total_factures, 0) AS total_factures
    FROM calendar c
    CROSS JOIN commerciaux m
    LEFT JOIN factures f
      ON f.jour = c.jour AND f.commercial_code = m.commercial_code
    ORDER BY c.jour, m.commercial_code;
    """
    
    print("Executing query...")
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Export to CSV
    filename = f"commercial_calendar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False)
    
    print(f"Exported {len(df):,} rows to {filename}")
    print(f"Date range: {df['jour'].min()} to {df['jour'].max()}")
    print(f"Commercials: {df['commercial_code'].nunique()}")

if __name__ == "__main__":
    quick_export()