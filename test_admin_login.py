import mysql.connector

def test_login():
    """Test the admin login with the new password"""
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            database='pfe1',
            user='root',
            password=''
        )
        
        cursor = conn.cursor(dictionary=True)
        
        # Test the login with new password
        login = "Admin"
        password = "password123"
        
        cursor.execute("SELECT * FROM users WHERE login = %s AND isactif = 1", (login,))
        user = cursor.fetchone()
        
        if user and user['password'] == password:
            print("✅ Login test SUCCESSFUL!")
            print(f"   User ID: {user['id']}")
            print(f"   Login: {user['login']}")
            print(f"   Name: {user['nom']} {user['prenom'] if user['prenom'] else ''}")
            print(f"   Is Admin: {user['isadmin']}")
            print(f"   Grade: {user['grade']}")
            return True
        else:
            print("❌ Login test FAILED!")
            if user:
                print(f"   User found but password mismatch")
                print(f"   Expected: {password}")
                print(f"   Actual: {user['password']}")
            else:
                print(f"   User not found or inactive")
            return False
        
        conn.close()
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        return False

if __name__ == "__main__":
    print("Testing admin login with new password...")
    test_login()
