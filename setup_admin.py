import mysql.connector

def check_all_users():
    """Check all users to identify potential admins"""
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            database='pfe1',
            user='root',
            password=''
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT id, login, nom, prenom, isadmin, grade, role_code FROM users LIMIT 10")
        users = cursor.fetchall()
        
        print("First 10 users:")
        for user in users:
            name = f"{user[2]} {user[3]}" if user[3] else user[2]
            print(f"ID: {user[0]}, Login: {user[1]}, Name: {name}, IsAdmin: {user[4]}, Grade: {user[5]}, Role: {user[6]}")
        
        # Check if there's a user that looks like admin
        cursor.execute("SELECT id, login FROM users WHERE login LIKE '%admin%' OR login = 'admin' OR grade = 'SUP'")
        potential_admins = cursor.fetchall()
        
        print("\nPotential admin users:")
        for admin in potential_admins:
            print(f"  - ID: {admin[0]}, Login: {admin[1]}")
        
        conn.close()
        return users, potential_admins
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        return [], []

def create_or_update_admin():
    """Create an admin user or update existing user to admin"""
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            database='pfe1',
            user='root',
            password=''
        )
        
        cursor = conn.cursor()
        
        # First, try to find a user with login 'admin'
        cursor.execute("SELECT id FROM users WHERE login = 'admin'")
        admin_user = cursor.fetchone()
        
        if admin_user:
            # Update existing admin user
            admin_id = admin_user[0]
            cursor.execute("UPDATE users SET password = %s, isadmin = 1 WHERE id = %s", ("password123", admin_id))
            print(f"Updated existing admin user (ID: {admin_id}) with new password")
        else:
            # Check if there's a user with ID 1 (often the first user)
            cursor.execute("SELECT id, login FROM users WHERE id = 1")
            first_user = cursor.fetchone()
            
            if first_user:
                # Make the first user an admin
                cursor.execute("UPDATE users SET password = %s, isadmin = 1 WHERE id = 1", ("password123",))
                print(f"Made user ID 1 (login: {first_user[1]}) an admin with password 'password123'")
            else:
                print("No suitable user found to make admin")
                return False
        
        conn.commit()
        conn.close()
        return True
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        return False

if __name__ == "__main__":
    print("Checking users...")
    users, potential_admins = check_all_users()
    
    print("\nCreating/updating admin user...")
    success = create_or_update_admin()
    
    if success:
        print("\nAdmin user setup complete! Login details:")
        print("  - Password: password123")
        print("  - The first user or 'admin' user has been given admin privileges")
    else:
        print("Failed to setup admin user.")
