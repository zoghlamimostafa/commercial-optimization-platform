import mysql.connector
import pandas as pd

# Database connection configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'pfe1'
}

def get_commercial_codes():
    """Get all commercial codes from the database"""
    try:
        conn = mysql.connector.connect(**db_config)
        query = """
        SELECT DISTINCT ec.commercial_code, COUNT(*) as record_count
        FROM entetecommercials ec 
        WHERE ec.date >= DATE_SUB(NOW(), INTERVAL 1 YEAR)
        GROUP BY ec.commercial_code
        ORDER BY record_count DESC
        LIMIT 10
        """
        result = pd.read_sql(query, conn)
        conn.close()
        return result
    except Exception as e:
        print(f"Database error: {e}")
        return None

# Get commercial codes
commercial_codes = get_commercial_codes()
if commercial_codes is not None:
    print("Available commercial codes:")
    print(commercial_codes)
else:
    print("Failed to retrieve commercial codes")
