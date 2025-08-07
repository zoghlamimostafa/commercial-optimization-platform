import pandas as pd
import mysql.connector
from datetime import datetime
import io
import base64
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, session, flash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # Change this to a secure random key

# Database connection function
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

# Authentication functions
def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current logged-in user information"""
    if 'user_id' not in session:
        return None
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s AND isactif = 1", (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    return user

def authenticate_user(login, password):
    """Authenticate user with login and password"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE login = %s AND isactif = 1", (login,))
    user = cursor.fetchone()
    conn.close()
    
    if user and user['password'] == password:  # Direct password comparison
        return user
    return None

# Function to get list of clients with their names
def get_clients():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT ec.client_code, c.nom, c.prenom FROM entetecommercials ec LEFT JOIN clients c ON ec.client_code = c.code")
    clients = []
    for row in cursor.fetchall():
        code = row[0] # type: ignore
        nom = row[1] if row[1] else '' # type: ignore
        prenom = row[2] if row[2] else ''
        # Create full name (in French format: Last name then First name)
        if nom and prenom:
            full_name = f"{nom} {prenom}".strip()
        else:
            full_name = nom or code
        clients.append((code, full_name))
    conn.close()
    return clients

# Function to get list of products
def get_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT p.code, p.nom FROM produits p")
    products = []
    for row in cursor.fetchall():
        code = row[0]
        nom = row[1] if row[1] else code
        products.append((code, nom))
    conn.close()
    return products

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_username = request.form['login']
        password = request.form['password']
        
        user = authenticate_user(login_username, password)
        if user:
            session['user_id'] = user['id']
            session['user_login'] = user['login']
            session['user_name'] = f"{user['nom']} {user['prenom']}"
            session['user_grade'] = user['grade']
            session['is_admin'] = user['isadmin']
            flash('Connexion réussie!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('login'))

# Protected routes
@app.route('/')
@login_required
def index():
    clients = get_clients()
    user = get_current_user()
    return render_template('index.html', clients=clients, user=user)

@app.route('/clients')
@login_required
def clients_list():
    clients = get_clients()
    user = get_current_user()
    return render_template('clients.html', clients=clients, user=user)

@app.route('/products')
@login_required
def products_list():
    products = get_products()
    user = get_current_user()
    return render_template('products.html', products=products, user=user)

@app.route('/dashboard/<client_code>')
@login_required
def dashboard(client_code):
    user = get_current_user()
    # Get client full name
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT nom, prenom FROM clients WHERE code = '{client_code}'")
    result = cursor.fetchone()
    if result and result[0]:
        nom = result[0]
        prenom = result[1] if result[1] else ""
        client_name = f"{nom} {prenom}".strip() if prenom else nom
    else:
        client_name = client_code
    conn.close()
    
    return render_template('dashboard.html', 
                          client_code=client_code,
                          client_name=client_name,
                          user=user,
                          message="Tableau de bord temporaire - Fonctionnalités analytiques temporairement désactivées en raison de problèmes de compatibilité des dépendances.")

if __name__ == '__main__':
    app.run(debug=True)
