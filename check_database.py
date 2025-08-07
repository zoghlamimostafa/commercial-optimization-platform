import sqlite3

def check_database_tables():
    conn = sqlite3.connect('deliveries.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("Available tables:")
    for table in tables:
        print(f"  - {table[0]}")
        
    # Check the first table structure
    if tables:
        table_name = tables[0][0]
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        print(f"\nColumns in '{table_name}':")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
            
        # Show sample data
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
        sample = cursor.fetchall()
        print(f"\nSample data from '{table_name}':")
        for row in sample:
            print(f"  {row}")
    
    conn.close()

if __name__ == "__main__":
    check_database_tables()
