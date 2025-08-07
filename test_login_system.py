"""
Simple test script to verify the login system without complex dependencies
"""
import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash

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

def test_user_authentication(login_username, password):
    """Test user authentication"""
    print(f"Testing authentication for user: {login_username}")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE login = %s AND isactif = 1", (login_username,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        print(f"User found: {user['nom']} {user['prenom']} (Grade: {user['grade']})")
        if user['password'] == password:  # Direct password comparison
            print("✅ Authentication successful!")
            return True
        else:
            print("❌ Invalid password")
            return False
    else:
        print("❌ User not found or inactive")
        return False

def list_sample_users():
    """List some sample users from the database"""
    print("Sample users in the database:")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT login, nom, prenom, grade, isactif FROM users WHERE isactif = 1 LIMIT 5")
    users = cursor.fetchall()
    conn.close()
    
    for user in users:
        print(f"  - Login: {user['login']}, Name: {user['nom']} {user['prenom']}, Grade: {user['grade']}")
    
    return users

if __name__ == "__main__":
    print("=== Login System Test ===")
    
    # List sample users
    sample_users = list_sample_users()
    
    if sample_users:
        # Test with the first user (assuming password is the same as login or a simple password)
        test_user = sample_users[0]
        test_login = test_user['login']
        
        print(f"\nTesting authentication with user: {test_login}")
        
        # Try different password possibilities
        possible_passwords = [test_login, '123', 'password', '1234', 'admin']
        
        for pwd in possible_passwords:
            print(f"\nTrying password: '{pwd}'")
            if test_user_authentication(test_login, pwd):
                break
    else:
        print("No active users found in the database")
