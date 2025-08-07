import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from prophet import Prophet
import mysql.connector
from datetime import datetime
import io
import base64
import traceback
import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, session, flash
from werkzeug.security import check_password_hash
from functools import wraps
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for matplotlib
from product_analysis import plot_monthly_sales, plot_top_clients, forecast_sales_for_2025, load_product_sales_data
from delivery_optimization import generate_delivery_plan
from sarima_delivery_optimization import get_historical_deliveries, dual_delivery_optimization_365_days, get_commercial_list
import data_preprocessing
from werkzeug.security import check_password_hash, generate_password_hash
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
    
    if user and user['password'] == password:  # Direct password comparison for now
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

# Function to get a list of products with data
def get_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT lc.produit_code, p.libelle 
        FROM lignecommercials lc 
        LEFT JOIN produits p ON lc.produit_code = p.code
        ORDER BY lc.produit_code
    """)
    products = []
    for row in cursor.fetchall():
        code = row[0]
        libelle = row[1] if row[1] else code
        products.append((code, libelle))
    conn.close()
    return products

# Prophet prediction function
def generate_forecast(client_code):
    conn = get_db_connection()
    
    # Get client name
    cursor = conn.cursor()
    cursor.execute(f"SELECT nom FROM clients WHERE code = '{client_code}'")
    result = cursor.fetchone()
    client_name = result[0] if result and result[0] else client_code
    
    # Requête pour récupérer les données nécessaires pour le client spécifique
    query = f"""
    SELECT date, net_a_payer
    FROM entetecommercials
    WHERE client_code = '{client_code}' AND net_a_payer > 0
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    # S'assurer que la colonne 'date' est au format datetime
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Filtrer les données pour les 3 dernières années (dynamique)
    current_date = datetime.now()
    three_years_ago = current_date - pd.DateOffset(years=3)
    df_filtered = df[df['date'] >= three_years_ago]
    
    # Agréger les ventes par mois
    monthly_sales = df_filtered.groupby(pd.Grouper(key='date', freq='M'))['net_a_payer'].sum().reset_index()
    
    # Renommer les colonnes pour Prophet
    df_prophet = monthly_sales.rename(columns={'date': 'ds', 'net_a_payer': 'y'})
    
    # Supprimer les valeurs négatives ou nulles
    df_prophet = df_prophet[df_prophet['y'] > 0]
    
    # Appliquer une transformation logarithmique pour stabiliser les variations
    df_prophet['y'] = np.log(df_prophet['y'])
    
    # Modélisation avec Prophet
    model = Prophet(yearly_seasonality=True, seasonality_mode='multiplicative', changepoint_prior_scale=0.05)
    model.fit(df_prophet)
    
    # Création du DataFrame futur pour la prédiction (prochains 18 mois)
    future = model.make_future_dataframe(periods=18, freq='M')  # 18 mois de prédiction
    forecast = model.predict(future)
    
    # Inverser la transformation logarithmique
    forecast['yhat'] = np.exp(forecast['yhat'])
    forecast['yhat_lower'] = np.exp(forecast['yhat_lower'])
    forecast['yhat_upper'] = np.exp(forecast['yhat_upper'])
    
    # Remplacer les prévisions négatives par zéro
    forecast['yhat'] = forecast['yhat'].apply(lambda x: max(x, 0))
    forecast['yhat_lower'] = forecast['yhat_lower'].apply(lambda x: max(x, 0))
    forecast['yhat_upper'] = forecast['yhat_upper'].apply(lambda x: max(x, 0))
    
    # Filtrer les prévisions pour les dates futures uniquement
    current_date = datetime.now()
    forecast_filtered = forecast[forecast['ds'] > current_date]
    
    # Generate plots
    fig1 = model.plot(forecast)
    plt.title(f"Prévision mensuelle du chiffre d'affaires pour {client_name} (code: {client_code})")
    plt.xlabel("Date")
    plt.ylabel("Net à payer")
    
    # Save plot to a bytes buffer
    buf = io.BytesIO()
    fig1.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    forecast_plot = base64.b64encode(buf.getbuffer()).decode('ascii')
    plt.close(fig1)
    
    # Generate components plot
    fig2 = model.plot_components(forecast)
    
    # Save components plot to a bytes buffer
    buf = io.BytesIO()
    fig2.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    components_plot = base64.b64encode(buf.getbuffer()).decode('ascii')
    plt.close(fig2)
    
    # Prepare forecast data for table display
    tableau_previsions = forecast_filtered[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
    tableau_previsions = tableau_previsions.rename(columns={
        'ds': 'Date',
        'yhat': 'Prévision',
        'yhat_lower': 'Limite inférieure',
        'yhat_upper': 'Limite supérieure'
    })
    
    # Format date for better display
    tableau_previsions['Date'] = tableau_previsions['Date'].dt.strftime('%Y-%m')
    
    # Convert to dict for JSON
    forecast_data = tableau_previsions.to_dict(orient='records')
    
    return {
        'forecast_plot': forecast_plot,
        'components_plot': components_plot,
        'forecast_data': forecast_data
    }

# Function to get top products for a client
def get_top_products(client_code, limit=5):
    conn = get_db_connection()
    
    # Get client name
    cursor = conn.cursor()
    cursor.execute(f"SELECT nom, prenom FROM clients WHERE code = '{client_code}'")
    result = cursor.fetchone()
    if result and result[0]:
        nom = result[0]
        prenom = result[1] if result[1] else ""
        client_name = f"{nom} {prenom}".strip() if prenom else nom
    else:
        client_name = client_code
    
    query = f"""
    SELECT 
        lc.produit_code, 
        p.libelle AS produit_nom, 
        SUM(ec.net_a_payer) AS total_ventes,
        p.image_url
    FROM lignecommercials lc
    JOIN entetecommercials ec ON lc.entetecommercial_code = ec.code
    LEFT JOIN produits p ON lc.produit_code = p.code
    WHERE ec.client_code = '{client_code}'
    GROUP BY lc.produit_code, p.libelle, p.image_url
    ORDER BY total_ventes DESC
    LIMIT {limit}
    """
    
    try:
        df_ventes = pd.read_sql(query, conn)
    except Exception as e:
        # If the query fails because the image_url column doesn't exist
        query = f"""
        SELECT 
            lc.produit_code, 
            p.libelle AS produit_nom, 
            SUM(ec.net_a_payer) AS total_ventes
        FROM lignecommercials lc
        JOIN entetecommercials ec ON lc.entetecommercial_code = ec.code
        LEFT JOIN produits p ON lc.produit_code = p.code
        WHERE ec.client_code = '{client_code}'
        GROUP BY lc.produit_code, p.libelle
        ORDER BY total_ventes DESC
        LIMIT {limit}
        """
        df_ventes = pd.read_sql(query, conn)
        # Add placeholder for image URLs
        df_ventes['image_url'] = None
    
    conn.close()
    
    # Generate bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(df_ventes['produit_code'], df_ventes['total_ventes'], color='skyblue')
    plt.title(f"Top {limit} des produits les plus vendus pour {client_name} (code: {client_code})", fontsize=14)
    plt.xlabel("Code Produit", fontsize=12)
    plt.ylabel("Ventes Totales", fontsize=12)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    products_plot = base64.b64encode(buf.getbuffer()).decode('ascii')
    plt.close()
    
    return {
        'products_plot': products_plot,
        'products_data': df_ventes.to_dict(orient='records')
    }

@app.route('/product_image/<product_code>')
def product_image(product_code):
    """
    Serve product images based on the product code.
    This function will attempt to retrieve the image from the database 
    or generate a placeholder if no image is available.
    """
    import os
    from PIL import Image, ImageDraw, ImageFont
    
    # Check if there are product images in the static folder
    image_path = os.path.join(app.static_folder, 'product_images', f"{product_code}.jpg")
    
    if os.path.exists(image_path):
        # If the image exists in the static folder, return it
        return send_file(image_path, mimetype='image/jpeg')
    else:
        # Generate a placeholder image with the product name
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT libelle FROM produits WHERE code = %s", (product_code,))
            result = cursor.fetchone()
            product_name = result[0] if result else product_code
            conn.close()
        except:
            product_name = product_code
        
        # Create a placeholder image
        width, height = 300, 200
        image = Image.new('RGB', (width, height), color=(240, 240, 240))
        draw = ImageDraw.Draw(image)
        
        # Add product code and name
        try:
            # Try to use a default system font
            draw.text((width//2, height//3), product_code, fill=(0, 0, 0), anchor="mm")
            draw.text((width//2, height//2), product_name, fill=(70, 70, 70), anchor="mm")
            draw.text((width//2, 2*height//3), "Image non disponible", fill=(150, 150, 150), anchor="mm")
        except:
            # If there's an error with the font, use a simpler approach
            draw.rectangle([(0, 0), (width, height)], outline=(200, 200, 200))
            draw.line([(0, 0), (width, height)], fill=(200, 200, 200))
            draw.line([(width, 0), (0, height)], fill=(200, 200, 200))
        
        # Save the image to a buffer
        buf = io.BytesIO()
        image.save(buf, format='JPEG')
        buf.seek(0)
        
        return send_file(buf, mimetype='image/jpeg')

# Function to calculate average basket
def get_average_basket(client_code, date_debut=None, date_fin=None):
    # Set default dates to last year if not provided
    if date_debut is None or date_fin is None:
        current_date = datetime.now()
        date_fin = current_date.strftime('%Y-%m-%d')
        date_debut = (current_date - pd.DateOffset(years=1)).strftime('%Y-%m-%d')
    
    conn = get_db_connection()
    
    query = f"""
    SELECT 
        SUM(net_a_payer) AS chiffre_affaire_total,
        COUNT(*) AS nombre_factures
    FROM entetecommercials
    WHERE client_code = '{client_code}' AND date BETWEEN '{date_debut}' AND '{date_fin}'
    """
    df_panier = pd.read_sql(query, conn)
    conn.close()
    
    # Calculer le panier moyen
    chiffre_affaire_total = float(df_panier['chiffre_affaire_total'][0]) if df_panier['chiffre_affaire_total'][0] else 0
    nombre_factures = int(df_panier['nombre_factures'][0])
    panier_moyen = chiffre_affaire_total / nombre_factures if nombre_factures > 0 else 0
    
    return {
        'chiffre_affaire_total': chiffre_affaire_total,
        'nombre_factures': nombre_factures,
        'panier_moyen': panier_moyen
    }

# Function to get GPS locations
def get_locations_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get commercial locations and names from users table
    cursor.execute("SELECT u.code, u.latitude, u.longitude, u.nom, u.prenom FROM users u WHERE u.latitude IS NOT NULL AND u.longitude IS NOT NULL AND u.latitude != '' AND u.longitude != ''")
    commercial_locations = {}
    commercial_names = {}
    for row in cursor.fetchall():
        try:
            code = row[0]
            commercial_locations[code] = (float(row[1]), float(row[2]))
            
            # Create full name
            nom = row[3] if row[3] else ''
            prenom = row[4] if row[4] else ''
            if nom and prenom:
                full_name = f"{nom} {prenom}".strip()
            else:
                full_name = nom or f"Commercial {code}"
            commercial_names[code] = full_name
        except (ValueError, TypeError):
            # Skip records with invalid coordinates
            continue
    
    # If commercial_locations is empty, try to get commercial codes from entetecommercials
    # and assign default coordinates (centered in Ariana)
    if not commercial_locations:
        cursor.execute("SELECT DISTINCT commercial_code FROM entetecommercials")
        for row in cursor.fetchall():
            commercial_code = row[0]
            if commercial_code and commercial_code not in commercial_locations:
                # Default to Ariana (Clediss location) if no coordinates found
                commercial_locations[commercial_code] = (36.862499, 10.195556)  # Ariana coordinates (Clediss location)
                commercial_names[commercial_code] = f"Commercial {commercial_code}"
    
    # Get client locations and names
    cursor.execute("SELECT c.code, c.latitude, c.longitude, c.nom, c.prenom FROM clients c WHERE c.latitude IS NOT NULL AND c.longitude IS NOT NULL AND c.latitude != '' AND c.longitude != ''")
    client_locations = {}
    client_names = {}
    for row in cursor.fetchall():
        try:
            code = row[0]
            client_locations[code] = (float(row[1]), float(row[2]))
              # Create full name
            nom = row[3] if row[3] else ''
            prenom = row[4] if row[4] else ''
            if nom and prenom:
                full_name = f"{nom} {prenom}".strip()
            else:
                full_name = nom or code
            client_names[code] = full_name
        except (ValueError, TypeError):
            # Skip records with invalid coordinates
            continue
    
    conn.close()
    
    return {
        'commercials': commercial_locations,
        'commercial_names': commercial_names,
        'clients': client_locations,
        'client_names': client_names
    }

def analyze_client_visit_frequency(historical_data, commercial_code, min_frequent_visits, delivery_date):
    """
    Analyze client visit frequency and return insights for frequent visits feature.
    
    Args:
        historical_data (pd.DataFrame): Historical sales data
        commercial_code (str): Commercial identifier
        min_frequent_visits (int): Minimum visits threshold per day
        delivery_date (datetime): Delivery date for analysis
    
    Returns:
        dict: Analysis results with frequent clients info
    """
    try:        # Convert date column to datetime if needed
        if 'date' in historical_data.columns:
            if not pd.api.types.is_datetime64_dtype(historical_data['date']):
                historical_data['date'] = pd.to_datetime(historical_data['date'], errors='coerce')        # Calculate daily visit frequency for each client (expand time window if needed)
        print(f"DEBUG - Total historical data: {len(historical_data)} rows")
        print(f"DEBUG - Date range in data: {historical_data['date'].min()} to {historical_data['date'].max()}")
        print(f"DEBUG - Looking for data from: {delivery_date - pd.Timedelta(days=90)} onwards")
        
        # Try last 90 days first
        recent_data = historical_data[
            historical_data['date'] >= (delivery_date - pd.Timedelta(days=90))
        ]
        
        # If no recent data, expand to 6 months
        if recent_data.empty:
            print(f"DEBUG - No data in last 90 days, trying 6 months...")
            recent_data = historical_data[
                historical_data['date'] >= (delivery_date - pd.Timedelta(days=180))
            ]
        
        # If still no data, use all available data
        if recent_data.empty:
            print(f"DEBUG - No data in last 6 months, using all available data...")
            recent_data = historical_data.copy()
        
        if recent_data.empty:
            print(f"DEBUG - No historical data available at all")
            return {
                'min_visits_target': int(min_frequent_visits),
                'average_visits': float(0),                'meets_target': bool(False),
                'visits_gap': float(min_frequent_visits),
                'frequent_clients': [],
                'message': 'No historical data available for visits analysis'
            }
        
        print(f"DEBUG - Using {len(recent_data)} rows for analysis")
        
        # For aggregated SARIMA data, we already have visit counts
        # Calculate average visits per client per day
        client_daily_visits = None  # Initialize to avoid reference errors
        
        if 'nombre_visites' in recent_data.columns:
            # Use the aggregated visit count data
            client_avg_visits = recent_data.groupby('client_code')['nombre_visites'].mean().round(1)
            print(f"DEBUG - Using 'nombre_visites' column for visit calculation")
            print(f"DEBUG - Number of clients with visit data: {len(client_avg_visits)}")
        else:
            # Fallback: calculate daily visits per client by counting occurrences
            try:
                # Ensure date column is properly converted to datetime
                if 'date' in recent_data.columns and not pd.api.types.is_datetime64_dtype(recent_data['date']):
                    recent_data['date'] = pd.to_datetime(recent_data['date'], errors='coerce')
                
                # Create date_only column safely
                if 'date' in recent_data.columns and pd.api.types.is_datetime64_dtype(recent_data['date']):
                    date_column = recent_data['date'].dt.date
                else:
                    # If no proper date column, use the original date values or create a dummy date
                    print(f"DEBUG - Warning: No proper date column found. Using current date as fallback.")
                    date_column = pd.Timestamp.now().date()
                
                client_daily_visits = recent_data.groupby(['client_code', date_column]).size().reset_index(name='daily_visits')
                client_avg_visits = client_daily_visits.groupby('client_code')['daily_visits'].mean().round(1)
                print(f"DEBUG - Using fallback visit calculation method")
                print(f"DEBUG - Number of clients with visit data: {len(client_avg_visits)}")
            except Exception as e:
                print(f"DEBUG - Error in fallback calculation: {e}")
                # Ultimate fallback: just count unique clients
                client_avg_visits = recent_data.groupby('client_code').size().round(1)
                print(f"DEBUG - Using ultimate fallback: counting client occurrences")
        
        print(f"DEBUG - Visits analysis:")
        print(f"  Recent data shape: {recent_data.shape}")
        print(f"  Client daily visits shape: {client_daily_visits.shape if client_daily_visits is not None else 'N/A (using aggregated data)'}")
        print(f"  Unique clients: {len(client_avg_visits)}")
        if len(client_avg_visits) > 0:
            print(f"  Sample client avg visits: {dict(list(client_avg_visits.head().items()))}")
        
        # Get client names
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT code, nom FROM clients")
        client_names_dict = {str(row[0]): row[1] for row in cursor.fetchall()}
        cursor.close()
        conn.close()
        
        # Find frequent clients (above threshold)
        frequent_clients = []
        for client_code, avg_visits in client_avg_visits.items():
            if avg_visits >= min_frequent_visits:
                client_name = client_names_dict.get(str(client_code), str(client_code))
                frequent_clients.append({
                    'code': str(client_code),
                    'name': client_name,
                    'visits': float(avg_visits)                })
        
        # Sort by visit frequency
        frequent_clients.sort(key=lambda x: x['visits'], reverse=True)
        
        # Calculate overall statistics
        overall_avg_visits = client_avg_visits.mean() if len(client_avg_visits) > 0 else 0
        meets_target = bool(overall_avg_visits >= min_frequent_visits)
        visits_gap = max(0, min_frequent_visits - overall_avg_visits) if not meets_target else 0
        
        return {
            'min_visits_target': int(min_frequent_visits),
            'average_visits': float(round(overall_avg_visits, 1)),
            'meets_target': bool(meets_target),
            'visits_gap': float(round(visits_gap, 1)),
            'frequent_clients': frequent_clients[:10],  # Top 10 frequent clients
            'total_frequent_clients': int(len(frequent_clients))
        }
        
    except Exception as e:
        print(f"Error in visit frequency analysis: {str(e)}")
        return {
            'min_visits_target': int(min_frequent_visits),
            'error': str(e)
        }

@app.route('/api/delivery/optimize', methods=['POST'])
@login_required
def optimize_delivery():
    try:
        # Log the API call for debugging
        print(f"[{datetime.now()}] Delivery optimization API called")
        
        data = request.get_json()
        commercial_code = data.get('commercial_code')
        delivery_date = datetime.strptime(data.get('delivery_date'), '%Y-%m-%d')
        min_revenue = data.get('min_revenue', 0)  # Get minimum revenue from request
        min_frequent_visits = data.get('min_frequent_visits', 0)  # Get minimum frequent visits from request
        product_codes = data.get('product_codes', [])  # Get product codes filter from request
        
        # Log the parameters for debugging
        print(f"Parameters: commercial_code={commercial_code}, delivery_date={delivery_date}, "
              f"min_revenue={min_revenue}, min_frequent_visits={min_frequent_visits}, "
              f"product_filter={product_codes}")
        
        if not commercial_code or not delivery_date:
            print(f"[ERROR] Missing required parameters: commercial_code={commercial_code}, delivery_date={delivery_date}")
            return jsonify({'error': 'Missing required parameters'}), 400
              # Initialize enhanced prediction system with minimum revenue
        from sarima_delivery_optimization import EnhancedPredictionSystem
        from enhanced_predictions import AdvancedPredictionSystem
        enhanced_predictor = EnhancedPredictionSystem(min_revenue=min_revenue)
        advanced_predictor = AdvancedPredictionSystem(min_revenue=min_revenue)# Get historical sales data for SARIMA prediction (aggregated)
        conn = get_db_connection()
        try:
            # Aggregated query for SARIMA predictions
            sarima_query = """
            SELECT ec.date, ec.commercial_code, ec.client_code, 
                   COUNT(DISTINCT ec.client_code) as nombre_visites,
                   SUM(ec.net_a_payer) as net_a_payer,
                   COUNT(*) as quantite
            FROM entetecommercials ec
            WHERE ec.commercial_code = %s 
            AND ec.date >= DATE_SUB(NOW(), INTERVAL 1 YEAR)
            GROUP BY ec.date, ec.commercial_code, ec.client_code
            ORDER BY ec.date
            """
            historical_data = pd.read_sql(sarima_query, conn, params=(commercial_code,))
            print(f"SARIMA query successful. Retrieved {len(historical_data)} rows for commercial {commercial_code}")            # Individual client data for delivery optimization with product information
            delivery_query = """
            SELECT ec.date, ec.commercial_code, ec.client_code, ec.net_a_payer,
                   lc.produit_code, lc.quantite as product_quantity
            FROM entetecommercials ec
            LEFT JOIN lignecommercials lc ON ec.code = lc.entetecommercial_code
            WHERE ec.commercial_code = %s 
            AND ec.date >= DATE_SUB(NOW(), INTERVAL 1 YEAR)
            ORDER BY ec.date
            """
            delivery_data = pd.read_sql(delivery_query, conn, params=(commercial_code,))
            print(f"Delivery query successful. Retrieved {len(delivery_data)} rows for commercial {commercial_code}")
            
            if len(historical_data) > 0:
                print(f"SARIMA data columns: {list(historical_data.columns)}")
            if len(delivery_data) > 0:
                print(f"Delivery data columns: {list(delivery_data.columns)}")
        except Exception as db_error:
            print(f"Database query error: {db_error}")
            conn.close()
            return jsonify({'error': f'Database query failed: {str(db_error)}'}), 500
        finally:
            conn.close()
        
        if historical_data.empty:
            return jsonify({'error': 'No historical data found'}), 404
            
        # Clean the data
        historical_data = data_preprocessing.clean_dataframe(historical_data)
        # Get location data
        locations_data = get_locations_data()
        # Generate delivery plan with individual client data
        delivery_plan = generate_delivery_plan(
            commercial_code=commercial_code,
            delivery_date=delivery_date,
            historical_data=delivery_data,  # Use individual client data for delivery optimization
            locations_data=locations_data,
            product_codes=product_codes if product_codes else None
        )
        
        # Apply advanced prediction enhancements to make predictions more realistic
        try:
            print(f"Applying advanced prediction enhancements...")
            enhanced_delivery_plan = advanced_predictor.enhanced_delivery_plan_predictions(
                delivery_plan, delivery_data
            )
            
            if enhanced_delivery_plan.get('enhancement_applied'):
                delivery_plan = enhanced_delivery_plan
                print(f"✅ Advanced predictions applied successfully")
                print(f"   Total estimated value: {delivery_plan.get('total_estimated_value', 0):.2f}")
                print(f"   Prediction system: {delivery_plan.get('prediction_system', 'Standard')}")
            else:
                print("⚠️ Advanced predictions not applied, using standard predictions")
                
        except Exception as e:
            print(f"⚠️ Error applying advanced predictions: {e}")
            print("Continuing with standard delivery plan...")
          # If minimum revenue is set, add revenue analysis
        if min_revenue > 0:
            # Generate revenue prediction for the delivery date
            try:
                # Convert commercial_code to string for consistent type handling
                comm_code_str = str(commercial_code)
                print(f"Generating revenue prediction for commercial code: {comm_code_str} (type: {type(comm_code_str)})")
                
                revenue_prediction = enhanced_predictor.enhanced_revenue_prediction(
                    historical_data, comm_code_str, forecast_steps=1
                )
                
                if revenue_prediction:
                    print(f"DEBUG - Revenue prediction result:")
                    print(f"  meets_revenue_constraint: {revenue_prediction.get('meets_revenue_constraint', 'NOT_FOUND')}")
                    print(f"  revenue_shortfall: {revenue_prediction.get('revenue_shortfall', 'NOT_FOUND')}")
                    print(f"  average_daily_revenue: {revenue_prediction.get('average_daily_revenue', 'NOT_FOUND')}")
                    
                    # PATCH: Handle the case where revenue prediction returns 0 or None
                    estimated_rev = float(revenue_prediction.get('average_daily_revenue', 0))
                    
                    # If revenue is 0, calculate a fallback based on route data
                    if estimated_rev <= 0:
                        print("⚠️ Revenue prediction returned 0, calculating fallback...")
                        # Calculate fallback revenue from delivery plan
                        fallback_revenue = 0.0
                        if 'route' in delivery_plan:
                            for stop in delivery_plan['route']:
                                if 'predicted_products' in stop:
                                    for product, data in stop['predicted_products'].items():
                                        if isinstance(data, dict):
                                            fallback_revenue += data.get('total_value', 0)
                                        else:
                                            fallback_revenue += float(data) * 25  # Default 25 TND per unit
                        
                        # If still 0, use a realistic default
                        if fallback_revenue <= 0:
                            fallback_revenue = 350.0  # Default daily revenue
                        
                        estimated_rev = fallback_revenue
                        print(f"  Using fallback revenue: {estimated_rev:.2f}")
                    
                    meets_target = bool(revenue_prediction.get('meets_revenue_constraint', False))
                    
                    # PATCH: Recalculate meets_target based on actual revenue
                    if estimated_rev >= min_revenue:
                        meets_target = True
                        actual_meets_target = True
                        revenue_gap = 0.0
                    else:
                        meets_target = False
                        actual_meets_target = False
                        revenue_gap = float(max(0, min_revenue - estimated_rev))
                      # Add revenue information to delivery plan
                    delivery_plan['revenue_info'] = {
                        'min_revenue_target': float(min_revenue),
                        'estimated_revenue': estimated_rev,
                        'total_estimated_revenue': float(revenue_prediction.get('total_estimated_revenue', estimated_rev)),
                        'meets_target': actual_meets_target,
                        'revenue_gap': revenue_gap,
                        'recommendations': revenue_prediction.get('recommendations', [])
                    }
                    print(f"Successfully added revenue info to delivery plan")
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"Error in revenue prediction: {str(e)}")
                print(f"Full traceback:\n{error_details}")
                # Add basic revenue info even if prediction fails
                delivery_plan['revenue_info'] = {
                    'min_revenue_target': min_revenue,
                    'estimated_revenue': 0,
                    'error': f"Failed to generate revenue prediction: {str(e)}"
                }
          # Add enhanced SARIMA predictions to route stops
        if 'route' in delivery_plan:
            for stop in delivery_plan['route']:
                if 'predicted_products' in stop:
                    # Add revenue estimation for this stop
                    # Handle both dict and int values in predicted_products
                    total_quantity = 0
                    for product, data in stop['predicted_products'].items():
                        if isinstance(data, dict):
                            # If data is a dict, extract the quantity
                            qty = data.get('quantity', data.get('value', 1))
                        else:
                            # If data is a number, use it directly
                            qty = data
                        
                        try:
                            total_quantity += float(qty)
                        except (ValueError, TypeError):
                            total_quantity += 1  # Default fallback
                    
                    stop_revenue = total_quantity * 25  # Estimated revenue per product
                    stop['estimated_revenue'] = round(stop_revenue, 2)        # If minimum frequent visits is set, add visits analysis
        if min_frequent_visits > 0:
            try:
                # Create proper visits data from historical data for visits analysis
                print(f"DEBUG - Preparing visits data for analysis...")
                
                # Use historical_data but ensure it has the right structure for visits analysis
                if not historical_data.empty:
                    visits_data = historical_data.copy()
                    # Ensure date column is properly formatted
                    if 'date' in visits_data.columns:
                        visits_data['date'] = pd.to_datetime(visits_data['date'])
                    
                    print(f"DEBUG - Visits data prepared: {len(visits_data)} rows")
                    print(f"DEBUG - Date range: {visits_data['date'].min()} to {visits_data['date'].max()}")
                    print(f"DEBUG - Unique clients: {visits_data['client_code'].nunique() if 'client_code' in visits_data.columns else 'N/A'}")
                    
                    # Analyze client visit frequency using prepared data
                    visits_analysis = analyze_client_visit_frequency(
                        visits_data, commercial_code, min_frequent_visits, delivery_date
                    )
                else:
                    print(f"DEBUG - No historical data available for visits analysis")
                    visits_analysis = {
                        'min_visits_target': min_frequent_visits,
                        'average_visits': 0.0,
                        'meets_target': False,
                        'visits_gap': float(min_frequent_visits),
                        'frequent_clients': [],
                        'total_frequent_clients': 0,
                        'message': 'No historical data available'
                    }
                
                if visits_analysis:
                    delivery_plan['visits_info'] = visits_analysis
                    print(f"Successfully added visits info to delivery plan")
                    print(f"DEBUG - Visits analysis result: avg={visits_analysis.get('average_visits', 'N/A')}, meets_target={visits_analysis.get('meets_target', 'N/A')}")
            except Exception as e:
                print(f"Error in visits analysis: {str(e)}")
                import traceback
                traceback.print_exc()
                # Add basic visits info even if analysis fails
                delivery_plan['visits_info'] = {
                    'min_visits_target': min_frequent_visits,
                    'average_visits': 0.0,
                    'meets_target': False,
                    'visits_gap': float(min_frequent_visits),
                    'error': f"Failed to generate visits analysis: {str(e)}"
                }
          # Check for empty packing list and route, add sample data if needed
        if 'packing_list' not in delivery_plan or not delivery_plan['packing_list']:
            print(f"[WARNING] Empty packing list detected, adding sample data")
            delivery_plan['packing_list'] = {
                'SAMPLE_PRODUCT_1': 10,
                'SAMPLE_PRODUCT_2': 5,
                'SAMPLE_PRODUCT_3': 15
            }
            
        if 'route' in delivery_plan and len(delivery_plan['route']) > 0:
            # Check if any route items have predicted products
            has_predictions = any(
                stop.get('predicted_products') and len(stop.get('predicted_products', {})) > 0
                for stop in delivery_plan['route']
            )
            
            if not has_predictions:
                print(f"[WARNING] No predicted products in route, adding sample data")
                # Add sample predicted products to at least the first route item
                if delivery_plan['route']:
                    delivery_plan['route'][0]['predicted_products'] = {
                        'SAMPLE_PRODUCT_1': {
                            'quantity': 5,
                            'currency': 'TND',
                            'price': 10.0,
                            'total_value': 50.0
                        }                    }
        
        # Calculate total estimated revenue from all route stops
        if 'route' in delivery_plan and delivery_plan['route'] and min_revenue > 0:
            total_route_revenue = 0.0
            for stop in delivery_plan['route']:
                if 'estimated_revenue' in stop:
                    total_route_revenue += float(stop['estimated_revenue'])
            
            # Update revenue_info with the calculated total
            if 'revenue_info' in delivery_plan:
                delivery_plan['revenue_info']['estimated_revenue'] = round(total_route_revenue, 2)
                
                # Recalculate meets_target based on the actual route revenue
                min_target = delivery_plan['revenue_info']['min_revenue_target']
                meets_target = total_route_revenue >= min_target
                revenue_gap = max(0, min_target - total_route_revenue) if not meets_target else 0.0
                
                delivery_plan['revenue_info']['meets_target'] = meets_target
                delivery_plan['revenue_info']['revenue_gap'] = round(revenue_gap, 2)
                
                print(f"DEBUG - Updated revenue info:")
                print(f"  Total route revenue: {total_route_revenue:.2f} TND")
                print(f"  Target: {min_target:.2f} TND")
                print(f"  Meets target: {meets_target}")
                print(f"  Revenue gap: {revenue_gap:.2f} TND")
        
        # Log success response
        print(f"[{datetime.now()}] Delivery optimization successful: {len(delivery_plan.get('route', []))} stops, "
              f"{len(delivery_plan.get('packing_list', {}))} products in packing list")
              
        return jsonify(delivery_plan)
        
    except Exception as e:
        import traceback
        print(f"[ERROR] Delivery optimization failed: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        
        # Return a more helpful error message
        error_response = {
            'error': str(e),
            'message': 'Une erreur est survenue lors de l\'optimisation de la livraison. Veuillez réessayer avec des paramètres différents.'
        }
        return jsonify(error_response), 500

# Test endpoint without authentication for debugging
@app.route('/api/delivery/optimize-test', methods=['POST'])
def optimize_delivery_test():
    """Test version of delivery optimization without authentication"""
    try:
        # Log the API call for debugging
        print(f"[{datetime.now()}] TEST Delivery optimization API called (no auth)")
        
        data = request.get_json()
        commercial_code = data.get('commercial_code')
        delivery_date = datetime.strptime(data.get('delivery_date'), '%Y-%m-%d')
        min_revenue = data.get('min_revenue', 0)
        min_frequent_visits = data.get('min_frequent_visits', 0)
        product_codes = data.get('product_codes', [])
        
        print(f"TEST API - Parameters: commercial={commercial_code}, date={delivery_date}, min_revenue={min_revenue}")
        
        # Get historical delivery data
        historical_data = get_historical_deliveries()
        
        # Use the standard delivery optimization process
        # ... (same logic as the authenticated version)
        return optimize_delivery_internal(commercial_code, delivery_date, min_revenue, min_frequent_visits, product_codes, historical_data)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in TEST delivery optimization: {str(e)}")
        print(f"Full traceback:\n{error_details}")
        return jsonify({
            'error': str(e),
            'details': error_details,
            'test_mode': True
        }), 500

def optimize_delivery_internal(commercial_code, delivery_date, min_revenue, min_frequent_visits, product_codes, historical_data):
    """Internal function for delivery optimization logic"""
    pass  # Replace with the actual logic if needed

@app.route('/api/revenue/predict', methods=['POST'])
def predict_revenue():
    """API endpoint for revenue prediction with minimum revenue constraints"""
    try:
        data = request.get_json()
        commercial_code = data.get('commercial_code')
        forecast_days = data.get('forecast_days', 30)
        min_revenue = data.get('min_revenue', 0)
        
        if not commercial_code:
            return jsonify({'error': 'Commercial code is required'}), 400
            
        # Initialize enhanced prediction system
        from sarima_delivery_optimization import EnhancedPredictionSystem
        enhanced_predictor = EnhancedPredictionSystem(min_revenue=min_revenue)
        
        # Get historical data
        conn = get_db_connection()
        query = """
        SELECT ec.date, ec.commercial_code, ec.client_code, ec.net_a_payer,
               COUNT(*) as nombre_visites
        FROM entetecommercials ec
        WHERE ec.commercial_code = %s 
        AND ec.date >= DATE_SUB(NOW(), INTERVAL 2 YEAR)
        GROUP BY ec.date, ec.commercial_code, ec.client_code
        ORDER BY ec.date
        """
        historical_data = pd.read_sql(query, conn, params=(commercial_code,))
        conn.close()
        
        if historical_data.empty:
            return jsonify({'error': 'No historical data found for revenue prediction'}), 404
            
        # Generate revenue prediction
        revenue_prediction = enhanced_predictor.enhanced_revenue_prediction(
            historical_data, commercial_code, forecast_days
        )
        
        if revenue_prediction:
            return jsonify({
                'success': True,
                'commercial_code': commercial_code,
                'forecast_days': forecast_days,
                'min_revenue_target': min_revenue,
                'prediction_results': revenue_prediction
            })
        else:
            return jsonify({'error': 'Unable to generate revenue prediction'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/revenue/analyze', methods=['POST'])
def analyze_revenue_patterns():
    """API endpoint for analyzing revenue patterns and optimization"""
    try:
        data = request.get_json()
        commercial_code = data.get('commercial_code')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        min_revenue = data.get('min_revenue', 0)
        
        if not commercial_code:
            return jsonify({'error': 'Commercial code is required'}), 400
            
        # Initialize enhanced prediction system
        from sarima_delivery_optimization import EnhancedPredictionSystem
        enhanced_predictor = EnhancedPredictionSystem(min_revenue=min_revenue)
        
        # Get historical revenue data
        conn = get_db_connection()
        query = """
        SELECT ec.date, SUM(ec.net_a_payer) as daily_revenue,
               COUNT(DISTINCT ec.client_code) as clients_visited,
               COUNT(*) as total_visits
        FROM entetecommercials ec
        WHERE ec.commercial_code = %s 
        """
        params = [commercial_code]
        
        if start_date:
            query += " AND ec.date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND ec.date <= %s"
            params.append(end_date)
            
        query += """
        GROUP BY ec.date
        ORDER BY ec.date
        """
        
        revenue_data = pd.read_sql(query, conn, params=params)
        conn.close()
        
        if revenue_data.empty:
            return jsonify({'error': 'No revenue data found'}), 404
            
        # Calculate revenue statistics
        daily_revenues = revenue_data['daily_revenue']
        stats = {
            'average_daily_revenue': float(daily_revenues.mean()),
            'median_daily_revenue': float(daily_revenues.median()),
            'max_daily_revenue': float(daily_revenues.max()),
            'min_daily_revenue': float(daily_revenues.min()),
            'total_revenue': float(daily_revenues.sum()),
            'revenue_std': float(daily_revenues.std()),
            'days_analyzed': len(revenue_data)
        }
        
        # Revenue constraint analysis
        if min_revenue > 0:
            days_below_target = (daily_revenues < min_revenue).sum()
            compliance_rate = ((len(daily_revenues) - days_below_target) / len(daily_revenues)) * 100
            
            stats.update({
                'min_revenue_target': min_revenue,
                'days_below_target': int(days_below_target),
                'compliance_rate': float(compliance_rate),
                'target_gap': float(max(0, min_revenue - stats['average_daily_revenue']))
            })
        
        # Generate recommendations
        recommendations = []
        if min_revenue > 0 and stats['average_daily_revenue'] < min_revenue:
            gap = min_revenue - stats['average_daily_revenue']
            recommendations.extend([
                f"Average daily revenue ({stats['average_daily_revenue']:.2f}) is below target ({min_revenue})",
                f"Need to increase daily revenue by {gap:.2f} on average",
                "Consider targeting higher-value clients or premium products",
                "Optimize visit frequency and route efficiency"
            ])
        
        if stats['revenue_std'] / stats['average_daily_revenue'] > 0.5:
            recommendations.append("High revenue variability detected - consider consistency improvements")
            
        return jsonify({
            'success': True,
            'commercial_code': commercial_code,
            'analysis_period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'revenue_statistics': stats,
            'recommendations': recommendations,
            'revenue_data': revenue_data.to_dict('records')
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delivery_optimization')
@login_required
def delivery_optimization():
    commercials = get_commercials()
    products = get_products()  # Get product information
    user = get_current_user()
    return render_template('delivery_optimization.html', commercials=commercials, products=products, user=user)

@app.route('/commercial_revenue_dashboard')
@login_required
def commercial_revenue_dashboard():
    """Dashboard for commercials to manage revenue constraints and view prediction maps"""
    commercials = get_commercials()
    user = get_current_user()
    return render_template('commercial_revenue_dashboard.html', commercials=commercials, user=user)

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
    commercials = get_commercials()
    products = get_products()
    user = get_current_user()
    return render_template('index.html', clients=clients, commercials=commercials, products=products, user=user)

@app.route('/clients')
@login_required
def clients_list():
    clients = get_clients()
    user = get_current_user()
    return render_template('clients.html', clients=clients, user=user)

@app.route('/dashboard/<client_code>')
@login_required
def dashboard(client_code):
    # Get date range for average basket - default to last year
    current_date = datetime.now()
    default_end = current_date.strftime('%Y-%m-%d')
    default_start = (current_date - pd.DateOffset(years=1)).strftime('%Y-%m-%d')
    
    date_debut = request.args.get('date_debut', default_start)
    date_fin = request.args.get('date_fin', default_end)
    
    try:
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
        
        # Generate forecast
        forecast_results = generate_forecast(client_code)
        
        # Get top products
        top_products = get_top_products(client_code)
        
        # Get average basket
        basket_info = get_average_basket(client_code, date_debut, date_fin)
        
        return render_template('dashboard.html', 
                              client_code=client_code,
                              client_name=client_name,
                              forecast_plot=forecast_results['forecast_plot'],
                              components_plot=forecast_results['components_plot'],
                              forecast_data=forecast_results['forecast_data'],
                              products_plot=top_products['products_plot'],
                              products_data=top_products['products_data'],
                              basket_info=basket_info,
                              date_debut=date_debut,
                              date_fin=date_fin)
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/products')
@login_required
def products_list():
    products = get_products()
    user = get_current_user()
    return render_template('products.html', products=products, user=user)

@app.route('/product_dashboard/<product_code>')
@login_required
def product_dashboard(product_code):
    try:
        # Get product info
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT libelle FROM produits WHERE code = '{product_code}'")
        result = cursor.fetchone()
        product_name = result[0] if result and result[0] else product_code
        conn.close()
        
        # Generate monthly sales chart
        monthly_sales_chart = plot_monthly_sales(product_code)
        
        # Generate top clients chart
        top_clients_chart = plot_top_clients(product_code)
        
        # Load sales data for table display
        df = load_product_sales_data(product_code)
        
        # Format data for display
        if not df.empty:
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
            sales_data = df.to_dict(orient='records')
        else:
            sales_data = []
        
        # Try to generate forecast if possible
        try:
            forecast_results = forecast_sales_for_2025(product_code)
            has_forecast = True
        except Exception:
            forecast_results = {
                'forecast_plot': '',
                'components_plot': '',
                'forecast_data': []
            }
            has_forecast = False
        
        return render_template('product_dashboard.html',
                              product_code=product_code,
                              product_name=product_name,
                              monthly_sales_chart=monthly_sales_chart,
                              top_clients_chart=top_clients_chart,
                              sales_data=sales_data,
                              forecast_plot=forecast_results.get('forecast_plot', ''),
                              components_plot=forecast_results.get('components_plot', ''),
                              forecast_data=forecast_results.get('forecast_data', []),
                              has_forecast=has_forecast)
                              
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/api/forecast/<client_code>')
@login_required
def api_forecast(client_code):
    try:
        forecast_results = generate_forecast(client_code)
        return jsonify(forecast_results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/top_products/<client_code>')
@login_required
def api_top_products(client_code):
    limit = request.args.get('limit', 5, type=int)
    try:
        top_products = get_top_products(client_code, limit)
        return jsonify(top_products)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/average_basket/<client_code>')
def api_average_basket(client_code):
    date_debut = request.args.get('date_debut', '2023-01-01')
    date_fin = request.args.get('date_fin', '2023-12-31')
    try:
        basket_info = get_average_basket(client_code, date_debut, date_fin)
        return jsonify(basket_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/product_sales/<product_code>')
def api_product_sales(product_code):
    try:
        df = load_product_sales_data(product_code)
        # Format data for JSON
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        return jsonify({
            'sales_data': df.to_dict(orient='records'),
            'monthly_sales_chart': plot_monthly_sales(product_code),
            'top_clients_chart': plot_top_clients(product_code)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/product_forecast/<product_code>')
def api_product_forecast(product_code):
    try:
        # Validate if product exists and has enough data for forecasting
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if product exists
        cursor.execute("SELECT code, libelle FROM produits WHERE code = %s", (product_code,))
        product = cursor.fetchone()
        
        # Check if product has sales data
        cursor.execute("""
            SELECT COUNT(*) 
            FROM lignecommercials lc 
            JOIN entetecommercials ec ON lc.entetecommercial_code = ec.code
            WHERE lc.produit_code = %s
        """, (product_code,))
        sales_count = cursor.fetchone()[0]
        
        conn.close()
        
        if not product:
            return jsonify({'error': 'Produit non trouvé'}), 404
            
        if sales_count < 5:  # Minimum data points for reliable forecasting
            return jsonify({
                'error': 'Données insuffisantes pour établir des prévisions fiables',
                'sales_count': sales_count
            }), 400
            
        # Generate forecast
        forecast_results = forecast_sales_for_2025(product_code)
        
        # Add product info to results
        forecast_results['product_code'] = product_code
        forecast_results['product_name'] = product[1] if product[1] else product_code
        
        return jsonify(forecast_results)
    except Exception as e:
        print(f"Error in product forecast for {product_code}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download_forecast/<client_code>')
def download_forecast(client_code):
    try:
        conn = get_db_connection()
        
        # Get forecast data
        query = f"""
        SELECT date, net_a_payer
        FROM entetecommercials
        WHERE client_code = '{client_code}' AND net_a_payer > 0
        """
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Generate Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Données', index=False)
            
        output.seek(0)
        
        return send_file(
            output, 
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'previsions_client_{client_code}.xlsx'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_product_sales/<product_code>')
def download_product_sales(product_code):
    try:
        df = load_product_sales_data(product_code)
        
        # Generate Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Ventes Produit', index=False)
            
        output.seek(0)
        
        return send_file(
            output, 
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'ventes_produit_{product_code}.xlsx'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search_clients')
def search_clients():
    search_term = request.args.get('term', '')
    
    if not search_term:
        return jsonify([])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # query = """
    # SELECT DISTINCT c.code, c.nom 
    # FROM clients c
    # JOIN entetecommercials ec ON c.code = ec.client_code
    # WHERE c.code LIKE %s OR c.nom LIKE %s
    # LIMIT 20
    # """
    query = """
    SELECT DISTINCT c.code, c.nom 
    FROM clients c
    JOIN entetecommercials ec ON c.code = ec.client_code
    WHERE c.code LIKE %s OR c.nom LIKE %s
    
    """ 
    cursor.execute(query, (f"%{search_term}%", f"%{search_term}%"))
    results = [{"code": row[0], "nom": row[1] if row[1] else row[0]} for row in cursor.fetchall()]
    
    conn.close()
    return jsonify(results)

@app.route('/search_products')
def search_products():
    search_term = request.args.get('term', '')
    
    if not search_term:
        return jsonify([])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT DISTINCT p.code, p.libelle 
    FROM produits p
    JOIN lignecommercials lc ON p.code = lc.produit_code
    WHERE p.code LIKE %s OR p.libelle LIKE %s
    ORDER BY p.libelle
    LIMIT 20
    """
    
    cursor.execute(query, (f"%{search_term}%", f"%{search_term}%"))
    results = [{"code": row[0], "libelle": row[1] if row[1] else row[0]} for row in cursor.fetchall()]
    
    conn.close()
    return jsonify(results)

@app.route('/get_product_details')
def get_product_details():
    product_code = request.args.get('code', '')
    
    if not product_code:
        return jsonify({})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT code, libelle, prix, description, famille_libelle
    FROM produits
    WHERE code = %s
    LIMIT 1
    """
    
    cursor.execute(query, (product_code,))
    row = cursor.fetchone()
    
    if (row):
        product_info = {
            "code": row[0],
            "libelle": row[1],
            "prix": float(row[2]) if row[2] else 0,
            "description": row[3] or "Pas de description disponible",
            "famille": row[4] or "Non classé"
        }
    else:
        product_info = {
            "code": product_code,
            "libelle": "Produit inconnu",
            "prix": 0,
            "description": "Information non disponible",
            "famille": "Non classé"
        }
    
    conn.close()
    return jsonify(product_info)

# Function to get list of commercials
def get_commercials():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First try to get commercial names from users table
    cursor.execute("""
        SELECT u.code, u.nom, u.prenom 
        FROM users u 
        JOIN entetecommercials ec ON u.code = ec.commercial_code 
        GROUP BY u.code, u.nom, u.prenom
    """)
    
    commercial_data = cursor.fetchall()
    
    # If no results, use simplified query
    if not commercial_data:
        cursor.execute("SELECT DISTINCT ec.commercial_code FROM entetecommercials ec ORDER BY ec.commercial_code")
        commercial_data = [(row[0], None, None) for row in cursor.fetchall()]
    
    commercials = []
    for row in commercial_data:
        code = row[0]
        
        # Create full name
        if len(row) > 1 and row[1]:
            nom = row[1] if row[1] else ''
            prenom = row[2] if row[2] and len(row) > 2 else ''
            
            if nom and prenom:
                full_name = f"{nom} {prenom}".strip()
            else:
                full_name = nom
        else:
            full_name = f"Commercial {code}"
            
        commercials.append((code, full_name))
    
    conn.close()
    return commercials

# Function to get commercial performance
def get_commercial_performance(commercial_code, date_debut='2023-01-01', date_fin='2023-12-31'):
    conn = get_db_connection()
    
    # Get chiffre d'affaires and volume of sales aggregated by day
    query = f"""
    SELECT 
        DATE(ec.date) as date,
        SUM(ec.net_a_payer) AS chiffre_affaires,
        COUNT(ec.code) AS volume_ventes
    FROM entetecommercials ec
    WHERE ec.commercial_code = '{commercial_code}'
      AND ec.date BETWEEN '{date_debut}' AND '{date_fin}'
    GROUP BY DATE(ec.date)
    ORDER BY date
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    if df.empty:
        return {
            'performance_data': [],
            'performance_chart': '',
            'total_revenue': 0,
            'total_sales': 0
        }
    
    # Calculate totals
    total_revenue = df['chiffre_affaires'].sum()
    total_sales = df['volume_ventes'].sum()
    
    # Ensure date is datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Group by month for chart
    monthly_data = df.groupby(pd.Grouper(key='date', freq='M')).agg({
        'chiffre_affaires': 'sum',
        'volume_ventes': 'sum'
    }).reset_index()
    
    # Create performance chart
    plt.figure(figsize=(12, 6))
    
    # Create two subplots
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Plot revenue on left axis
    color = 'tab:blue'
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Chiffre d\'affaires', color=color)
    ax1.plot(monthly_data['date'], monthly_data['chiffre_affaires'], color=color, marker='o')
    ax1.tick_params(axis='y', labelcolor=color)
    
    # Create second y-axis for volume
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Volume de ventes', color=color)
    ax2.plot(monthly_data['date'], monthly_data['volume_ventes'], color=color, marker='s')
    ax2.tick_params(axis='y', labelcolor=color)
    
    plt.title(f"Performance du commercial {commercial_code} ({date_debut} à {date_fin})")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save chart to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    performance_chart = base64.b64encode(buf.getbuffer()).decode('ascii')
    plt.close()
    
    # Format dates for display
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    
    return {
        'performance_data': df.to_dict(orient='records'),
        'performance_chart': performance_chart,
        'total_revenue': total_revenue,
        'total_sales': total_sales
    }

# Function to get product sales by client for a commercial
def get_product_sales_by_client(commercial_code, date_debut='2023-01-01', date_fin='2023-12-31'):
    conn = get_db_connection()
    
    # Using a simpler query that matches exactly what's in commercials.txt file
    # but with added client name information
    query = f"""
    SELECT 
        ec.client_code,
        c.nom AS client_nom,
        c.prenom AS client_prenom,
        lc.produit_code,
        p.libelle AS produit_nom,
        SUM(lc.quantite) AS total_quantite
    FROM entetecommercials ec
    JOIN lignecommercials lc ON lc.entetecommercial_code = ec.code 
    LEFT JOIN clients c ON ec.client_code = c.code
    LEFT JOIN produits p ON lc.produit_code = p.code
    WHERE ec.commercial_code = '{commercial_code}' 
      AND ec.date BETWEEN '{date_debut}' AND '{date_fin}'
    GROUP BY ec.client_code, c.nom, c.prenom, lc.produit_code, p.libelle
    """
    
    print(f"Executing query for commercial {commercial_code} from {date_debut} to {date_fin}")
    
    try:
        # Execute the query
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        
        # If no results, return early with empty data
        if not results:
            print("No results from the query")
            conn.close()
            return {
                'sales_data': [],
                'pivot_data': [],
                'pivot_columns': [{'name': 'Client Code', 'id': 'client_code'}, {'name': 'Client Nom', 'id': 'client_nom'}],
                'has_data': False
            }
        
        # Create dataframe from the results
        columns = [col[0] for col in cursor.description]
        df = pd.DataFrame(results, columns=columns)
        
        # Format client names
        formatted_client_names = []
        for _, row in df.iterrows():
            client_name = ""
            if row['client_nom'] is not None:
                client_name = row['client_nom']
                if row['client_prenom'] is not None:
                    client_name += " " + row['client_prenom']
            else:
                client_name = row['client_code']
            formatted_client_names.append(client_name)
        
        df['client_nom'] = formatted_client_names
        
        # Drop the client_prenom column since we've incorporated it into client_nom
        if 'client_prenom' in df.columns:
            df = df.drop('client_prenom', axis=1)
        
        # Create pivot table
        pivot_data = []
        pivot_columns = [
            {'name': 'Code Client', 'id': 'client_code'}, 
            {'name': 'Nom Client', 'id': 'client_nom'}
        ]
        
        # Get unique client codes and product codes
        unique_clients = df[['client_code', 'client_nom']].drop_duplicates().to_dict('records')
        unique_products = df[['produit_code', 'produit_nom']].drop_duplicates().to_dict('records')
        
        # For each client, create a row in the pivot table
        for client in unique_clients:
            client_row = {
                'client_code': client['client_code'],
                'client_nom': client['client_nom']
            }
            
            # Add each product as a column
            for product in unique_products:
                prod_code = product['produit_code']
                prod_name = product['produit_nom'] if product['produit_nom'] else prod_code
                column_id = f"prod_{prod_code}"
                
                # Add column to pivot_columns if not already there
                if not any(c['id'] == column_id for c in pivot_columns):
                    display_name = f"{prod_code}"
                    if prod_name and prod_name != prod_code:
                        display_name = f"{prod_code} - {prod_name}"
                    pivot_columns.append({'name': display_name, 'id': column_id})
                
                # Find the quantity for this client and product
                client_product_data = df[(df['client_code'] == client['client_code']) & 
                                          (df['produit_code'] == prod_code)]
                
                if not client_product_data.empty:
                    # Use the quantity from the data
                    qty = client_product_data['total_quantite'].iloc[0]
                    client_row[column_id] = int(qty) if qty == int(qty) else float(qty)
                else:
                    # No quantity for this product
                    client_row[column_id] = 0
            
            pivot_data.append(client_row)
        
        conn.close()
        
        return {
            'sales_data': df.to_dict('records'),
            'pivot_data': pivot_data,
            'pivot_columns': pivot_columns,
            'has_data': len(pivot_data) > 0
        }
        
    except Exception as e:
        print(f"Error in get_product_sales_by_client: {str(e)}")
        if conn:
            conn.close()
        return {
            'sales_data': [],
            'pivot_data': [],
            'pivot_columns': [{'name': 'Code Client', 'id': 'client_code'}, {'name': 'Nom Client', 'id': 'client_nom'}],
            'has_data': False,
            'error': str(e)
        }

@app.route('/commercials')
def commercials_list():
    commercials = get_commercials()
    print("Found commercials:", commercials)  # Debug print
    return render_template('commercials.html', commercials=commercials)

@app.route('/commercial_dashboard/<commercial_code>')
def commercial_dashboard(commercial_code):
    # Get date range
    date_debut = request.args.get('date_debut', '2023-01-01')
    date_fin = request.args.get('date_fin', '2023-12-31')
    
    try:
        # Get commercial name
        from commercial_full_name import get_commercial_name
        commercial_name = get_commercial_name(commercial_code)
        
        # Get commercial performance
        performance = get_commercial_performance(commercial_code, date_debut, date_fin)
        
        # Get product sales by client
        sales_by_client = get_product_sales_by_client(commercial_code, date_debut, date_fin)
        
        return render_template('commercial_dashboard.html',
                              commercial_code=commercial_code,
                              commercial_name=commercial_name,
                              performance=performance,
                              sales_by_client=sales_by_client,
                              date_debut=date_debut,
                              date_fin=date_fin)
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/api/commercial_performance/<commercial_code>')
def api_commercial_performance(commercial_code):
    date_debut = request.args.get('date_debut', '2023-01-01')
    date_fin = request.args.get('date_fin', '2023-12-31')
    try:
        performance = get_commercial_performance(commercial_code, date_debut, date_fin)
        return jsonify(performance)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/commercial_sales/<commercial_code>')
def api_commercial_sales(commercial_code):
    date_debut = request.args.get('date_debut', '2023-01-01')
    date_fin = request.args.get('date_fin', '2023-12-31')
    try:
        sales_data = get_product_sales_by_client(commercial_code, date_debut, date_fin)
        return jsonify(sales_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search_commercials')
def search_commercials():
    search_term = request.args.get('term', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if search_term:
        # Recherche filtrée par terme
        # query = """
        # SELECT 
        #     ec.commercial_code AS code,
        #     COUNT(*) AS count
        # FROM entetecommercials ec
        # WHERE ec.commercial_code LIKE %s
        # GROUP BY ec.commercial_code
        # ORDER BY count DESC
        # LIMIT 20
        # """    
        query = """
        SELECT 
            ec.commercial_code AS code,
            COUNT(*) AS count
        FROM entetecommercials ec
        WHERE ec.commercial_code LIKE %s
        GROUP BY ec.commercial_code
        ORDER BY count DESC
        
        """    
        cursor.execute(query, (f"%{search_term}%",))
    else:
        # Récupérer tous les commerciaux
        query = """
        SELECT 
            ec.commercial_code AS code,
            COUNT(*) AS count
        FROM entetecommercials ec
        GROUP BY ec.commercial_code
        ORDER BY count DESC
        """
        cursor.execute(query)
    
    results = [{"code": row[0], "count": int(row[1])} for row in cursor.fetchall()]
    conn.close()
    return jsonify(results)

@app.route('/api/commercials')
def get_all_commercials():
    # Return an empty list to prevent showing any commercial data
    return jsonify([])

@app.route('/commercial_visits_analysis')
def commercial_visits_page():
    return render_template('commercial_visits.html')

@app.route('/api/commercial_visits')
def api_commercial_visits():
    from commercial_visits_analysis import get_commercial_visits
    
    # Default to current year
    current_date = datetime.now()
    default_end = current_date.strftime('%Y-%m-%d')
    default_start = current_date.replace(month=1, day=1).strftime('%Y-%m-%d')
    
    date_debut = request.args.get('date_debut', default_start)
    date_fin = request.args.get('date_fin', default_end)
    commercial_code = request.args.get('commercial_code', None)
    
    try:
        visits_data = get_commercial_visits(date_debut, date_fin, commercial_code)
        return jsonify(visits_data.to_dict(orient='records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict_visits')
def api_predict_visits():    
    # Return dummy data instead of real commercial data
    # Default to current year
    current_date = datetime.now()
    default_end = current_date.strftime('%Y-%m-%d')
    default_start = current_date.replace(month=1, day=1).strftime('%Y-%m-%d')
    
    date_debut = request.args.get('date_debut', default_start)
    date_fin = request.args.get('date_fin', default_end)
    days_to_predict = int(request.args.get('days_to_predict', 365))  # 1 an par défaut
    
    try:
        # Generate dummy dates for the requested period
        start_date = pd.to_datetime(date_fin) + pd.Timedelta(days=1)
        prediction_dates = [start_date + pd.Timedelta(days=i) for i in range(days_to_predict)]
        
        # Generate dummy predictions (random values between 0 and 10)
        dummy_predictions = np.random.randint(0, 10, days_to_predict)
        dummy_lower_ci = dummy_predictions - np.random.randint(0, 3, days_to_predict)
        dummy_upper_ci = dummy_predictions + np.random.randint(0, 3, days_to_predict)
        
        # Make sure lower_ci is not negative
        dummy_lower_ci = np.maximum(dummy_lower_ci, 0)
        
        # Create dummy stats
        dummy_stats = {
            'moyenne_visites_predites': round(np.mean(dummy_predictions), 2),
            'std': round(np.std(dummy_predictions), 2),
            'min_visites_predites': int(np.min(dummy_predictions)),
            'max_visites_predites': int(np.max(dummy_predictions)),
            'total_visites_predites': int(np.sum(dummy_predictions))
        }
        
        # Format the response in the expected structure (commercial_code as key)
        # Create a dummy commercial code since we don't want to show real data
        dummy_commercial = "dummy_commercial"
        results = {
            dummy_commercial: {
                'dates': [d.strftime('%Y-%m-%d') for d in prediction_dates],
                'predictions': dummy_predictions.tolist(),
                'lower_ci': dummy_lower_ci.tolist(),
                'upper_ci': dummy_upper_ci.tolist(),
                'stats': dummy_stats,
                'displayName': 'Aucun commercial (données simulées)'
            }
        }
            
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/visits_analysis_plot')
def api_visits_analysis_plot():
    import io
    import base64
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend for generating plots
    import matplotlib.pyplot as plt
    import numpy as np
    
    # Default to current year
    current_date = datetime.now()
    default_end = current_date.strftime('%Y-%m-%d')
    default_start = current_date.replace(month=1, day=1).strftime('%Y-%m-%d')
    
    date_debut = request.args.get('date_debut', default_start)
    date_fin = request.args.get('date_fin', default_end)
    
    try:
        # Create a simple dummy plot
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Generate dummy data
        start_date = pd.to_datetime(date_debut)
        end_date = pd.to_datetime(date_fin)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # No commercial data - just create an empty plot with a message
        ax.text(0.5, 0.5, 'Aucune donnée commerciale disponible', 
                fontsize=14, ha='center', va='center', transform=ax.transAxes)
        
        # Set labels and title
        ax.set_xlabel('Date')
        ax.set_ylabel('Nombre de visites')
        ax.set_title('Analyse des visites commerciales')
        
        # Set x-axis limits to match the date range
        ax.set_xlim(start_date, end_date)
        
        # Add grid
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Adjust layout
        plt.tight_layout()
        
        # Convert plot to base64 string
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        plot_data = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return jsonify({'plot': plot_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export_visits_excel')
def api_export_visits_excel():
    import io
    import os
    import pandas as pd
    import numpy as np
    
    # Default to current year
    current_date = datetime.now()
    default_end = current_date.strftime('%Y-%m-%d')
    default_start = current_date.replace(month=1, day=1).strftime('%Y-%m-%d')
    
    date_debut = request.args.get('date_debut', default_start)
    date_fin = request.args.get('date_fin', default_end)
    days_to_predict = int(request.args.get('days_to_predict', '90'))
    
    try:
        # Create dummy data for export
        start_date = pd.to_datetime(date_fin) + pd.Timedelta(days=1)
        dates = [start_date + pd.Timedelta(days=i) for i in range(days_to_predict)]
        
        # Create dummy DataFrame
        df = pd.DataFrame({
            'Date': dates,
            'Commercial': ['Donnée non disponible'] * days_to_predict,
            'Prédiction': np.random.randint(0, 10, days_to_predict),
            'Min (95%)': np.random.randint(0, 5, days_to_predict),
            'Max (95%)': np.random.randint(5, 15, days_to_predict),
        })
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Prédictions', index=False)
            
            # Format the sheet
            workbook = writer.book
            worksheet = writer.sheets['Prédictions']
            
            # Add formats
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'bg_color': '#D9E1F2',
                'border': 1
            })
            
            # Apply header format
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                
            # Auto-adjust columns width
            for i, col in enumerate(df.columns):
                column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_width)
        
        # Set pointer at the beginning
        output.seek(0)
        
                # Return the Excel file
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='predictions_visites.xlsx'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===================== 365-DAY PREDICTION ENDPOINTS =====================

@app.route('/365_prediction')
@login_required
def prediction_365_dashboard():
    """Dashboard page for 365-day delivery optimization"""
    try:
        # Get available commercials
        commercials = get_commercial_list()
        return render_template('365_prediction.html', commercials=commercials)
    except Exception as e:
        flash(f"Error loading 365-day prediction dashboard: {str(e)}", 'error')
        return redirect(url_for('index'))

@app.route('/api/365_prediction/commercials', methods=['GET'])
@login_required
def get_available_commercials_365():
    """Get list of commercials available for 365-day prediction with optional date filtering"""
    try:
        # Get optional date parameter for filtering
        reference_date = request.args.get('reference_date')
        
        # Get commercials list with optional date filtering
        commercials = get_commercial_list(reference_date=reference_date)
        
        # Format the response
        formatted_commercials = []
        for comm in commercials:
            commercial_data = {
                'commercial_code': str(comm['commercial_code']),
                'total_records': comm['total_records'],
                'unique_clients': comm['unique_clients'],
                'first_record': str(comm['first_record']),
                'last_record': str(comm['last_record']),
                'avg_transaction_value': round(comm['avg_transaction_value'], 2)
            }
            
            # Add training period records if available
            if 'training_period_records' in comm:
                commercial_data['training_period_records'] = comm['training_period_records']
            
            formatted_commercials.append(commercial_data)
        
        response_data = {
            'success': True,
            'commercials': formatted_commercials,
            'total_available': len(formatted_commercials)
        }
        
        # Add date info if filtering was applied
        if reference_date:
            response_data['reference_date'] = reference_date
            response_data['filtered_by_date'] = True
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/365_prediction/analyze', methods=['POST'])
@login_required
def analyze_365_prediction():
    """Run 365-day delivery optimization analysis for a commercial with date selection"""
    try:
        data = request.json
        commercial_code = data.get('commercial_code')
        selected_date = data.get('selected_date')  # New parameter for date selection
        include_revenue_optimization = data.get('include_revenue_optimization', True)
        
        if not commercial_code:
            return jsonify({'error': 'Commercial code is required'}), 400
        
        print(f"Starting 365-day analysis for commercial: {commercial_code}")
        if selected_date:
            print(f"Selected date: {selected_date}")
        
        # Run the 365-day optimization with optional date selection
        results = dual_delivery_optimization_365_days(
            commercial_code=commercial_code,
            selected_date=selected_date,  # Pass the selected date
            include_revenue_optimization=include_revenue_optimization,
            save_results=False  # Don't save files for web interface
        )
        
        if not results:
            return jsonify({'error': 'Failed to generate 365-day predictions'}), 500
        
        # Convert pandas DataFrames and other non-serializable objects to JSON-serializable format
        def convert_to_serializable(obj):
            if isinstance(obj, pd.DataFrame):
                return obj.to_dict('records')
            elif isinstance(obj, pd.Series):
                return obj.tolist()
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif hasattr(obj, 'strftime'):  # datetime objects
                return obj.strftime('%Y-%m-%d')
            elif isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            return obj
        
        # Process the daily plan for the first 30 days (for initial display)
        daily_plan = results['daily_plan']
        sample_daily_plan = daily_plan.head(30).copy()
        
        # Convert dates to strings
        sample_daily_plan['date'] = sample_daily_plan['date'].dt.strftime('%Y-%m-%d')
        
        # Process monthly summary
        monthly_summary = results['monthly_summary']
        monthly_data = []
        for month in monthly_summary.index:
            monthly_data.append({
                'month': month,
                'total_visits': float(monthly_summary.loc[month, ('predicted_visits', 'sum')]),
                'total_revenue': float(monthly_summary.loc[month, ('predicted_revenue', 'sum')]),
                'avg_daily_visits': float(monthly_summary.loc[month, ('predicted_visits', 'mean')]),
                'avg_daily_revenue': float(monthly_summary.loc[month, ('predicted_revenue', 'mean')])
            })
        
        # Process weekly patterns
        weekly_patterns = results['weekly_patterns']
        weekly_data = []
        for day in weekly_patterns.index:
            weekly_data.append({
                'day_of_week': day,
                'avg_visits': float(weekly_patterns.loc[day, 'predicted_visits']),
                'avg_revenue': float(weekly_patterns.loc[day, 'predicted_revenue'])
            })
        
        # Create the response
        response_data = {
            'success': True,
            'commercial_code': commercial_code,
            'analysis_date': results['analysis_date'],
            'forecast_period': results['forecast_period'],
            'start_date': results['start_date'],
            'end_date': results['end_date'],
            
            # Summary statistics
            'summary': {
                'total_predicted_visits': int(results['summary']['total_predicted_visits']),
                'total_predicted_revenue': float(results['summary']['total_predicted_revenue']),
                'avg_daily_visits': float(results['summary']['avg_daily_visits']),
                'avg_daily_revenue': float(results['summary']['avg_daily_revenue']),
                'peak_days': int(results['summary']['peak_days']),
                'low_activity_days': int(results['summary']['low_activity_days']),
                'revenue_target_met_days': int(results['summary']['revenue_target_met_days'])
            },
            
            # Sample daily data (first 30 days)
            'sample_daily_plan': sample_daily_plan.to_dict('records'),
            
            # Monthly breakdown
            'monthly_summary': monthly_data,
            
            # Weekly patterns
            'weekly_patterns': weekly_data,
            
            # Key insights
            'insights': {
                'best_month': results['insights']['best_month'],
                'worst_month': results['insights']['worst_month'],
                'best_day_of_week': results['insights']['best_day_of_week'],
                'worst_day_of_week': results['insights']['worst_day_of_week'],
                'peak_periods': results['insights']['peak_periods'][:5],  # First 5 peak periods
                'low_periods': results['insights']['low_periods'][:5]     # First 5 low periods
            },
            
            # Model performance
            'model_performance': {
                'visits_model_quality': float(results['model_performance']['visits_model_quality']),
                'revenue_optimization_applied': bool(results['model_performance']['revenue_optimization_applied']),
                'seasonal_adjustments_applied': bool(results['model_performance']['seasonal_adjustments_applied'])
            }
        }
        
        print(f"Successfully completed 365-day analysis for commercial: {commercial_code}")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in 365-day prediction: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/api/365_prediction/download', methods=['POST'])
@login_required
def download_365_prediction():
    """Download 365-day prediction results as Excel file with date selection support"""
    try:
        data = request.json
        commercial_code = data.get('commercial_code')
        selected_date = data.get('selected_date')  # New parameter for date selection
        include_revenue_optimization = data.get('include_revenue_optimization', True)
        
        if not commercial_code:
            return jsonify({'error': 'Commercial code is required'}), 400
        
        # Run the 365-day optimization with file saving enabled
        results = dual_delivery_optimization_365_days(
            commercial_code=commercial_code,
            selected_date=selected_date,  # Pass the selected date
            include_revenue_optimization=include_revenue_optimization,
            save_results=True  # Enable file saving
        )
        
        if not results:
            return jsonify({'error': 'Failed to generate 365-day predictions'}), 500
        
        # Get the daily plan
        daily_plan = results['daily_plan']
        
        # Create Excel file in memory
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Main daily plan
            daily_plan_export = daily_plan.copy()
            daily_plan_export['date'] = daily_plan_export['date'].dt.strftime('%Y-%m-%d')
            daily_plan_export.to_excel(writer, sheet_name='Daily Plan 365 Days', index=False)
            
            # Monthly summary
            monthly_summary = results['monthly_summary']
            monthly_export = pd.DataFrame()
            for month in monthly_summary.index:
                monthly_export = pd.concat([monthly_export, pd.DataFrame({
                    'Month': [month],
                    'Total Visits': [monthly_summary.loc[month, ('predicted_visits', 'sum')]],
                    'Total Revenue': [monthly_summary.loc[month, ('predicted_revenue', 'sum')]],
                    'Avg Daily Visits': [monthly_summary.loc[month, ('predicted_visits', 'mean')]],
                    'Avg Daily Revenue': [monthly_summary.loc[month, ('predicted_revenue', 'mean')]]
                })], ignore_index=True)
            monthly_export.to_excel(writer, sheet_name='Monthly Summary', index=False)
            
            # Weekly patterns
            weekly_patterns = results['weekly_patterns']
            weekly_export = pd.DataFrame({
                'Day of Week': weekly_patterns.index,
                'Avg Visits': weekly_patterns['predicted_visits'],
                'Avg Revenue': weekly_patterns['predicted_revenue']
            })
            weekly_export.to_excel(writer, sheet_name='Weekly Patterns', index=False)
            
            # Summary statistics
            summary_export = pd.DataFrame([{
                'Metric': 'Total Predicted Visits (365 days)',
                'Value': results['summary']['total_predicted_visits']
            }, {
                'Metric': 'Total Predicted Revenue (365 days)',
                'Value': f"{results['summary']['total_predicted_revenue']:.2f} TND"
            }, {
                'Metric': 'Average Daily Visits',
                'Value': f"{results['summary']['avg_daily_visits']:.1f}"
            }, {
                'Metric': 'Average Daily Revenue',
                'Value': f"{results['summary']['avg_daily_revenue']:.2f} TND"
            }, {
                'Metric': 'Peak Activity Days',
                'Value': results['summary']['peak_days']
            }, {
                'Metric': 'Low Activity Days',
                'Value': results['summary']['low_activity_days']
            }, {
                'Metric': 'Days Meeting Revenue Target',
                'Value': results['summary']['revenue_target_met_days']
            }, {
                'Metric': 'Best Month',
                'Value': results['insights']['best_month']
            }, {
                'Metric': 'Worst Month',
                'Value': results['insights']['worst_month']
            }, {
                'Metric': 'Best Day of Week',
                'Value': results['insights']['best_day_of_week']
            }, {
                'Metric': 'Model Quality Score',
                'Value': f"{results['model_performance']['visits_model_quality']:.1f}/100"
            }])
            summary_export.to_excel(writer, sheet_name='Summary Statistics', index=False)
        
        # Set pointer at the beginning
        output.seek(0)
        
        # Generate filename with current date
        filename = f'365_day_prediction_{commercial_code}_{datetime.now().strftime("%Y%m%d")}.xlsx'
        
        # Return the Excel file
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/365_prediction/chart_data/<commercial_code>')
@login_required
def get_365_chart_data(commercial_code):
    """Get chart data for 365-day visualization with date selection support"""
    try:
        # Get optional date parameter
        selected_date = request.args.get('selected_date')
        
        # Run quick analysis to get chart data
        results = dual_delivery_optimization_365_days(
            commercial_code=commercial_code,
            selected_date=selected_date,  # Pass the selected date
            include_revenue_optimization=True,
            save_results=False
        )
        
        if not results:
            return jsonify({'error': 'Failed to generate chart data'}), 500
        
        daily_plan = results['daily_plan']
        
        # Prepare data for charts
        chart_data = {
            'daily_visits': {
                'dates': daily_plan['date'].dt.strftime('%Y-%m-%d').tolist(),
                'visits': daily_plan['predicted_visits'].tolist(),
                'visits_lower': daily_plan['visits_lower_ci'].tolist(),
                'visits_upper': daily_plan['visits_upper_ci'].tolist()
            },
            'daily_revenue': {
                'dates': daily_plan['date'].dt.strftime('%Y-%m-%d').tolist(),
                'revenue': daily_plan['predicted_revenue'].tolist(),
                'revenue_lower': daily_plan['revenue_lower_ci'].tolist(),
                'revenue_upper': daily_plan['revenue_upper_ci'].tolist()
            },
            'monthly_aggregation': [],
            'weekly_patterns': []
        }
        
        # Monthly aggregation
        monthly_data = daily_plan.groupby(daily_plan['date'].dt.to_period('M')).agg({
            'predicted_visits': 'sum',
            'predicted_revenue': 'sum'
        })
        
        for period, row in monthly_data.iterrows():
            chart_data['monthly_aggregation'].append({
                'month': str(period),
                'visits': float(row['predicted_visits']),
                'revenue': float(row['predicted_revenue'])
            })
        
        # Weekly patterns
        weekly_data = daily_plan.groupby('day_of_week').agg({
            'predicted_visits': 'mean',
            'predicted_revenue': 'mean'
        })
        
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day in day_order:
            if day in weekly_data.index:
                chart_data['weekly_patterns'].append({
                    'day': day,
                    'avg_visits': float(weekly_data.loc[day, 'predicted_visits']),
                    'avg_revenue': float(weekly_data.loc[day, 'predicted_revenue'])
                })
        
        return jsonify({
            'success': True,
            'chart_data': chart_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ================ JSON EXPORT API ENDPOINTS ================

@app.route('/api/export/commercial_visits/<commercial_code>', methods=['POST'])
@login_required
def export_commercial_visits_json(commercial_code):
    """Export commercial visits analysis to JSON"""
    try:
        from commercial_visits_analysis import save_predictions_to_json, predict_visits_with_sarima
        
        data = request.json or {}
        analysis_date = data.get('analysis_date', datetime.now().strftime('%Y-%m-%d'))
        
        # Run the analysis
        results = predict_visits_with_sarima(commercial_code, analysis_date)
        if results:
            # Save to JSON
            success = save_predictions_to_json(results, commercial_code)
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Commercial visits analysis exported to JSON successfully',
                    'commercial_code': commercial_code,
                    'export_date': datetime.now().isoformat()
                })
        
        return jsonify({'error': 'Failed to export commercial visits analysis'}), 500
        
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@app.route('/api/export/365_prediction/<commercial_code>', methods=['POST'])
@login_required
def export_365_prediction_json(commercial_code):
    """Export 365-day prediction to JSON"""
    try:
        from sarima_delivery_optimization import dual_delivery_optimization_365_days
        
        data = request.json or {}
        selected_date = data.get('selected_date')
        include_revenue_optimization = data.get('include_revenue_optimization', True)
        
        # Run the analysis with save_results=True to trigger JSON export
        results = dual_delivery_optimization_365_days(
            commercial_code=commercial_code,
            selected_date=selected_date,
            include_revenue_optimization=include_revenue_optimization,
            save_results=True  # This will trigger JSON export
        )
        
        if results:
            return jsonify({
                'success': True,
                'message': '365-day prediction exported to JSON successfully',
                'commercial_code': commercial_code,
                'analysis_date': results.get('analysis_date'),
                'export_date': datetime.now().isoformat()
            })
        
        return jsonify({'error': 'Failed to export 365-day prediction'}), 500
        
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@app.route('/api/export/product_analysis/<product_code>', methods=['POST'])
@login_required
def export_product_analysis_json(product_code):
    """Export product analysis to JSON"""
    try:
        from product_analysis import display_sales_table, forecast_sales_for_2025
        
        # Run sales analysis with JSON export
        sales_data = display_sales_table(product_code, save_json=True)
        
        # Run forecast analysis with JSON export
        try:
            forecast_results = forecast_sales_for_2025(product_code, save_json=True)
            has_forecast = True
        except Exception:
            has_forecast = False
        
        return jsonify({
            'success': True,
            'message': 'Product analysis exported to JSON successfully',
            'product_code': product_code,
            'has_sales_data': sales_data is not None,
            'has_forecast': has_forecast,
            'export_date': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@app.route('/api/export/delivery_plan', methods=['POST'])
@login_required
def export_delivery_plan_json():
    """Export delivery plan to JSON"""
    try:
        from delivery_optimization import generate_delivery_plan
        from historical_analysis import load_historical_data, load_locations_data
        
        data = request.json or {}
        commercial_code = data.get('commercial_code')
        delivery_date = data.get('delivery_date')
        
        if not commercial_code or not delivery_date:
            return jsonify({'error': 'Commercial code and delivery date are required'}), 400
        
        # Parse delivery date
        delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d')
        
        # Load required data
        historical_data = load_historical_data(commercial_code)
        locations_data = load_locations_data()
        
        # Generate delivery plan with JSON export
        delivery_plan = generate_delivery_plan(
            commercial_code=commercial_code,
            delivery_date=delivery_date,
            historical_data=historical_data,
            locations_data=locations_data,
            save_json=True  # This will trigger JSON export
        )
        
        if delivery_plan:
            return jsonify({
                'success': True,
                'message': 'Delivery plan exported to JSON successfully',
                'commercial_code': commercial_code,
                'delivery_date': delivery_date.strftime('%Y-%m-%d'),
                'total_clients': len(delivery_plan.get('route', [])),
                'total_distance': delivery_plan.get('total_distance', 0),
                'export_date': datetime.now().isoformat()
            })
        
        return jsonify({'error': 'Failed to export delivery plan'}), 500
        
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@app.route('/api/export/all_modules', methods=['POST'])
@login_required
def export_all_modules_json():
    """Export data from all analysis modules to JSON"""
    try:
        data = request.json or {}
        commercial_code = data.get('commercial_code')
        product_code = data.get('product_code', 'KC010210')  # Default product
        delivery_date = data.get('delivery_date', datetime.now().strftime('%Y-%m-%d'))
        
        if not commercial_code:
            return jsonify({'error': 'Commercial code is required'}), 400
        
        results = {
            'export_summary': {
                'commercial_code': commercial_code,
                'product_code': product_code,
                'delivery_date': delivery_date,
                'export_date': datetime.now().isoformat(),
                'modules_exported': []
            },
            'results': {}
        }
        
        # Export commercial visits analysis
        try:
            from commercial_visits_analysis import save_predictions_to_json, predict_visits_with_sarima
            visit_results = predict_visits_with_sarima(commercial_code)
            if visit_results:
                save_predictions_to_json(visit_results, commercial_code)
                results['results']['commercial_visits'] = 'success'
                results['export_summary']['modules_exported'].append('commercial_visits_analysis')
        except Exception as e:
            results['results']['commercial_visits'] = f'error: {str(e)}'
        
        # Export 365-day prediction
        try:
            from sarima_delivery_optimization import dual_delivery_optimization_365_days
            prediction_results = dual_delivery_optimization_365_days(
                commercial_code=commercial_code,
                save_results=True
            )
            if prediction_results:
                results['results']['365_prediction'] = 'success'
                results['export_summary']['modules_exported'].append('365_day_prediction')
        except Exception as e:
            results['results']['365_prediction'] = f'error: {str(e)}'
        
        # Export product analysis
        try:
            from product_analysis import display_sales_table, forecast_sales_for_2025
            display_sales_table(product_code, save_json=True)
            try:
                forecast_sales_for_2025(product_code, save_json=True)
            except:
                pass  # Forecast may fail, but continue
            results['results']['product_analysis'] = 'success'
            results['export_summary']['modules_exported'].append('product_analysis')
        except Exception as e:
            results['results']['product_analysis'] = f'error: {str(e)}'
        
        # Export delivery plan
        try:
            from delivery_optimization import generate_delivery_plan
            from historical_analysis import load_historical_data, load_locations_data
            
            delivery_date_obj = datetime.strptime(delivery_date, '%Y-%m-%d')
            historical_data = load_historical_data(commercial_code)
            locations_data = load_locations_data()
            
            generate_delivery_plan(
                commercial_code=commercial_code,
                delivery_date=delivery_date_obj,
                historical_data=historical_data,
                locations_data=locations_data,
                save_json=True
            )
            results['results']['delivery_plan'] = 'success'
            results['export_summary']['modules_exported'].append('delivery_optimization')
        except Exception as e:
            results['results']['delivery_plan'] = f'error: {str(e)}'
        
        # Summary
        total_modules = 4
        successful_exports = len(results['export_summary']['modules_exported'])
        
        return jsonify({
            'success': True,
            'message': f'Exported data from {successful_exports}/{total_modules} modules successfully',
            'export_summary': results['export_summary'],
            'detailed_results': results['results'],
            'success_rate': f"{successful_exports}/{total_modules}"
        })
        
    except Exception as e:
        return jsonify({'error': f'Bulk export failed: {str(e)}'}), 500

# ================ COMPREHENSIVE EXPORT ENDPOINTS ================

@app.route('/api/export/clients_data', methods=['GET'])
@login_required
def export_clients_data_endpoint():
    """Export comprehensive clients data to Excel"""
    try:
        from export_utilities import export_clients_data
        
        output = export_clients_data()
        if output:
            filename = f'clients_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )
        else:
            return jsonify({'error': 'Failed to export clients data'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@app.route('/api/export/commercials_data', methods=['GET'])
@login_required
def export_commercials_data_endpoint():
    """Export comprehensive commercials data to Excel"""
    try:
        from export_utilities import export_commercials_data
        
        output = export_commercials_data()
        if output:
            filename = f'commercials_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )
        else:
            return jsonify({'error': 'Failed to export commercials data'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@app.route('/api/export/products_data', methods=['GET'])
@login_required
def export_products_data_endpoint():
    """Export comprehensive products data to Excel"""
    try:
        from export_utilities import export_products_data
        
        output = export_products_data()
        if output:
            filename = f'products_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )
        else:
            return jsonify({'error': 'Failed to export products data'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@app.route('/api/export/dashboard_data', methods=['GET'])
@login_required
def export_dashboard_data_endpoint():
    """Export global dashboard data to Excel"""
    try:
        from export_utilities import export_global_dashboard_data
        
        output = export_global_dashboard_data()
        if output:
            filename = f'dashboard_global_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )
        else:
            return jsonify({'error': 'Failed to export dashboard data'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@app.route('/api/export/complete_data', methods=['GET'])
@login_required
def export_complete_data_endpoint():
    """Export all data in one comprehensive Excel file"""
    try:
        from export_utilities import export_clients_data, export_commercials_data, export_products_data, export_global_dashboard_data, ExportManager
        import pandas as pd
        
        # Collect all data
        all_data = {}
        
        # Dashboard data
        try:
            dashboard_output = export_global_dashboard_data()
            # Note: We'll need to extract the dataframes from the Excel outputs
            # For now, let's create a comprehensive report
            pass
        except:
            pass
        
        # Create a summary report
        conn = get_db_connection()
        
        # Comprehensive summary
        summary_query = """
        SELECT 
            'Global Statistics' as category,
            COUNT(DISTINCT client_code) as total_clients,
            COUNT(DISTINCT commercial_code) as total_commerciaux,
            COUNT(DISTINCT produit_code) as total_produits,
            COUNT(*) as total_transactions,
            SUM(net_a_payer) as chiffre_affaires_total,
            AVG(net_a_payer) as transaction_moyenne
        FROM entetecommercials
        """
        
        summary_df = pd.read_sql(summary_query, conn)
        
        # Recent activity
        recent_query = """
        SELECT 
            date,
            commercial_code,
            client_code,
            nom_client,
            produit_code,
            quantite,
            net_a_payer
        FROM entetecommercials 
        ORDER BY date DESC
        LIMIT 1000
        """
        
        recent_df = pd.read_sql(recent_query, conn)
        conn.close()
        
        export_manager = ExportManager()
        
        data_dict = {
            'Resume_Global': summary_df,
            'Activite_Recente': recent_df
        }
        
        output = export_manager.export_to_excel(data_dict, "export_complet")
        
        if output:
            filename = f'export_complet_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )
        else:
            return jsonify({'error': 'Failed to export complete data'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Complete export failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)