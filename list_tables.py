import mysql.connector

def list_tables():
    # Database connection
    server = '127.0.0.1'
    database = 'pfe1'
    username = 'root'
    password = ''
    
    try:
        conn = mysql.connector.connect(
            host=server,
            database=database,
            user=username,
            password=password
        )
        
        cursor = conn.cursor()
        
        # List all tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print("Tables in the database:")
        for table in tables:
            print(f"- {table[0]}")
            
            # Show table structure
            cursor.execute(f"DESCRIBE {table[0]}")
            columns = cursor.fetchall()
            print("  Columns:")
            for column in columns:
                print(f"  - {column[0]}: {column[1]}")
            print()
        
        conn.close()
        print("Connection closed.")
        
    except mysql.connector.Error as e:
        print(f"Error connecting to database: {e}")

if __name__ == "__main__":
    list_tables()
