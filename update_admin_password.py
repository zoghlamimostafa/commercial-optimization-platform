import mysql.connector

def check_admin_users():
    """Check which users have admin privileges"""
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            database='pfe1',
            user='root',
            password=''
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT id, login, nom, prenom, isadmin FROM users WHERE isadmin = 1")
        admins = cursor.fetchall()
        
        print("Admin users found:")
        for admin in admins:
            name = f"{admin[2]} {admin[3]}" if admin[3] else admin[2]
            print(f"  - ID: {admin[0]}, Login: {admin[1]}, Name: {name}, IsAdmin: {admin[4]}")
        
        conn.close()
        return admins
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        return []

def update_admin_password(admin_id, new_password):
    """Update admin password"""
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            database='pfe1',
            user='root',
            password=''
        )
        
        cursor = conn.cursor()
        # Update password (direct text for now, as the existing passwords appear to be plaintext)
        cursor.execute("UPDATE users SET password = %s WHERE id = %s", (new_password, admin_id))
        conn.commit()
        
        print(f"Password updated successfully for admin ID: {admin_id}")
        
        conn.close()
        return True
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        return False

if __name__ == "__main__":
    # Check admin users
    admins = check_admin_users()
    
    if admins:
        # Update password for the first admin user
        admin_id = admins[0][0]
        new_password = "password123"
        
        print(f"\nUpdating password for admin ID {admin_id} to '{new_password}'...")
        success = update_admin_password(admin_id, new_password)
        
        if success:
            print("Admin password changed successfully!")
        else:
            print("Failed to change admin password.")
    else:
        print("No admin users found!")
