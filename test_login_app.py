from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import mysql.connector
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

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
    
    if user and user['password'] == password:
        return user
    return None

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
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    user = get_current_user()
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - Test Login</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="#">Tableau de Bord</a>
                <div class="navbar-nav ms-auto">
                    <span class="navbar-text me-3">
                        Bienvenue, {user['nom']} {user['prenom']} ({user['login']})
                    </span>
                    <a class="nav-link" href="{url_for('logout')}">Déconnexion</a>
                </div>
            </div>
        </nav>
        <div class="container mt-4">
            <div class="alert alert-success">
                <h4>✅ Connexion réussie!</h4>
                <p><strong>Utilisateur:</strong> {user['login']}</p>
                <p><strong>Nom:</strong> {user['nom']} {user['prenom']}</p>
                <p><strong>Grade:</strong> {user['grade']}</p>
                <p><strong>Admin:</strong> {'Oui' if user['isadmin'] else 'Non'}</p>
                <p><strong>ID:</strong> {user['id']}</p>
            </div>
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Système de login fonctionnel</h5>
                    <p class="card-text">L'authentification fonctionne correctement. Vous pouvez maintenant intégrer ce système avec votre application complète.</p>
                    <a href="{url_for('logout')}" class="btn btn-danger">Se déconnecter</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(debug=True, port=5001)
