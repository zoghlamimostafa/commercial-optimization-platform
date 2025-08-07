"""
Check actual passwords in the users table
"""
import mysql.connector

def get_db_connection():
    server = '127.0.0.1'
    database = 'pfe1'
    username = 'root'
    password = ''
    
    conn = mysql.connector.connect(
        host=server,
        database=database,
        user=username,
        password=password
    )
    return conn

def check_passwords():
    """Check what passwords are actually stored"""
    print("Checking actual passwords in the database:")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT login, password, nom, prenom FROM users WHERE isactif = 1 LIMIT 5")
    users = cursor.fetchall()
    conn.close()
    
    for user in users:
        print(f"  - Login: '{user['login']}', Password: '{user['password']}', Name: {user['nom']} {user['prenom']}")
    
    return users

if __name__ == "__main__":
    print("=== Password Check ===")
    check_passwords()
