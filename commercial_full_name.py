"""
This script adds the full name of commercials to the commercial dashboard.
"""
import mysql.connector

def get_commercial_name(commercial_code):
    """Get the full name of a commercial from the users table."""
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            database="pfe1",
            user="root",
            password=""
        )
        cursor = conn.cursor()
        
        # Try to get name from users table
        cursor.execute(
            "SELECT nom, prenom FROM users WHERE code = %s", 
            (commercial_code,)
        )
        result = cursor.fetchone()
        
        if result and result[0]:
            nom = result[0]
            prenom = result[1] if result[1] else ""
            commercial_name = f"{nom} {prenom}".strip() if prenom else nom
        else:
            commercial_name = f"Commercial {commercial_code}"
        
        conn.close()
        return commercial_name
    except Exception as e:
        print(f"Error getting commercial name: {str(e)}")
        return f"Commercial {commercial_code}"

# For testing
if __name__ == "__main__":
    test_code = "COM001"
    print(f"Name for {test_code}: {get_commercial_name(test_code)}")
