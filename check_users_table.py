import mysql.connector

def get_users_table_structure():
    """Get the structure of the users table"""
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            database='pfe1',
            user='root',
            password=''
        )
        
        cursor = conn.cursor()
        
        # Get table structure
        cursor.execute("DESCRIBE users")
        columns = cursor.fetchall()
        
        print("Users table structure:")
        for column in columns:
            print(f"  - {column[0]}: {column[1]} {column[2] if column[2] == 'NO' else 'NULL'} {column[3] if column[3] else ''}")
        
        # Check if password column exists
        cursor.execute("SHOW COLUMNS FROM users LIKE 'password'")
        password_column = cursor.fetchone()
        
        if password_column:
            print(f"\nPassword column exists: {password_column}")
        else:
            print("\nNo password column found")
        
        # Get sample data
        cursor.execute("SELECT code, nom, prenom FROM users LIMIT 5")
        sample_users = cursor.fetchall()
        
        print(f"\nSample users:")
        for user in sample_users:
            print(f"  - Code: {user[0]}, Name: {user[1]} {user[2] if user[2] else ''}")
        
        conn.close()
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    get_users_table_structure()
