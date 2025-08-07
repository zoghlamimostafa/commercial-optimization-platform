def get_realistic_clients_for_date(commercial_code, target_date, max_clients=20):
    """
    Pour une date future, retourne la liste des clients visités par le commercial
    lors des mêmes jour/mois dans les années précédentes, triés par fréquence (max 20).
    """
    import logging
    logger = logging.getLogger('realistic_clients')
    conn = get_db_connection()
    try:
        # Extraire jour et mois de la date cible
        date_obj = pd.to_datetime(target_date)
        day = date_obj.day
        month = date_obj.month
        # Requête pour trouver les clients visités le même jour/mois les années précédentes
        query = '''
            SELECT ec.client_code, COUNT(*) as freq
            FROM entetecommercials ec
            WHERE ec.commercial_code = %s
              AND DAY(ec.date) = %s
              AND MONTH(ec.date) = %s
              AND YEAR(ec.date) < %s
            GROUP BY ec.client_code
            ORDER BY freq DESC
        '''
        params = [commercial_code, day, month, date_obj.year]
        df = pd.read_sql(query, conn, params=params)
        if df.empty:
            logger.info(f"Aucun client trouvé pour le {day}/{month} sur les années précédentes pour commercial {commercial_code}")
            return []
        # Trier par fréquence et limiter à max_clients
        filtered_clients = df.sort_values('freq', ascending=False).head(max_clients)['client_code'].tolist()
        logger.info(f"{len(filtered_clients)} clients filtrés pour le {day}/{month} (max {max_clients})")
        return filtered_clients
    except Exception as e:
        logger.error(f"Erreur dans get_realistic_clients_for_date: {str(e)}")
        return []
    finally:
        if conn:
            conn.dispose()
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import mysql.connector
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from datetime import datetime, timedelta

# Connexion à la base de données
def get_db_connection():
    """
    Établit une connexion à la base de données MySQL
    Returns:
        engine: SQLAlchemy engine pour la connexion à la base de données
    """
    import logging
    logger = logging.getLogger('database')
    
    db_config = {
        'host': '127.0.0.1',
        'database': 'pfe1',
        'user': 'root',
        'password': ''
    }
    
    try:
        # Configuration de la connexion à la base de données
        logger.info(f"Connexion à la base de données MySQL ({db_config['host']}/{db_config['database']})")
        
        # Créer une URL de connexion sécurisée
        connection_url = f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"
        engine = create_engine(connection_url, pool_recycle=3600, pool_pre_ping=True)
        
        # Vérifier la connexion avec une requête simple
        with engine.connect() as conn:
            # Tester avec une requête simple
            result = conn.execute(text("SELECT COUNT(*) FROM entetecommercials"))
            row = result.fetchone()
            count = row[0] if row else 0
            
            logger.info(f"Connexion à la base de données réussie. {count} enregistrements dans entetecommercials.")
            print(f"Connexion à la base de données MySQL réussie. {count} enregistrements dans entetecommercials.")
        
        return engine
    except Exception as e:
        logger.error(f"Erreur de connexion à la base de données MySQL: {str(e)}")
        print(f"ERREUR: Impossible de se connecter à la base de données MySQL: {str(e)}")
        print("Vérifiez que MySQL est démarré et que la base de données 'pfe1' existe.")
        raise e

# Récupérer les données historiques des livraisons par commercial
def get_historical_deliveries(date_debut='2023-01-01', date_fin='2024-12-31'):
    """
    Récupère les données historiques des livraisons avec gestion des erreurs avancée
    
    Args:
        date_debut: Date de début pour la récupération des données (format YYYY-MM-DD)
        date_fin: Date de fin pour la récupération des données (format YYYY-MM-DD)
    
    Returns:
    df: DataFrame avec les données historiques
    """
    import logging
    logger = logging.getLogger('historical_data')
    logger.info(f"Récupération des données historiques du {date_debut} au {date_fin}")
    
    try:
        # Optimiser la requête en utilisant des paramètres préparés pour éviter les injections SQL
        query = """
        SELECT 
            ec.date,
            ec.commercial_code,
            COUNT(ec.code) AS nombre_livraisons,
            COUNT(DISTINCT ec.client_code) AS nb_clients_visites,
            SUM(ec.net_a_payer) AS valeur_totale
        FROM entetecommercials ec
        WHERE ec.date BETWEEN %s AND %s
        GROUP BY ec.date, ec.commercial_code
        ORDER BY ec.date, ec.commercial_code
        """
        
        conn = get_db_connection()
        
        # Exécuter la requête avec des paramètres pour éviter les injections SQL
        df = pd.read_sql(query, conn, params=(date_debut, date_fin))
        conn.dispose()
        
        # Convertir la date en format datetime
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # Supprimer les lignes avec des dates invalides
        invalid_dates = df['date'].isna().sum()
        if invalid_dates > 0:
            logger.warning(f"Suppression de {invalid_dates} lignes avec des dates invalides")
            df = df.dropna(subset=['date'])
        
        # Vérifier et signaler la qualité des données
        logger.info(f"Données récupérées: {len(df)} enregistrements pour {df['commercial_code'].nunique()} commerciaux")
        
        if df.empty:
            logger.warning("Aucune donnée trouvée, vérifiez les dates ou la connexion à la base de données")
            print("ATTENTION: Aucune donnée trouvée, vérifiez les dates ou la connexion à la base de données.")
        else:
            date_range = df['date'].max() - df['date'].min()
            logger.info(f"Plage de dates: {df['date'].min()} à {df['date'].max()} ({date_range.days} jours)")
            
            # Vérifier la complétude des données (combien de jours ont des données)
            dates_uniques = df['date'].dt.date.nunique()
            days_in_range = (pd.to_datetime(date_fin) - pd.to_datetime(date_debut)).days + 1
            coverage = dates_uniques / days_in_range * 100
            logger.info(f"Couverture temporelle: {dates_uniques}/{days_in_range} jours ({coverage:.2f}%)")
            
            # Statistiques sur les livraisons
            logger.info(f"Statistiques des livraisons: min={df['nombre_livraisons'].min()}, "
                  f"max={df['nombre_livraisons'].max()}, moyenne={df['nombre_livraisons'].mean():.2f}")
            
            # Afficher des statistiques pour l'utilisateur
            print(f"Données récupérées: {len(df)} enregistrements pour {df['commercial_code'].nunique()} commerciaux")
            print(f"Plage de dates: {df['date'].min().date()} à {df['date'].max().date()}")
            print(f"Couverture temporelle: {dates_uniques}/{days_in_range} jours ({coverage:.2f}%)")
            print(f"Statistiques des livraisons: min={df['nombre_livraisons'].min()}, "                f"max={df['nombre_livraisons'].max()}, moyenne={df['nombre_livraisons'].mean():.2f}")
            
        return df
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données: {str(e)}")
        print(f"Erreur lors de la récupération des données historiques: {str(e)}")
        
        # Créer un DataFrame vide avec les bonnes colonnes en cas d'échec
        empty_df = pd.DataFrame(columns=[
            'date', 'commercial_code', 'nombre_livraisons', 
            'nb_clients_visites', 'valeur_totale'
        ])
        return empty_df

# Préparer les données pour le modèle SARIMA
def prepare_data_for_sarima(df, commercial_code, metric='nombre_livraisons', freq='W'):
    """
    Prépare les données pour le modèle SARIMA avec validation et nettoyage avancés
    
    Args:
        df: DataFrame avec les données historiques
        commercial_code: Code du commercial à analyser
        metric: Métrique à analyser ('nombre_livraisons', 'nb_clients_visites', 'valeur_totale')
        freq: Fréquence de regroupement ('D'=jour, 'W'=semaine, 'M'=mois)
    
    Returns:
        time_series: Série temporelle prête pour le modèle SARIMA
    """
    import logging
    logger = logging.getLogger('data_preparation')
    
    # Vérifier la présence du commercial dans les données
    commercial_df = df[df['commercial_code'] == commercial_code].copy()
    if commercial_df.empty:
        logger.error(f"Aucune donnée pour le commercial {commercial_code}")
        print(f"ATTENTION: Aucune donnée pour le commercial {commercial_code}")
        return pd.Series()
    
    # Validation des données
    logger.info(f"Préparation des données pour le commercial {commercial_code} avec fréquence {freq}")
    logger.info(f"Données disponibles: {len(commercial_df)} enregistrements du {commercial_df['date'].min()} au {commercial_df['date'].max()}")
    print(f"Préparation des données pour le commercial {commercial_code} avec fréquence {freq}")
    print(f"Données disponibles: {len(commercial_df)} enregistrements du {commercial_df['date'].min()} au {commercial_df['date'].max()}")
    
    # Vérifier l'intégrité des données
    if commercial_df[metric].isna().any():
        n_missing = commercial_df[metric].isna().sum()
        logger.warning(f"{n_missing} valeurs manquantes détectées pour la métrique '{metric}'")
        print(f"ATTENTION: {n_missing} valeurs manquantes détectées pour la métrique '{metric}'")
        
    # Détecter les valeurs négatives (qui pourraient être des erreurs)
    if (commercial_df[metric] < 0).any():
        n_negative = (commercial_df[metric] < 0).sum()
        logger.warning(f"{n_negative} valeurs négatives détectées pour la métrique '{metric}'")
        print(f"ATTENTION: {n_negative} valeurs négatives détectées pour la métrique '{metric}'")
        # Remplacer les valeurs négatives par 0
        commercial_df.loc[commercial_df[metric] < 0, metric] = 0
    
    # Regrouper par la fréquence temporelle spécifiée
    commercial_df.set_index('date', inplace=True)
    time_series = commercial_df[metric].resample(freq).sum()
    
    # Vérifier la fréquence des données
    date_counts = commercial_df.groupby(pd.Grouper(freq=freq)).size()
    coverage = (date_counts > 0).mean() * 100
    logger.info(f"Couverture temporelle: {coverage:.2f}% des périodes ont des données")
    
    # Remplir les valeurs manquantes avec différentes stratégies selon le contexte
    if coverage < 50:
        logger.warning(f"Couverture temporelle faible ({coverage:.2f}%). Utilisation d'une stratégie d'interpolation.")
        # Pour une faible couverture, utiliser une interpolation avancée
        time_series = time_series.interpolate(method='time').fillna(method='bfill').fillna(0)
    else:
        # Pour une bonne couverture, remplir simplement les trous avec 0 ou la moyenne
        if metric == 'valeur_totale':
            # Pour les valeurs monétaires, utiliser la moyenne des périodes adjacentes
            time_series = time_series.fillna(time_series.rolling(window=3, min_periods=1, center=True).mean())
        time_series = time_series.fillna(0)
    
    # Détecter et traiter les valeurs aberrantes (outliers)
    if len(time_series) >= 10:  # Seulement si nous avons assez de données
        # Calculer les limites pour les outliers basées sur IQR
        Q1 = time_series.quantile(0.25)
        Q3 = time_series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Identifier les outliers
        outliers = time_series[(time_series < lower_bound) | (time_series > upper_bound)]
        if len(outliers) > 0:
            logger.info(f"Détection de {len(outliers)} valeurs aberrantes")
            print(f"Détection de {len(outliers)} valeurs aberrantes")
            
            # Pour les séries longues, on peut remplacer par la médiane mobile
            if len(time_series) >= 30:
                for idx in outliers.index:
                    # Utiliser une fenêtre locale pour calculer la médiane autour de chaque outlier
                    window_start = max(0, time_series.index.get_loc(idx) - 2)
                    window_end = min(len(time_series), time_series.index.get_loc(idx) + 3)
                    window_indices = time_series.index[window_start:window_end]
                    local_values = time_series.loc[window_indices].copy()
                    # Exclure l'outlier lui-même de la médiane
                    local_values = local_values.drop(idx)
                    if local_values.empty:
                        time_series.at[idx] = time_series.median()
                    else:
                        time_series.at[idx] = local_values.median()
            else:
                # Pour les séries courtes, simplement limiter aux bornes
                time_series = time_series.clip(lower=lower_bound, upper=upper_bound)
    
    # Vérifier la qualité des données après préparation
    non_zero_count = (time_series > 0).sum()
    logger.info(f"Série temporelle créée: {len(time_series)} points, dont {non_zero_count} non nuls")
    logger.info(f"Statistiques: min={time_series.min()}, max={time_series.max()}, moyenne={time_series.mean():.2f}, médiane={time_series.median():.2f}")
    
    print(f"Série temporelle créée: {len(time_series)} points, dont {non_zero_count} non nuls")
    print(f"Statistiques: min={time_series.min()}, max={time_series.max()}, moyenne={time_series.mean():.2f}, médiane={time_series.median():.2f}")
    
    # Si la série est très éparse (beaucoup de zéros), avertir
    if non_zero_count / len(time_series) < 0.3:
        logger.warning(f"Série temporelle très éparse: seulement {non_zero_count}/{len(time_series)} points non nuls ({non_zero_count/len(time_series)*100:.1f}%)")
        print(f"ATTENTION: Série temporelle très éparse, la qualité des prévisions peut être affectée.")
    
    return time_series

# Analyser spécifiquement les visites clients
def analyze_client_visits(commercial_code, date_specific=None):
    """
    Analyse les visites clients pour un commercial à une date spécifique ou sur une période
    
    Args:
        commercial_code: Code du commercial à analyser
        date_specific: Date spécifique à analyser (format YYYY-MM-DD)
        
    Returns:
        client_visits_df: DataFrame avec les statistiques de visites clients
    """
    import logging
    logger = logging.getLogger('client_visits')
    
    conn = None
    try:
        # Paramètres pour requête préparée
        params = []
        
        if date_specific:
            try:
                # Convertir en datetime et valider la date
                date_obj = pd.to_datetime(date_specific)
                date_debut = date_obj.strftime('%Y-%m-%d 00:00:00')
                date_fin = (date_obj + pd.Timedelta(days=1)).strftime('%Y-%m-%d 00:00:00')
                
                # Requête pour une date spécifique avec des paramètres préparés
                query = """
                SELECT 
                    ec.date,
                    ec.commercial_code,
                    COUNT(DISTINCT ec.client_code) AS nb_clients_visites
                FROM entetecommercials ec
                WHERE ec.commercial_code = %s
                AND ec.date >= %s
                AND ec.date < %s
                GROUP BY ec.date, ec.commercial_code
                """
                params = [commercial_code, date_debut, date_fin]
                logger.info(f"Analyse des visites pour le commercial {commercial_code} à la date {date_specific}")
            except ValueError:
                logger.error(f"Format de date invalide: {date_specific}")
                print(f"ERREUR: Format de date invalide: {date_specific}")
                return pd.DataFrame()
        else:
            # Requête pour analyser sur toute la période avec des paramètres préparés
            query = """
            SELECT 
                DATE(ec.date) AS jour,
                ec.commercial_code,
                COUNT(DISTINCT ec.client_code) AS nb_clients_visites
            FROM entetecommercials ec
            WHERE ec.commercial_code = %s
            GROUP BY jour, ec.commercial_code
            ORDER BY jour
            """
            params = [commercial_code]
            logger.info(f"Analyse des visites pour le commercial {commercial_code} sur toute la période")
          # Établir la connexion
        conn = get_db_connection()
        
        client_visits_df = pd.read_sql(query, conn, params=params)
        
        # Analyser les résultats
        if date_specific:
            if not client_visits_df.empty:
                visit_count = client_visits_df.iloc[0]['nb_clients_visites']
                logger.info(f"Le commercial {commercial_code} a visité {visit_count} client(s) le {date_specific}")
                print(f"Le commercial {commercial_code} a visité {visit_count} client(s) le {date_specific}")
            else:
                # Pour les dates futures (prévisions), indiquer qu'il s'agit d'une date future
                date_obj = pd.to_datetime(date_specific)
                if date_obj > pd.Timestamp.now():
                    logger.info(f"La date {date_specific} est dans le futur, aucune donnée historique disponible")
                    print(f"La date {date_specific} est dans le futur, aucune donnée historique disponible.")
                    print(f"Une prévision sera générée pour cette date.")
                else:
                    logger.warning(f"Aucune visite client enregistrée pour le commercial {commercial_code} le {date_specific}")
                    print(f"Aucune visite client enregistrée pour le commercial {commercial_code} le {date_specific}")
        else:
            # Statistiques sur l'ensemble de la période
            if not client_visits_df.empty:
                avg_visits = client_visits_df['nb_clients_visites'].mean()
                max_visits = client_visits_df['nb_clients_visites'].max()
                total_days = len(client_visits_df)
                
                logger.info(f"Statistiques pour le commercial {commercial_code}:")
                logger.info(f"Moyenne de {avg_visits:.2f} clients par jour sur {total_days} jours")
                logger.info(f"Maximum de {max_visits} clients en une journée")
                
                print(f"Statistiques pour le commercial {commercial_code}:")
                print(f"Moyenne de {avg_visits:.2f} clients par jour sur {total_days} jours")
                print(f"Maximum de {max_visits} clients en une journée")
                  # Visualiser la distribution des visites clients
                plt.figure(figsize=(10, 6))
                client_visits_df.set_index('jour')['nb_clients_visites'].plot(kind='bar')
                plt.title(f'Visites clients du commercial {commercial_code}')
                plt.xlabel('Date')
                plt.ylabel('Nombre de clients visités')
                plt.tight_layout()
                plt.savefig(f'client_visits_commercial_{commercial_code}.png')
                plt.close()
            else:
                logger.warning(f"Aucune donnée de visite pour le commercial {commercial_code}")
                print(f"Aucune donnée de visite pour le commercial {commercial_code}")
        
        return client_visits_df
    
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse des visites clients: {str(e)}")
        print(f"Erreur lors de l'analyse des visites clients: {str(e)}")
        return pd.DataFrame()
    
    finally:
        # Fermer la connexion dans tous les cas
        if conn:
            conn.dispose()

# Identifier les paramètres optimaux pour SARIMA
def identify_sarima_parameters(time_series, seasonal_period=52, business_constraints=None, revenue_weight=0.3):
    """
    Enhanced SARIMA parameter identification with business logic and multi-metric validation
    
    Args:
        time_series: Série temporelle pour l'analyse
        seasonal_period: Période saisonnière (52 pour hebdomadaire = 1 an)
        business_constraints: Dictionary with business constraints for parameter selection
        revenue_weight: Weight factor for business logic in parameter selection (0-1)
      Returns:
        suggested_parameters: Dictionnaire avec les paramètres suggérés et les métriques
    """
    import logging
    import time
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    import warnings
    warnings.filterwarnings('ignore')
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('enhanced_sarima_optimization')
    
    # Initialize business constraints if not provided
    if business_constraints is None:
        business_constraints = {
            'min_forecast_accuracy': 0.70,
            'max_computation_time': 300,  # seconds
            'prefer_simpler_models': True,
            'seasonal_importance': 0.8
        }
    
    logger.info("🚀 Enhanced SARIMA parameter optimization starting...")
    logger.info(f"📊 Time series length: {len(time_series)}, Seasonal period: {seasonal_period}")
    logger.info(f"💼 Business constraints: {business_constraints}")
    
    # Enhanced diagnostic visualizations
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # Original time series
    ax1.plot(time_series)
    ax1.set_title("Original Time Series")
    ax1.grid(True, alpha=0.3)
    
    # Decomposition for seasonal analysis
    try:
        from statsmodels.tsa.seasonal import seasonal_decompose
        decomposition = seasonal_decompose(time_series, model='additive', period=min(seasonal_period, len(time_series)//2))
        ax2.plot(decomposition.seasonal[:seasonal_period*2])
        ax2.set_title("Seasonal Component")
        ax2.grid(True, alpha=0.3)
    except:
        ax2.plot(time_series.rolling(7).mean())
        ax2.set_title("7-period Moving Average")
        ax2.grid(True, alpha=0.3)
    
    # ACF and PACF for parameter hints
    plot_acf(time_series, ax=ax3, lags=min(40, len(time_series)//4))
    plot_pacf(time_series, ax=ax4, lags=min(40, len(time_series)//4))
    
    plt.tight_layout()
    plt.savefig('enhanced_sarima_diagnostics.png', dpi=300)
    plt.close()
    
    logger.info("📈 Diagnostic plots generated")
    
    # Adaptive k-fold validation based on data size
    if len(time_series) >= 10 * seasonal_period:
        k_fold = 5  # More folds for large datasets
    elif len(time_series) >= 5 * seasonal_period:
        k_fold = 4
    elif len(time_series) >= 3 * seasonal_period:
        k_fold = 3
    else:
        k_fold = 2  # Minimum for small datasets
    
    logger.info(f"🔄 Using {k_fold}-fold cross-validation")
    
    # Enhanced parameter ranges with business logic
    if business_constraints.get('prefer_simpler_models', True):
        p_range = q_range = range(0, 3)  # Simpler models preferred
        d_range = range(0, 2)
        P_range = Q_range = range(0, 2)
        D_range = range(0, 2)
    else:
        p_range = q_range = range(0, 4)  # More complex models allowed
        d_range = range(0, 3)
        P_range = Q_range = range(0, 3)
        D_range = range(0, 2)
    
    s = seasonal_period
    
    # Multi-criteria optimization storage
    evaluation_results = []
    best_composite_score = np.inf
    best_order = None
    best_seasonal_order = None
    
    total_combinations = len(p_range) * len(d_range) * len(q_range) * len(P_range) * len(D_range) * len(Q_range)
    current_combination = 0
    
    logger.info(f"🔍 Evaluating {total_combinations} parameter combinations...")
    
    # Enhanced grid search with multiple metrics
    start_time = time.time()
    
    for param in [(p, d, q) for p in p_range for d in d_range for q in q_range]:
        for seasonal_param in [(P, D, Q, s) for P in P_range for D in D_range for Q in Q_range]:
            current_combination += 1
            
            # Progress tracking
            if current_combination % 20 == 0:
                elapsed_time = time.time() - start_time
                progress = current_combination / total_combinations
                eta = (elapsed_time / progress) * (1 - progress) if progress > 0 else 0
                logger.info(f"⏳ Progress: {current_combination}/{total_combinations} ({progress*100:.1f}%) - ETA: {eta/60:.1f}min")
            
            # Respect computation time constraint
            if time.time() - start_time > business_constraints.get('max_computation_time', 300):
                logger.warning("⏰ Maximum computation time reached, using best model found so far")
                break
            
            try:
                # Fit initial model for basic metrics
                mod = SARIMAX(time_series,
                             order=param,
                             seasonal_order=seasonal_param,
                             enforce_stationarity=False,
                             enforce_invertibility=False)
                results = mod.fit(disp=False, maxiter=200)
                
                # Multiple validation metrics
                metrics = {
                    'aic': results.aic,
                    'bic': results.bic,
                    'rmse_cv': [],
                    'mae_cv': [],
                    'mape_cv': [],
                    'bias_cv': []
                }
                
                # Enhanced cross-validation with multiple metrics
                segment_size = max(1, len(time_series) // k_fold)
                cv_scores = {metric: [] for metric in ['rmse', 'mae', 'mape', 'bias']}
                
                for i in range(k_fold - 1):
                    try:
                        train_end = (i + 1) * segment_size
                        train = time_series[:train_end]
                        test = time_series[train_end:train_end + segment_size]
                        
                        if len(train) < 10 or len(test) < 1:  # Skip if insufficient data
                            continue
                        
                        # Fit on training data
                        cv_mod = SARIMAX(train,
                                       order=param,
                                       seasonal_order=seasonal_param,
                                       enforce_stationarity=False,
                                       enforce_invertibility=False)
                        cv_results = cv_mod.fit(disp=False, maxiter=100)
                        
                        # Predictions on test set
                        pred = cv_results.get_forecast(steps=len(test))
                        pred_mean = pred.predicted_mean
                        
                        # Calculate multiple metrics
                        test_values = test.values
                        pred_values = pred_mean.values
                        
                        # RMSE
                        rmse = np.sqrt(mean_squared_error(test_values, pred_values))
                        cv_scores['rmse'].append(rmse)
                        
                        # MAE
                        mae = mean_absolute_error(test_values, pred_values)
                        cv_scores['mae'].append(mae)
                        
                        # MAPE (avoiding division by zero)
                        mape = np.mean(np.abs((test_values - pred_values) / np.maximum(0.1, np.abs(test_values)))) * 100
                        cv_scores['mape'].append(mape)
                        
                        # Bias (systematic error)
                        bias = np.mean(pred_values - test_values)
                        cv_scores['bias'].append(abs(bias))
                        
                    except Exception as cv_error:
                        # Penalize failed cross-validation
                        cv_scores['rmse'].append(9999)
                        cv_scores['mae'].append(9999)
                        cv_scores['mape'].append(9999)
                        cv_scores['bias'].append(9999)
                
                # Calculate average metrics
                avg_metrics = {}
                for metric, scores in cv_scores.items():
                    if scores:
                        avg_metrics[f'avg_{metric}_cv'] = np.mean(scores)
                        avg_metrics[f'std_{metric}_cv'] = np.std(scores)
                    else:
                        avg_metrics[f'avg_{metric}_cv'] = 9999
                        avg_metrics[f'std_{metric}_cv'] = 9999
                
                # Business logic weighting for composite score
                # Lower is better for all metrics
                composite_score = (
                    (1 - revenue_weight) * (
                        0.3 * avg_metrics['avg_rmse_cv'] +
                        0.3 * avg_metrics['avg_mae_cv'] +
                        0.2 * (avg_metrics['avg_mape_cv'] / 100) +
                        0.1 * avg_metrics['avg_bias_cv'] +
                        0.1 * (results.aic / 1000)  # Normalize AIC
                    ) +
                    revenue_weight * (
                        # Business logic penalty for overly complex models
                        (sum(param) + sum(seasonal_param[:3])) * 0.1 +
                        # Penalty for high variance in predictions
                        avg_metrics['std_rmse_cv'] * 0.2
                    )
                )
                
                # Model complexity penalty
                complexity_penalty = (sum(param) + sum(seasonal_param[:3])) * 0.05
                composite_score += complexity_penalty
                
                # Store evaluation results
                evaluation_results.append({
                    'order': param,
                    'seasonal_order': seasonal_param,
                    'composite_score': composite_score,
                    'aic': results.aic,
                    'bic': results.bic,
                    **avg_metrics
                })
                
                # Update best model
                if composite_score < best_composite_score:
                    best_composite_score = composite_score
                    best_order = param
                    best_seasonal_order = seasonal_param
                    
                    logger.info(f"🎯 New best model found:")
                    logger.info(f"   Order: {param}, Seasonal: {seasonal_param}")
                    logger.info(f"   Composite Score: {composite_score:.4f}")
                    logger.info(f"   RMSE CV: {avg_metrics['avg_rmse_cv']:.3f} (±{avg_metrics['std_rmse_cv']:.3f})")
                    logger.info(f"   MAE CV: {avg_metrics['avg_mae_cv']:.3f}")
                    logger.info(f"   MAPE CV: {avg_metrics['avg_mape_cv']:.2f}%")
                    logger.info(f"   AIC: {results.aic:.2f}")
                
            except Exception as e:
                continue
    
    # Enhanced fallback logic with business constraints
    if best_order is None or best_seasonal_order is None:
        logger.warning("🔄 No valid combination found, applying enhanced fallback logic...")
        
        # Try progressively simpler models based on data characteristics
        data_length = len(time_series)
        has_trend = abs(np.corrcoef(range(len(time_series)), time_series)[0,1]) > 0.3
        seasonal_strength = 0
        
        try:
            # Quick seasonal strength estimation
            if data_length >= 2 * seasonal_period:
                seasonal_data = time_series.values.reshape(-1, seasonal_period)
                seasonal_strength = np.std(np.mean(seasonal_data, axis=0)) / np.mean(time_series)
        except:
            pass
        
        # Adaptive fallback parameters
        if data_length < 30:  # Very short series
            best_order = (1, 0, 0)
            best_seasonal_order = (0, 0, 0, s)
        elif seasonal_strength > 0.2 and data_length >= seasonal_period:  # Strong seasonality
            best_order = (1, 1, 1)
            best_seasonal_order = (1, 1, 1, s)
        elif has_trend:  # Trend present
            best_order = (1, 1, 1)
            best_seasonal_order = (0, 0, 0, s)
        else:  # Simple stationary model
            best_order = (1, 0, 1)
            best_seasonal_order = (0, 0, 0, s)
        
        logger.info(f"🛠️ Fallback parameters selected: {best_order}, {best_seasonal_order}")
        logger.info(f"   Data characteristics: length={data_length}, trend={has_trend}, seasonal_strength={seasonal_strength:.3f}")
    
    # Compile final results with enhanced information
    best_result = None
    if evaluation_results:
        best_result = min(evaluation_results, key=lambda x: x['composite_score'])
    
    suggested_parameters = {
        'p': best_order[0],
        'd': best_order[1],
        'q': best_order[2],
        'P': best_seasonal_order[0],
        'D': best_seasonal_order[1],
        'Q': best_seasonal_order[2],
        's': best_seasonal_order[3],
        # Enhanced metadata
        'optimization_info': {
            'total_combinations_tested': current_combination,
            'computation_time': time.time() - start_time,
            'k_fold_validation': k_fold,
            'business_constraints_applied': business_constraints,
            'revenue_weight': revenue_weight
        }
    }
    
    if best_result:
        suggested_parameters['metrics'] = {
            'composite_score': best_result['composite_score'],
            'aic': best_result['aic'],
            'bic': best_result['bic'],
            'rmse_cv_mean': best_result['avg_rmse_cv'],
            'rmse_cv_std': best_result['std_rmse_cv'],
            'mae_cv_mean': best_result['avg_mae_cv'],
            'mape_cv_mean': best_result['avg_mape_cv'],
            'bias_cv_mean': best_result['avg_bias_cv'],
            'prediction_quality': 'High' if best_result['avg_mape_cv'] < 15 else 'Medium' if best_result['avg_mape_cv'] < 30 else 'Low'
        }
    
    # Final summary
    total_time = time.time() - start_time
    logger.info(f"✅ Enhanced SARIMA optimization completed in {total_time:.2f} seconds")
    logger.info(f"🏆 Best parameters: SARIMA{best_order}×{best_seasonal_order}")
    
    if best_result:
        logger.info(f"📊 Performance metrics:")
        logger.info(f"   • Composite Score: {best_result['composite_score']:.4f}")
        logger.info(f"   • Cross-validation RMSE: {best_result['avg_rmse_cv']:.3f} (±{best_result['std_rmse_cv']:.3f})")
        logger.info(f"   • Cross-validation MAPE: {best_result['avg_mape_cv']:.2f}%")
        logger.info(f"   • AIC: {best_result['aic']:.2f}")
        logger.info(f"   • Prediction Quality: {suggested_parameters['metrics']['prediction_quality']}")
    
    print(f"🎯 Enhanced SARIMA parameters optimized: {suggested_parameters}")
    return suggested_parameters

# Ajuster le modèle SARIMA et faire des prédictions
def fit_sarima_and_predict(time_series, params, forecast_steps=12, prediction_type='visits', enhanced_predictor=None):
    """
    Enhanced SARIMA prediction with validation and business constraints
    
    Args:
        time_series: Série temporelle pour le modèle
        params: Paramètres SARIMA (p, d, q, P, D, Q, s)
        forecast_steps: Nombre de périodes à prévoir
        prediction_type: Type of prediction ('visits', 'deliveries', 'quantity')
        enhanced_predictor: Instance of EnhancedPredictionSystem for constraints
    
    Returns:
        forecast: Enhanced predictions with constraints
        model: Modèle SARIMA ajusté
        metrics: Enhanced metrics with quality scores
    """
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('enhanced_sarima_forecast')
    
    # Extraire les paramètres
    p, d, q = params['p'], params['d'], params['q']
    P, D, Q, s = params['P'], params['D'], params['Q'], params['s']
    
    # Créer et ajuster le modèle
    logger.info(f"Création du modèle SARIMA({p},{d},{q})({P},{D},{Q},{s})")
    model = SARIMAX(
        time_series,
        order=(p, d, q),
        seasonal_order=(P, D, Q, s),
        enforce_stationarity=False,
        enforce_invertibility=False
    )
    
    # Augmenter le nombre maximum d'itérations pour une meilleure convergence
    results = model.fit(disp=False, maxiter=500)
    
    # Résumé du modèle
    logger.info("Modèle SARIMA ajusté avec succès")
    logger.info(f"Log likelihood: {results.llf:.2f}, AIC: {results.aic:.2f}, BIC: {results.bic:.2f}")
      # Calculer multiples métriques d'évaluation sur l'historique
    try:
        # Prédictions in-sample pour évaluation
        pred = results.get_prediction(start=s, end=len(time_series)-1)
        y_true = time_series[s:]
        y_pred = pred.predicted_mean
        
        # Mean Absolute Error (MAE)
        mae = np.mean(np.abs(y_true - y_pred))
        # Root Mean Square Error (RMSE)
        rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
        # Mean Absolute Percentage Error (MAPE)
        mape = np.mean(np.abs((y_true - y_pred) / np.maximum(0.1, y_true))) * 100
        # Symmetric MAPE (sMAPE) - plus robuste lorsque certaines valeurs sont proches de zéro
        smape = np.mean(2 * np.abs(y_true - y_pred) / (np.abs(y_true) + np.abs(y_pred) + 0.1)) * 100
        # R²
        ss_total = np.sum((y_true - y_true.mean()) ** 2)
        ss_residual = np.sum((y_true - y_pred) ** 2)
        r_squared = 1 - (ss_residual / ss_total) if ss_total > 0 else 0
          # Stocker les métriques pour la sortie
        metrics = {
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'smape': smape,
            'r_squared': r_squared,
            'aic': results.aic,
            'bic': results.bic
        }
        
        logger.info(f"Métriques d'évaluation:")
        logger.info(f"MAE: {mae:.2f}")
        logger.info(f"RMSE: {rmse:.2f}")
        logger.info(f"MAPE: {mape:.2f}%")
        logger.info(f"sMAPE: {smape:.2f}%")
        logger.info(f"R²: {r_squared:.4f}")
        
        # Afficher un résumé des métriques
        print(f"SARIMA - Métriques d'évaluation sur l'historique:")
        print(f"MAE: {mae:.2f}")
        print(f"RMSE: {rmse:.2f}")
        print(f"MAPE: {mape:.2f}%")
        print(f"sMAPE: {smape:.2f}%")
        print(f"R²: {r_squared:.4f}")
        
        # Précision approximative (1 - sMAPE/100)
        accuracy = max(0, min(100, 100 - smape))
        print(f"Précision approximative: {accuracy:.2f}%")
        
    except Exception as e:
        logger.error(f"Erreur lors du calcul des métriques: {str(e)}")
        print(f"Erreur lors du calcul des métriques: {str(e)}")
      # Prévisions avec intervalle de confiance
    logger.info(f"Génération des prévisions pour {forecast_steps} périodes...")
    forecast = results.get_forecast(steps=forecast_steps)
    forecast_mean = forecast.predicted_mean
    forecast_ci = forecast.conf_int(alpha=0.05)  # Intervalle de confiance à 95%
      # Apply enhanced business constraints
    logger.info("Application des contraintes métier...")
    if enhanced_predictor:
        constrained_predictions = enhanced_predictor.apply_business_constraints(
            forecast_mean.values, prediction_type
        )
    else:
        constrained_predictions = forecast_mean.values
    
    # Apply seasonal adjustments if available
    if enhanced_predictor and hasattr(enhanced_predictor, 'seasonal_enhancement_enabled') and enhanced_predictor.seasonal_enhancement_enabled:
        # Generate future dates for seasonal adjustment
        last_date = time_series.index[-1] if hasattr(time_series, 'index') else datetime.now()
        future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=forecast_steps, freq='D')
        
        # Try to extract commercial code from context (you may need to pass this as parameter)
        commercial_code = getattr(fit_sarima_and_predict, '_current_commercial', '1')
        
        # Apply seasonal adjustments
        if enhanced_predictor:
            seasonally_adjusted_predictions, seasonal_adjustments = enhanced_predictor.apply_seasonal_adjustments(
                constrained_predictions, commercial_code, future_dates
            )
            
            if seasonal_adjustments:
                logger.info(f"Ajustements saisonniers appliqués: {', '.join(seasonal_adjustments)}")
                constrained_predictions = seasonally_adjusted_predictions
        
    # Apply constraints to confidence intervals
    if enhanced_predictor:
        constrained_lower = enhanced_predictor.apply_business_constraints(
            forecast_ci.iloc[:, 0].values, prediction_type
        )
        constrained_upper = enhanced_predictor.apply_business_constraints(
            forecast_ci.iloc[:, 1].values, prediction_type
        )
    else:
        constrained_lower = forecast_ci.iloc[:, 0].values
        constrained_upper = forecast_ci.iloc[:, 1].values
    
    # Ensure confidence intervals make sense
    constrained_lower = np.minimum(constrained_lower, constrained_predictions - 0.5)
    constrained_upper = np.maximum(constrained_upper, constrained_predictions + 0.5)
    
    # Create enhanced forecast series with constraints
    enhanced_forecast = pd.Series(constrained_predictions, index=forecast_mean.index)
    
    # Calculate prediction quality score
    ci_dict = {'lower': constrained_lower, 'upper': constrained_upper}
    if enhanced_predictor:
        quality_score = enhanced_predictor.calculate_prediction_quality_score(
            constrained_predictions, ci_dict
        )
    else:
        # Simple quality score calculation
        quality_score = 75.0  # Default moderate quality score
    
    # Stocker les intervalles dans les métriques avec contraintes appliquées
    metrics['forecast_lower'] = pd.Series(constrained_lower, index=forecast_mean.index)
    metrics['forecast_upper'] = pd.Series(constrained_upper, index=forecast_mean.index)
    metrics['prediction_quality_score'] = quality_score
    metrics['constraints_applied'] = True
    metrics['prediction_type'] = prediction_type
    
    logger.info(f"Contraintes appliquées. Score de qualité: {quality_score:.1f}/100")
      # Visualiser les prévisions avec l'intervalle de confiance amélioré
    plt.figure(figsize=(12, 8))
    plt.plot(time_series, label='Observations historiques', color='blue')
    plt.plot(enhanced_forecast, label='Prédictions avec contraintes', color='red', linestyle='-')
    plt.fill_between(
        enhanced_forecast.index,
        constrained_lower,
        constrained_upper,
        color='pink', alpha=0.3, label='Intervalle de confiance 95% (contraint)'
    )
    
    # Ajouter une légende détaillée avec les métriques améliorées
    plt.title(f'Prévisions SARIMA améliorées - Score qualité: {quality_score:.1f}/100')
    plt.legend(loc='best')
    plt.grid(True, alpha=0.3)
    plt.savefig('enhanced_sarima_forecast.png', dpi=300)
    plt.close()
    
    return enhanced_forecast, results, metrics

# Générer un plan d'optimisation des livraisons
def generate_delivery_optimization_plan(forecast, commercial_code):
    """
    Génère un plan d'optimisation des livraisons basé sur les prévisions SARIMA
    
    Args:
        forecast: Prévisions du modèle SARIMA
        commercial_code: Code du commercial
    
    Returns:
        optimization_plan: DataFrame avec le plan d'optimisation
    """
    # Créer un DataFrame pour le plan d'optimisation
    optimization_plan = pd.DataFrame({
        'date': forecast.index,
        'commercial_code': commercial_code,
        'livraisons_prevues': np.round(forecast.values),
        'confiance': np.where(forecast.values > forecast.mean(), 'Élevée', 'Modérée')
    })
    
    # Ajouter des recommandations
    optimization_plan['recommandation'] = np.where(
        optimization_plan['livraisons_prevues'] > forecast.mean() * 1.2,
        'Prévoir personnel supplémentaire',
        np.where(
            optimization_plan['livraisons_prevues'] < forecast.mean() * 0.8,
            'Possibilité de réduire les ressources',
            'Maintenir les ressources actuelles'
        )
    )
    
    return optimization_plan

# Fonction principale pour exécuter l'analyse SARIMA
def run_sarima_analysis(commercial_code, metric='nombre_livraisons', frequency='W', forecast_periods=12, target_date=None, target_clients=None):
    """
    Exécute l'analyse SARIMA complète pour un commercial
    
    Args:
        commercial_code: Code du commercial à analyser
        metric: Métrique à analyser ('nombre_livraisons', 'nb_clients_visites', 'valeur_totale')
        frequency: Fréquence d'analyse ('D', 'W', 'M')
        forecast_periods: Nombre de périodes à prévoir
        target_date: Date cible spécifique (format 'YYYY-MM-DD')
        target_clients: Nombre de clients cible pour la date spécifique
    
    Returns:
        optimization_plan: Plan d'optimisation des livraisons
    """
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('sarima_analysis')
    
    # Périodes saisonnières selon la fréquence
    seasonal_periods = {'D': 7, 'W': 52, 'M': 12}
    
    # Récupérer les données historiques
    logger.info(f"Récupération des données pour le commercial {commercial_code}...")
    # Élargir la plage de dates pour avoir plus de données historiques (3 ans)
    current_date = datetime.now()
    date_debut = (current_date - timedelta(days=365*3)).strftime('%Y-%m-%d')
    date_fin = current_date.strftime('%Y-%m-%d')
    historical_data = get_historical_deliveries(date_debut, date_fin)
    
    if historical_data.empty:
        logger.error("Aucune donnée trouvée")
        return None
      # Préparer les données pour SARIMA
    logger.info(f"Préparation des données avec fréquence {frequency} pour l'analyse de {metric}...")
    time_series = prepare_data_for_sarima(historical_data, commercial_code, metric=metric, freq=frequency)
    
    if len(time_series) < 2 * seasonal_periods[frequency]:
        logger.error(f"Données insuffisantes pour l'analyse SARIMA. Au moins {2 * seasonal_periods[frequency]} périodes requises.")
        return None
    
    # Détecter et traiter les valeurs aberrantes (outliers)
    def detect_and_handle_outliers(series, threshold=3):
        # Calculer la moyenne et l'écart-type
        mean = series.mean()
        std = series.std()
        # Identifier les valeurs aberrantes (Z-score > threshold)
        z_scores = np.abs((series - mean) / std)
        outliers = series[z_scores > threshold]
        if len(outliers) > 0:
            logger.info(f"Détection de {len(outliers)} valeurs aberrantes")
            # Remplacer les valeurs aberrantes par la médiane
            for idx in outliers.index:
                series.at[idx] = series.median()
            logger.info("Valeurs aberrantes remplacées par la médiane")
        return series
    
    # Gestion des outliers si le dataset est assez grand
    if len(time_series) >= 30:
        time_series = detect_and_handle_outliers(time_series)
      # Identifier les paramètres avec contraintes métier
    logger.info("Identification des paramètres SARIMA optimaux avec contraintes métier...")
    
    # Définir les contraintes métier selon la métrique analysée
    business_constraints = {
        'min_forecast_accuracy': 0.75 if metric == 'valeur_totale' else 0.70,
        'max_computation_time': 180,  # 3 minutes max pour une analyse interactive
        'prefer_simpler_models': True,
        'seasonal_importance': 0.9 if frequency == 'W' else 0.7
    }
    
    # Poids de revenu plus élevé pour les métriques liées à la valeur
    revenue_weight = 0.4 if metric == 'valeur_totale' else 0.3
    
    params = identify_sarima_parameters(
        time_series, 
        seasonal_period=seasonal_periods[frequency],
        business_constraints=business_constraints,
        revenue_weight=revenue_weight
    )
    
    # Ajuster le modèle et faire des prédictions
    logger.info("Ajustement du modèle SARIMA et génération des prévisions...")
    
    # Calculer le nombre de périodes nécessaires pour atteindre la date cible
    target_forecast_steps = forecast_periods
    if target_date:
        target_date_obj = pd.to_datetime(target_date)        # Calculer combien de périodes il faut prévoir pour atteindre la date cible
        last_data_date = time_series.index[-1]
        
        if frequency == 'D':
            periods_to_target = (target_date_obj - last_data_date).days
        elif frequency == 'W':
            periods_to_target = (target_date_obj - last_data_date).days // 7 + 1
        elif frequency == 'M':
            periods_to_target = ((target_date_obj.year - last_data_date.year) * 12 + 
                               target_date_obj.month - last_data_date.month)
        
        # S'assurer que nous prévoyons assez loin
        target_forecast_steps = max(forecast_periods, periods_to_target + 5)
        logger.info(f"Prévisions étendues à {target_forecast_steps} périodes pour atteindre la date cible {target_date}")
    
    # Ajuster le modèle et obtenir les prévisions améliorées
    forecast, model, metrics = fit_sarima_and_predict(
        time_series, 
        params, 
        forecast_steps=target_forecast_steps,
        prediction_type='visits' if metric == 'nb_clients_visites' else 'deliveries'
    )
    
    # Générer le plan d'optimisation
    logger.info(f"Génération du plan d'optimisation basé sur {metric}...")
    
    # Créer un DataFrame pour le plan d'optimisation
    optimization_plan = pd.DataFrame({
        'date': forecast.index,
        'commercial_code': commercial_code,
        f'{metric}_prevus': np.round(forecast.values),
        'confiance_inf': np.round(metrics['forecast_lower']),
        'confiance_sup': np.round(metrics['forecast_upper']),
    })
    
    # Ajouter le niveau de confiance
    optimization_plan['confiance'] = np.where(
        (optimization_plan[f'{metric}_prevus'] - optimization_plan['confiance_inf']) < 
        (optimization_plan['confiance_sup'] - optimization_plan[f'{metric}_prevus']),
        'Élevée',
        'Modérée'
    )
    
    # Si nous avons une date cible et un nombre cible de clients
    if target_date and target_clients:
        logger.info(f"Ajustement des prévisions pour la date cible {target_date} avec {target_clients} clients")
        target_date_obj = pd.to_datetime(target_date)
        
        # Trouver la date la plus proche dans nos prévisions
        closest_dates = optimization_plan['date'].dt.strftime('%Y-%m-%d').apply(
            lambda x: abs((pd.to_datetime(x) - target_date_obj).total_seconds()))
        closest_idx = closest_dates.idxmin()
        
        if closest_idx is not None:
            # Remplacer la prévision par le nombre exact de clients pour la date cible
            logger.info(f"Date la plus proche trouvée: {optimization_plan.at[closest_idx, 'date']}")
            original_prediction = optimization_plan.at[closest_idx, f'{metric}_prevus']
            optimization_plan.at[closest_idx, f'{metric}_prevus'] = target_clients
            logger.info(f"Prévision ajustée pour {target_date}: {original_prediction} -> {target_clients}")
            
            # Ajuster également les intervalles de confiance autour de la valeur cible
            confidence_range = optimization_plan.at[closest_idx, 'confiance_sup'] - optimization_plan.at[closest_idx, 'confiance_inf']
            optimization_plan.at[closest_idx, 'confiance_inf'] = max(0, target_clients - confidence_range/4)
            optimization_plan.at[closest_idx, 'confiance_sup'] = target_clients + confidence_range/4
            
            # Marquer cette prévision comme exacte
            optimization_plan.at[closest_idx, 'confiance'] = 'Exacte'
            logger.info(f"Confiance définie comme 'Exacte' pour la date cible")
      # Ajouter des recommandations adaptées à la métrique
    if metric == 'nombre_livraisons':
        optimization_plan['recommandation'] = np.where(
            optimization_plan[f'{metric}_prevus'] > forecast.mean() * 1.2,
            'Prévoir personnel supplémentaire pour les livraisons',
            np.where(
                optimization_plan[f'{metric}_prevus'] < forecast.mean() * 0.8,
                'Possibilité de réduire les ressources de livraison',
                'Maintenir les ressources de livraison actuelles'
            )
        )
    elif metric == 'nb_clients_visites':
        optimization_plan['recommandation'] = np.where(
            optimization_plan[f'{metric}_prevus'] > forecast.mean() * 1.2,
            'Prévoir plus de temps pour les visites clients',
            np.where(
                optimization_plan[f'{metric}_prevus'] < forecast.mean() * 0.8,
                'Possibilité d\'ajouter plus de clients à visiter',
                'Maintenir le planning actuel de visites clients'
            )        )
    else:  # valeur_totale
        optimization_plan['recommandation'] = np.where(
            optimization_plan[f'{metric}_prevus'] > forecast.mean() * 1.2,
            'Haute priorité - Anticiper les besoins logistiques',
            np.where(
                optimization_plan[f'{metric}_prevus'] < forecast.mean() * 0.8,
                'Envisager des actions commerciales pour stimuler les ventes',
                'Maintenir la stratégie commerciale actuelle'            )
        )
    
    # Afficher le plan d'optimisation
    logger.info(f"\nPlan d'optimisation basé sur {metric}:")
    logger.info(optimization_plan.to_string())
    
    # Retourner le plan d'optimisation
    return optimization_plan

# Analyser les tendances saisonnières pour tous les commerciaux
def analyze_seasonal_patterns():
    """
    Analyse les tendances saisonnières pour l'ensemble des commerciaux
    """
    # Récupérer les données
    df = get_historical_deliveries()
    
    if df.empty:
        print("Aucune donnée trouvée")
        return
    
    # Grouper par mois pour visualiser les tendances saisonnières
    df['month'] = df['date'].dt.month
    df['year'] = df['date'].dt.year
    
    monthly_patterns = df.groupby(['year', 'month', 'commercial_code']).agg({
        'nombre_livraisons': 'sum',
        'valeur_totale': 'sum'
    }).reset_index()
    
    # Visualiser les tendances pour les principaux commerciaux
    top_commercials = df['commercial_code'].value_counts().head(5).index.tolist()
    
    plt.figure(figsize=(15, 8))
    for commercial in top_commercials:
        comm_data = monthly_patterns[monthly_patterns['commercial_code'] == commercial]
        plt.plot(
            [f"{year}-{month:02d}" for year, month in zip(comm_data['year'], comm_data['month'])],
            comm_data['nombre_livraisons'],
            label=f"Commercial {commercial}"
        )
    
    plt.title("Tendances saisonnières des livraisons par commercial")
    plt.xlabel("Période")
    plt.ylabel("Nombre de livraisons")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('seasonal_patterns.png')
    plt.close()
    
    print("Analyse des tendances saisonnières terminée. Consultez 'seasonal_patterns.png'")

# ===================== SARIMA VISITS FORECASTING (NEW BLOCK) =====================
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.statespace.sarimax import SARIMAX
import mysql.connector
import warnings
warnings.filterwarnings('ignore')

# Duplicate function removed - using the SQLAlchemy version above

def get_commercial_visits(date_debut=None, date_fin=None, commercial_code=None):
    """
    Récupérer les visites journalières des commerciaux
    """
    conn = get_db_connection()
    query = """
    SELECT 
        ec.date,
        ec.commercial_code,
        COUNT(DISTINCT ec.client_code) as nombre_visites,
        COUNT(DISTINCT lc.produit_code) as nombre_produits_vendus,
        SUM(ec.net_a_payer) as chiffre_affaires
    FROM entetecommercials ec
    LEFT JOIN lignecommercials lc ON lc.entetecommercial_code = ec.code
    WHERE 1=1
    """
    params = []
    if date_debut:
        query += " AND ec.date >= %s"
        params.append(date_debut)
    if date_fin:
        query += " AND ec.date <= %s"
        params.append(date_fin)
    if commercial_code:
        query += " AND ec.commercial_code = %s"
        params.append(commercial_code)
    query += " GROUP BY ec.date, ec.commercial_code ORDER BY ec.date"
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    df['date'] = pd.to_datetime(df['date'])
    return df

def train_sarima_model(data):
    """
    Entraîner un modèle SARIMA sur les données de visites
    """
    model = SARIMAX(
        data,
        order=(1, 1, 1),
        seasonal_order=(1, 1, 1, 7),
        enforce_stationarity=False,
        enforce_invertibility=False
    )
    fitted_model = model.fit(disp=False)
    return fitted_model

def predict_future_visits_sarima(historical_data, days_to_predict=730):  # 2 ans
    """
    Prédire les futures visites avec SARIMA
    """
    predictions = {}
    for commercial in historical_data['commercial_code'].unique():
        commercial_data = historical_data[historical_data['commercial_code'] == commercial].copy()
        
        # Ensure the date column is properly converted to datetime
        if 'date' in commercial_data.columns:
            commercial_data['date'] = pd.to_datetime(commercial_data['date'], errors='coerce')
            # Drop rows with invalid dates
            commercial_data = commercial_data.dropna(subset=['date'])
        
        if commercial_data.empty:
            print(f"Warning: No valid data for commercial {commercial} after date conversion")
            continue
            
        date_range = pd.date_range(
            start=commercial_data['date'].min(),
            end=commercial_data['date'].max(),
            freq='D'
        )
        
        # Properly aggregate visits by day before creating time series
        # Now we can safely use .dt.date since we've ensured it's datetime
        commercial_data['date_only'] = commercial_data['date'].dt.date
        daily_aggregated = commercial_data.groupby('date_only')['nombre_visites'].sum().reset_index()
        daily_aggregated['date_only'] = pd.to_datetime(daily_aggregated['date_only'])
        ts_data = daily_aggregated.set_index('date_only')['nombre_visites'].reindex(date_range).fillna(0)
        
        try:
            model = train_sarima_model(ts_data)
            
            # Ensure historical_data has proper datetime column for max() operation
            if 'date' in historical_data.columns:
                historical_data['date'] = pd.to_datetime(historical_data['date'], errors='coerce')
            
            last_date = historical_data['date'].max()
            
            # S'assurer que last_date est un datetime object propre
            if isinstance(last_date, pd.Timestamp):
                last_date = last_date.to_pydatetime()
            elif isinstance(last_date, str):
                last_date = pd.to_datetime(last_date).to_pydatetime()
            elif pd.isna(last_date):
                # Fallback to current date if no valid date found
                last_date = datetime.now()
                
            future_dates = pd.date_range(
                start=last_date + timedelta(days=1),
                periods=days_to_predict,
                freq='D'
            )
            forecast = model.get_forecast(steps=days_to_predict)
            predicted_mean = forecast.predicted_mean
            conf_int = forecast.conf_int()# Always use string commercial_code as key to avoid type mismatches
            predictions[str(commercial)] = {
                'dates': future_dates,
                'predictions': predicted_mean.values,
                'lower_ci': conf_int.iloc[:, 0].values,
                'upper_ci': conf_int.iloc[:, 1].values,
                'stats': {
                    'moyenne_visites_predites': np.mean(predicted_mean),
                    'max_visites_predites': np.max(predicted_mean),
                    'min_visites_predites': np.min(predicted_mean),
                    'total_visites_predites': np.sum(predicted_mean),
                    'aic': model.aic,
                    'bic': model.bic
                }
            }
        except Exception as e:
            print(f"Erreur lors de la prédiction pour le commercial {commercial}: {str(e)}")
            continue
    return predictions

def plot_visits_analysis_sarima(df, predictions, commercial_code=None):
    """
    Générer des graphiques d'analyse avec les prédictions SARIMA
    """
    if commercial_code:
        df = df[df['commercial_code'] == commercial_code]
    plt.figure(figsize=(20, 12))
    plt.subplot(2, 2, 1)
    for commercial, pred in predictions.items():
        if commercial_code is None or commercial == commercial_code:
            hist_data = df[df['commercial_code'] == commercial]
            plt.plot(hist_data['date'], hist_data['nombre_visites'], 
                    label=f'Historique {commercial}', alpha=0.6)
            plt.plot(pred['dates'], pred['predictions'], '--', 
                    label=f'Prédictions {commercial}')
            plt.fill_between(pred['dates'], 
                           pred['lower_ci'], 
                           pred['upper_ci'], 
                           alpha=0.2)
    plt.title('Visites historiques et prédictions SARIMA')
    plt.legend()
    plt.xticks(rotation=45)
    plt.subplot(2, 2, 2)
    df['jour_semaine'] = df['date'].dt.day_name()
    avg_visits = df.groupby(['jour_semaine', 'commercial_code'])['nombre_visites'].mean().reset_index()
    sns.barplot(data=avg_visits, x='jour_semaine', y='nombre_visites', hue='commercial_code')
    plt.title('Moyenne des visites par jour de la semaine')
    plt.xticks(rotation=45)
    plt.subplot(2, 2, 3)
    sns.boxplot(data=df, x='commercial_code', y='nombre_visites')
    plt.title('Distribution des visites par commercial')
    plt.subplot(2, 2, 4)
    df['mois'] = df['date'].dt.strftime('%Y-%m')
    monthly_avg = df.groupby(['mois', 'commercial_code'])['nombre_visites'].mean().reset_index()
    sns.lineplot(data=monthly_avg, x='mois', y='nombre_visites', hue='commercial_code')
    plt.title('Tendance mensuelle des visites')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def save_predictions_to_csv(predictions, output_file='predictions_visites_sarima.csv'):
    """
    Sauvegarder les prédictions dans un fichier CSV
    """
    rows = []
    for commercial, pred in predictions.items():
        for i, (date, visits, lower, upper) in enumerate(zip(
            pred['dates'], pred['predictions'], pred['lower_ci'], pred['upper_ci'])):
            rows.append({
                'commercial_code': commercial,
                'date': date.strftime('%Y-%m-%d'),
                'visites_predites': round(max(0, visits), 1),
                'intervalle_confiance_min': round(max(0, lower), 1),
                'intervalle_confiance_max': round(max(0, upper), 1)
            })
    pd.DataFrame(rows).to_csv(output_file, index=False)
    print(f"Prédictions sauvegardées dans {output_file}")

def save_predictions_to_json(predictions, output_file='predictions_sarima_optimization.json'):
    """
    Sauvegarder les prédictions et optimisations dans un fichier JSON
    """
    import json
    from datetime import datetime
    
    json_data = {
        'metadata': {
            'export_date': datetime.now().isoformat(),
            'total_commercials': len(predictions),
            'prediction_type': 'sarima_delivery_optimization',
            'model': 'SARIMA',
            'version': '2.0'
        },
        'predictions': {}
    }
    
    for commercial, pred in predictions.items():
        json_data['predictions'][commercial] = {
            'statistics': pred.get('stats', {}),
            'model_info': {
                'aic': pred.get('stats', {}).get('aic', 0),
                'bic': pred.get('stats', {}).get('bic', 0),
                'model_params': pred.get('model_params', {}),
                'seasonal_params': pred.get('seasonal_params', {}),
                'model_quality': pred.get('model_quality', 0)
            },
            'optimization_data': {
                'total_predicted_visits': pred.get('stats', {}).get('total_visites_predites', 0),
                'avg_visits_per_day': pred.get('stats', {}).get('moyenne_visites_predites', 0),
                'max_visits_day': pred.get('stats', {}).get('max_visites_predites', 0),
                'min_visits_day': pred.get('stats', {}).get('min_visites_predites', 0)
            },
            'forecast_data': []
        }
        
        # Add detailed forecast data
        for i, (date, visits, lower, upper) in enumerate(zip(
            pred['dates'], pred['predictions'], pred['lower_ci'], pred['upper_ci'])):
            json_data['predictions'][commercial]['forecast_data'].append({
                'date': date.strftime('%Y-%m-%d'),
                'predicted_visits': round(max(0, visits), 1),
                'confidence_interval': {
                    'lower': round(max(0, lower), 1),
                    'upper': round(max(0, upper), 1)
                },
                'day_info': {
                    'day_of_week': date.strftime('%A'),
                    'week_number': date.isocalendar()[1],
                    'month': date.strftime('%B'),
                    'quarter': f"Q{(date.month-1)//3 + 1}",
                    'is_weekend': date.weekday() >= 5
                },
                'optimization_score': round(max(0, visits) / max(1, pred.get('stats', {}).get('moyenne_visites_predites', 1)), 2)
            })
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"Optimisations SARIMA sauvegardées en JSON dans {output_file}")

def save_dual_optimization_to_json(results, output_file='dual_optimization_results.json'):
    """
    Sauvegarder les résultats de l'optimisation duale en JSON
    """
    import json
    from datetime import datetime
    
    if not results:
        print("Aucun résultat à sauvegarder")
        return
    
    # Convert pandas objects to serializable format
    json_data = {
        'metadata': {
            'export_date': datetime.now().isoformat(),
            'commercial_code': results.get('commercial_code'),
            'analysis_period': {
                'start_date': results.get('start_date'),
                'end_date': results.get('end_date')
            },
            'optimization_type': 'dual_visits_revenue',
            'model': 'Enhanced_SARIMA',
            'prediction_days': 365
        },
        'summary': results.get('summary', {}),
        'model_performance': results.get('model_performance', {}),
        'insights': results.get('insights', {}),
        'weekly_patterns': {},
        'monthly_summary': {},
        'daily_plan': []
    }
    
    # Add weekly patterns
    if 'weekly_patterns' in results:
        for day, values in results['weekly_patterns'].items():
            json_data['weekly_patterns'][day] = {
                'avg_visits': float(values.get('avg_visits', 0)),
                'avg_revenue': float(values.get('avg_revenue', 0)),
                'confidence_score': float(values.get('confidence_score', 0))
            }
    
    # Add monthly summary
    if 'monthly_summary' in results:
        monthly_df = results['monthly_summary']
        for month in monthly_df.index:
            json_data['monthly_summary'][month] = {
                'total_visits': float(monthly_df.loc[month, ('predicted_visits', 'sum')]),
                'total_revenue': float(monthly_df.loc[month, ('predicted_revenue', 'sum')]),
                'avg_daily_visits': float(monthly_df.loc[month, ('predicted_visits', 'mean')]),
                'avg_daily_revenue': float(monthly_df.loc[month, ('predicted_revenue', 'mean')])
            }
    
    # Add daily plan
    if 'daily_plan' in results:
        daily_df = results['daily_plan']
        for _, row in daily_df.iterrows():
            json_data['daily_plan'].append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'predicted_visits': float(row['predicted_visits']),
                'predicted_revenue': float(row.get('predicted_revenue', 0)),
                'visits_lower_ci': float(row.get('visits_lower_ci', 0)),
                'visits_upper_ci': float(row.get('visits_upper_ci', 0)),
                'revenue_lower_ci': float(row.get('revenue_lower_ci', 0)),
                'revenue_upper_ci': float(row.get('revenue_upper_ci', 0)),
                'day_of_week': row['day_of_week'],
                'confidence_level': row['confidence_level'],
                'optimization_priority': row.get('optimization_priority', 'medium')
            })
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"Résultats d'optimisation duale sauvegardés en JSON dans {output_file}")

# Enhanced Prediction System Integration
class EnhancedPredictionSystem:
    """Enhanced prediction system with realistic constraints and validation"""
    
    def __init__(self, min_revenue=0):
        self.min_visits_per_day = 0
        self.max_visits_per_day = 20  # Realistic maximum
        self.min_quantity = 0
        self.max_quantity_per_client = 100  # Realistic maximum per client per day
        self.min_revenue = min_revenue  # Chiffre d'affaires minimum défini par l'utilisateur
        
        # Initialize seasonal pattern enhancer
        try:
            from seasonal_pattern_enhancement import SeasonalPatternEnhancer
            self.seasonal_enhancer = SeasonalPatternEnhancer()
            self.seasonal_enhancement_enabled = True
            print("✓ Seasonal pattern enhancement initialized")
        except ImportError:
            self.seasonal_enhancer = None
            self.seasonal_enhancement_enabled = False
            print("⚠️ Seasonal pattern enhancement not available")
        
        # Cache for seasonal patterns
        self._seasonal_patterns_analyzed = False
        self._last_analysis_data_hash = None
        
    def analyze_seasonal_patterns(self, historical_data):
        """Analyze seasonal patterns in historical data"""
        if not self.seasonal_enhancement_enabled:
            return {}
            
        try:
            # Check if we need to reanalyze patterns
            data_hash = hash(str(historical_data.shape) + str(historical_data['date'].min()) + str(historical_data['date'].max()))
            
            if not self._seasonal_patterns_analyzed or data_hash != self._last_analysis_data_hash:
                print("🔍 Analyzing seasonal patterns...")
                
                # Run comprehensive seasonal analysis
                self.seasonal_report = self.seasonal_enhancer.analyze_all_patterns(historical_data)
                self._seasonal_patterns_analyzed = True
                self._last_analysis_data_hash = data_hash
                
                print(f"✓ Seasonal patterns analyzed for {self.seasonal_report['commercials_analyzed']} commercials")
                
            return self.seasonal_report
            
        except Exception as e:
            print(f"⚠️ Error in seasonal pattern analysis: {e}")
            return {}
    
    def get_enhanced_sarima_params(self, commercial_code, base_params, historical_data=None):
        """Get enhanced SARIMA parameters with seasonal optimization"""
        enhanced_params = base_params.copy()
        
        if not self.seasonal_enhancement_enabled:
            return enhanced_params
            
        try:
            # Analyze patterns if historical data is provided
            if historical_data is not None:
                self.analyze_seasonal_patterns(historical_data)
            
            # Get enhanced parameters from seasonal enhancer
            if hasattr(self, 'seasonal_enhancer'):
                enhanced_params = self.seasonal_enhancer.generate_enhanced_sarima_params(
                    commercial_code, base_params
                )
                
                print(f"📈 Enhanced SARIMA params for commercial {commercial_code}: {enhanced_params}")
                
        except Exception as e:
            print(f"⚠️ Error enhancing SARIMA params: {e}")
            
        return enhanced_params
    
    def apply_seasonal_adjustments(self, predictions, commercial_code, prediction_dates):
        """Apply seasonal adjustments to predictions"""
        if not self.seasonal_enhancement_enabled:
            return predictions, []
            
        try:
            adjusted_predictions, adjustments_applied = self.seasonal_enhancer.apply_seasonal_adjustments(
                predictions, commercial_code, prediction_dates
            )
            
            if adjustments_applied:
                print(f"🔧 Seasonal adjustments applied to commercial {commercial_code}: {', '.join(adjustments_applied)}")
                
            return adjusted_predictions, adjustments_applied
            
        except Exception as e:
            print(f"⚠️ Error applying seasonal adjustments: {e}")
            return predictions, []
        
    def apply_business_constraints(self, predictions, prediction_type='visits'):
        """
        Apply business logic constraints to predictions including revenue constraints
        
        Args:
            predictions: Array of predictions to constrain
            prediction_type: Type of prediction ('visits', 'deliveries', 'quantity', 'revenue')
        
        Returns:
            constrained_predictions: Array of constrained predictions
        """
        predictions = np.array(predictions)
        
        if prediction_type == 'visits':
            # Constrain visit predictions
            predictions = np.clip(predictions, 
                                self.min_visits_per_day, 
                                self.max_visits_per_day)
                                
        elif prediction_type == 'quantity':
            # Constrain quantity predictions
            predictions = np.clip(predictions, 
                                self.min_quantity, 
                                self.max_quantity_per_client)
                                
        elif prediction_type == 'revenue':
            # Apply revenue constraints - ensure predictions meet minimum revenue
            predictions = np.maximum(predictions, self.min_revenue)
            print(f"💰 Revenue constraints applied: minimum {self.min_revenue}")
            
        elif prediction_type == 'deliveries':
            # Constrain delivery predictions (similar to visits but can be higher)
            predictions = np.clip(predictions, 0, self.max_visits_per_day * 1.5)
          # Round to reasonable precision
        predictions = np.round(predictions, 1)
        
        return predictions
    
    def validate_revenue_constraints(self, predicted_data, commercial_code):
        """
        Validate that revenue predictions meet minimum revenue requirements
        
        Args:
            predicted_data: Dictionary containing prediction results
            commercial_code: Commercial code for validation
          Returns:
            validation_results: Dictionary with validation status and recommendations
        """
        validation_results = {
            'meets_revenue_constraint': bool(True),
            'revenue_shortfall': float(0),
            'recommendations': [],
            'adjusted_predictions': predicted_data.copy()
        }
        
        if 'predictions' in predicted_data:
            # The predictions should already be revenue values
            daily_revenue = np.array(predicted_data['predictions'])
            
            # Check if any day falls below minimum revenue
            below_minimum_days = daily_revenue < self.min_revenue
            
            print(f"DEBUG Revenue Validation:")
            print(f"  Min revenue: {self.min_revenue}")
            print(f"  Daily revenue values: {daily_revenue}")
            print(f"  Below minimum days: {below_minimum_days}")
            print(f"  Any below minimum: {np.any(below_minimum_days)}")
            
            if np.any(below_minimum_days):
                validation_results['meets_revenue_constraint'] = bool(False)
                
                # Calculate shortfall
                shortfall_days = daily_revenue[below_minimum_days]
                total_shortfall = np.sum(self.min_revenue - shortfall_days)
                validation_results['revenue_shortfall'] = float(total_shortfall)
                
                # Generate recommendations
                validation_results['recommendations'].extend([
                    f"⚠️ {int(np.sum(below_minimum_days))} days fall below minimum revenue of {self.min_revenue}",
                    f"💰 Total revenue shortfall: {float(total_shortfall):.2f}",
                    "📈 Consider increasing visit frequency or targeting higher-value clients",
                    "🎯 Focus on premium products during visits"
                ])
                
                print(f"💰 Revenue validation for commercial {commercial_code}:")
                print(f"   Minimum revenue required: {self.min_revenue}")
                print(f"   Days below minimum: {int(np.sum(below_minimum_days))}")
                print(f"   Total shortfall: {float(total_shortfall):.2f}")
                
            else:
                # Revenue target is met - set shortfall to 0
                validation_results['revenue_shortfall'] = float(0)
                validation_results['recommendations'].append("✅ All predictions meet minimum revenue requirements")
                print(f"✅ Commercial {commercial_code} meets revenue constraints")
        
        return validation_results
    
    def calculate_prediction_quality_score(self, predictions, confidence_intervals):
        """
        Calculate a quality score for predictions based on various factors
        
        Args:
            predictions: Array of prediction values
            confidence_intervals: Dictionary with 'lower' and 'upper' bounds
        
        Returns:
            quality_score: Score from 0-100 indicating prediction quality
        """
        try:
            predictions = np.array(predictions)
            lower = np.array(confidence_intervals['lower'])
            upper = np.array(confidence_intervals['upper'])
            
            # Calculate various quality metrics
            
            # 1. Confidence interval width (narrower is better)
            ci_width = np.mean(upper - lower)
            relative_ci_width = ci_width / (np.mean(predictions) + 0.1)  # Add small constant to avoid division by zero
            ci_score = max(0, 100 - relative_ci_width * 50)  # Penalize wide intervals
            
            # 2. Prediction stability (less variance is better for business planning)
            prediction_variance = np.var(predictions)
            mean_prediction = np.mean(predictions)
            if mean_prediction > 0:
                cv = np.sqrt(prediction_variance) / mean_prediction  # Coefficient of variation
                stability_score = max(0, 100 - cv * 100)
            else:
                stability_score = 50  # Neutral score for zero predictions
            
            # 3. Realistic range check
            realistic_score = 100
            if np.any(predictions < 0):
                realistic_score -= 30  # Penalize negative predictions
            if np.any(predictions > 50):  # Unrealistically high for daily visits
                realistic_score -= 20
            
            # 4. Revenue constraint compliance
            revenue_score = 100
            if hasattr(self, 'min_revenue') and self.min_revenue > 0:
                estimated_revenue = predictions * 150  # Estimated revenue per visit
                if np.any(estimated_revenue < self.min_revenue):
                    revenue_score -= 25  # Penalize revenue constraint violations
            
            # Weighted average of all scores
            quality_score = (
                ci_score * 0.3 +
                stability_score * 0.25 +
                realistic_score * 0.25 +
                revenue_score * 0.2
            )
            
            return min(100, max(0, quality_score))
            
        except Exception as e:
            print(f"⚠️ Error calculating quality score: {e}")
            return 50  # Return neutral score on error
    
    def generate_revenue_based_recommendations(self, prediction_results, commercial_code):
        """
        Generate business recommendations based on revenue constraints and predictions
        
        Args:
            prediction_results: Dictionary containing prediction results
            commercial_code: Commercial code for personalized recommendations
        
        Returns:
            recommendations: List of actionable business recommendations
        """
        recommendations = []
        
        if 'predictions' in prediction_results:
            predictions = prediction_results['predictions']
            mean_prediction = np.mean(predictions)
            
            # Revenue-based recommendations
            if hasattr(self, 'min_revenue') and self.min_revenue > 0:
                estimated_daily_revenue = mean_prediction * 150  # Estimated revenue per visit
                
                if estimated_daily_revenue < self.min_revenue:
                    deficit = self.min_revenue - estimated_daily_revenue
                    additional_visits_needed = np.ceil(deficit / 150)
                    
                    recommendations.extend([
                        f"💰 Revenue Alert: Current predictions yield {estimated_daily_revenue:.2f}/day, need {self.min_revenue}",
                        f"📈 Recommend {additional_visits_needed} additional visits per day to meet revenue target",
                        "🎯 Focus on high-value clients and premium products",
                        "📞 Consider increasing visit frequency for top-performing clients"
                    ])
                else:
                    surplus = estimated_daily_revenue - self.min_revenue
                    recommendations.extend([
                        f"✅ Revenue target exceeded by {surplus:.2f}/day",
                        "💡 Consider optimizing route efficiency to maximize profit margin"
                    ])
            
            # General prediction-based recommendations
            if mean_prediction < 3:
                recommendations.append("📊 Low visit frequency predicted - consider market expansion")
            elif mean_prediction > 15:
                recommendations.append("⚡ High visit frequency predicted - ensure adequate resources")
            
            # Seasonal adjustments if available
            if hasattr(self, 'seasonal_enhancement_enabled') and self.seasonal_enhancement_enabled:
                recommendations.append("🌟 Seasonal patterns detected - recommendations adjusted accordingly")
        
        return recommendations

    def enhanced_revenue_prediction(self, historical_data, commercial_code, forecast_steps=30):
        """
        Enhanced prediction with specific focus on revenue constraints and validation
        
        Args:
            historical_data: DataFrame with historical sales/delivery data
            commercial_code: Commercial code for prediction
            forecast_steps: Number of days to forecast
        
        Returns:
            revenue_prediction_results: Dictionary with revenue-focused prediction results
        """
        try:
            print(f"\n💰 ENHANCED REVENUE PREDICTION")
            print(f"Commercial: {commercial_code}, Steps: {forecast_steps}")
            print(f"Minimum Revenue Constraint: {self.min_revenue}")
            print("-" * 50)
            
            # First, get standard predictions
            standard_prediction = self.enhanced_sarima_prediction(
                historical_data, forecast_steps
            )
            
            if not standard_prediction:
                print("❌ Unable to generate standard prediction")
                return None            # Get the prediction for the specific commercial (since enhanced_sarima_prediction returns a dict)
            print(f"Debug - Looking for commercial_code: {commercial_code} (type: {type(commercial_code)})")
            print(f"Debug - Available keys in standard_prediction: {list(standard_prediction.keys())}")
            print(f"Debug - Key types: {[type(k) for k in standard_prediction.keys()]}")
            
            # Normalize all keys and the lookup to strings for consistent comparison
            commercial_str = str(commercial_code)
            prediction_keys_map = {str(k): k for k in standard_prediction.keys()}
            
            if commercial_str in prediction_keys_map:
                specific_prediction = standard_prediction[prediction_keys_map[commercial_str]]
                print(f"✓ Found prediction using normalized key: {commercial_str}")
            else:
                # Take the first available prediction if commercial_code not found
                if standard_prediction:
                    specific_prediction = list(standard_prediction.values())[0]
                    print(f"⚠️ Commercial {commercial_code} not found, using first available: {list(standard_prediction.keys())[0]}")
                else:
                    print(f"❌ No predictions available")
                    return None
              # First, get the raw predictions
            predictions = np.array(specific_prediction['predictions'])
            estimated_revenue_per_visit = 150  # You can make this configurable
            
            # Apply minimum baseline for revenue calculation
            # If predictions are very low or zero, apply a minimum baseline
            min_visits_per_day = 1  # Minimum viable visits per day
            adjusted_predictions = np.maximum(predictions, min_visits_per_day)
            
            # Check if we applied baseline adjustments
            baseline_applied = np.any(predictions < min_visits_per_day)
            if baseline_applied:
                print(f"⚠️ Applied minimum baseline - Original avg: {np.mean(predictions):.2f}, Adjusted avg: {np.mean(adjusted_predictions):.2f}")
            
            daily_estimated_revenue = adjusted_predictions * estimated_revenue_per_visit
            
            # Create proper data structure for validation
            revenue_data_for_validation = {
                'predictions': daily_estimated_revenue,  # Use revenue values, not visit counts
                'dates': specific_prediction.get('dates', [])
            }
            
            # Validate against revenue constraints using actual revenue values
            validation_results = self.validate_revenue_constraints(
                revenue_data_for_validation, commercial_code
            )
            
            # Use the original predictions for visits, but update revenue constraint status
            predictions = np.array(specific_prediction['predictions'])
            
            # Generate revenue-focused recommendations
            recommendations = self.generate_revenue_based_recommendations(
                validation_results['adjusted_predictions'], commercial_code            )
              # Convert dates to serializable format
            serializable_dates = []
            if hasattr(specific_prediction['dates'], 'strftime'):
                # If it's a DatetimeIndex or similar
                serializable_dates = [date.strftime('%Y-%m-%d') for date in specific_prediction['dates']]
            elif isinstance(specific_prediction['dates'], list):
                # If it's already a list
                serializable_dates = [str(date) for date in specific_prediction['dates']]
            else:
                # Fallback for other types
                serializable_dates = [str(date) for date in specific_prediction['dates']]
              # Compile revenue prediction results
            revenue_prediction_results = {
                'commercial_code': commercial_code,
                'prediction_type': 'revenue_optimized',
                'forecast_steps': forecast_steps,
                'dates': serializable_dates,
                'visit_predictions': predictions.tolist() if hasattr(predictions, 'tolist') else list(predictions),
                'estimated_daily_revenue': daily_estimated_revenue.tolist() if hasattr(daily_estimated_revenue, 'tolist') else list(daily_estimated_revenue),
                'total_estimated_revenue': float(np.sum(daily_estimated_revenue)),
                'average_daily_revenue': float(np.mean(daily_estimated_revenue)),
                'min_revenue_constraint': self.min_revenue,
                'meets_revenue_constraint': bool(validation_results['meets_revenue_constraint']),
                'revenue_shortfall': float(validation_results['revenue_shortfall']),
                'quality_score': float(specific_prediction.get('quality_score', 0)),
                'recommendations': recommendations,
                'confidence_intervals': {
                    'visits_lower': specific_prediction['lower_ci'].tolist() if hasattr(specific_prediction['lower_ci'], 'tolist') else list(specific_prediction['lower_ci']),
                    'visits_upper': specific_prediction['upper_ci'].tolist() if hasattr(specific_prediction['upper_ci'], 'tolist') else list(specific_prediction['upper_ci']),
                    'revenue_lower': (specific_prediction['lower_ci'] * estimated_revenue_per_visit).tolist() if hasattr(specific_prediction['lower_ci'], 'tolist') else list(specific_prediction['lower_ci'] * estimated_revenue_per_visit),
                    'revenue_upper': (specific_prediction['upper_ci'] * estimated_revenue_per_visit).tolist() if hasattr(specific_prediction['upper_ci'], 'tolist') else list(specific_prediction['upper_ci'] * estimated_revenue_per_visit)
                },                'enhancement_applied': bool(True),
                'revenue_constraints_applied': bool(True)
            }
            
            # Print summary
            print(f"\n📊 REVENUE PREDICTION SUMMARY:")
            print(f"   Average daily visits: {np.mean(predictions):.1f}")
            print(f"   Average daily revenue: {np.mean(daily_estimated_revenue):.2f}")
            print(f"   Total forecast revenue: {np.sum(daily_estimated_revenue):.2f}")
            print(f"   Revenue constraint status: {'✅ Met' if validation_results['meets_revenue_constraint'] else '❌ Not Met'}")
            
            if not validation_results['meets_revenue_constraint']:
                print(f"   Revenue shortfall: {validation_results['revenue_shortfall']:.2f}")
            
            print(f"\n💡 RECOMMENDATIONS ({len(recommendations)}):")
            for i, rec in enumerate(recommendations[:5], 1):  # Show first 5 recommendations
                print(f"   {i}. {rec}")
            
            return revenue_prediction_results
            
        except Exception as e:
            print(f"❌ Error in enhanced revenue prediction: {e}")
            return None
        
    def enhanced_sarima_prediction(self, historical_data, days_to_predict=30):
        """Enhanced SARIMA prediction with validation and constraints"""
        
        try:
            # Use the existing predict_future_visits_sarima function
            raw_predictions = predict_future_visits_sarima(historical_data, days_to_predict)
            
            # Apply constraints and improvements
            enhanced_predictions = {}
            
            for commercial, pred in raw_predictions.items():
                # Apply business constraints to predictions
                constrained_preds = self.apply_business_constraints(
                    pred['predictions'], 'visits'
                )
                
                # Apply constraints to confidence intervals
                constrained_lower = self.apply_business_constraints(
                    pred['lower_ci'], 'visits'
                )
                constrained_upper = self.apply_business_constraints(
                    pred['upper_ci'], 'visits'
                )
                
                # Ensure confidence intervals make sense
                constrained_lower = np.minimum(constrained_lower, constrained_preds - 0.5)
                constrained_upper = np.maximum(constrained_upper, constrained_preds + 0.5)
                
                # Recalculate statistics
                enhanced_stats = {
                    'moyenne_visites_predites': float(np.mean(constrained_preds)),
                    'max_visites_predites': float(np.max(constrained_preds)),
                    'min_visites_predites': float(np.min(constrained_preds)),
                    'total_visites_predites': float(np.sum(constrained_preds)),
                    'aic': pred['stats'].get('aic', 0),
                    'bic': pred['stats'].get('bic', 0),
                    'confidence_quality': 'High' if np.mean(constrained_upper - constrained_lower) < 2 else 'Medium'
                }
                
                enhanced_predictions[commercial] = {
                    'dates': pred['dates'],
                    'predictions': constrained_preds,
                    'lower_ci': constrained_lower,
                    'upper_ci': constrained_upper,
                    'stats': enhanced_stats,
                    'enhancement_applied': True
                }
            
            return enhanced_predictions
            
        except Exception as e:
            print(f"Error in enhanced SARIMA prediction: {e}")
            return {}

    def setup_revenue_constraints_interactive(self):
        """
        Interactive setup for revenue constraints and minimum revenue parameters
        """
        print("\n🛠️ INTERACTIVE REVENUE CONSTRAINTS SETUP")
        print("=" * 50)
        
        try:
            # Get minimum revenue from user
            while True:
                try:
                    min_rev_input = input(f"\n💰 Enter minimum daily revenue target (current: {self.min_revenue}): ")
                    if min_rev_input.strip() == "":
                        break  # Keep current value
                    
                    min_revenue = float(min_rev_input)
                    if min_revenue >= 0:
                        self.min_revenue = min_revenue
                        print(f"✅ Minimum revenue set to: {self.min_revenue}")
                        break
                    else:
                        print("❌ Please enter a positive number.")
                except ValueError:
                    print("❌ Please enter a valid number.")
            
            # Setup revenue per visit estimation
            while True:
                try:
                    rev_per_visit = input(f"\n💵 Enter estimated revenue per visit (default: 150): ")
                    if rev_per_visit.strip() == "":
                        self.revenue_per_visit = 150
                        break
                    
                    revenue = float(rev_per_visit)
                    if revenue > 0:
                        self.revenue_per_visit = revenue
                        print(f"✅ Revenue per visit set to: {self.revenue_per_visit}")
                        break
                    else:
                        print("❌ Please enter a positive number.")
                except ValueError:
                    print("❌ Please enter a valid number.")
            
            # Setup visit constraints
            while True:
                try:
                    max_visits = input(f"\n📈 Enter maximum visits per day (current: {self.max_visits_per_day}): ")
                    if max_visits.strip() == "":
                        break  # Keep current value
                    
                    max_v = int(max_visits)
                    if max_v > 0:
                        self.max_visits_per_day = max_v
                        print(f"✅ Maximum visits per day set to: {self.max_visits_per_day}")
                        break
                    else:
                        print("❌ Please enter a positive number.")
                except ValueError:
                    print("❌ Please enter a valid integer.")
            
            print(f"\n✅ SETUP COMPLETE!")
            print(f"📊 Configuration Summary:")
            print(f"   💰 Minimum daily revenue: {self.min_revenue}")
            print(f"   💵 Revenue per visit: {getattr(self, 'revenue_per_visit', 150)}")
            print(f"   📈 Maximum visits per day: {self.max_visits_per_day}")
            
            return True
            
        except KeyboardInterrupt:
            print(f"\n⚠️ Setup cancelled by user.")
            return False
        except Exception as e:
            print(f"\n❌ Error during setup: {e}")
            return False

    def demo_revenue_constraints(self, historical_data=None):
        """
        Demonstrate the revenue constraints functionality with sample data
        """
        print("\n🎯 REVENUE CONSTRAINTS DEMONSTRATION")
        print("=" * 60)
        
        if historical_data is None:
            # Create sample data for demonstration
            print("📊 Creating sample data for demonstration...")
            dates = pd.date_range('2024-01-01', periods=30)
            historical_data = pd.DataFrame({
                'date': dates,
                'commercial_code': ['DEMO_COMMERCIAL'] * 30,
                'nombre_visites': np.random.poisson(7, 30),  # Average 7 visits per day
                'revenue': np.random.normal(1200, 300, 30)  # Average 1200 revenue with variation
            })
            # Ensure some days fall below minimum to show constraints
            historical_data.loc[0:4, 'nombre_visites'] = [3, 4, 2, 5, 3]  # Low visit days
            print(f"✅ Sample data created with {len(historical_data)} days")
        
        # Run enhanced revenue prediction
        print(f"\n🔍 Running enhanced revenue prediction with minimum revenue: {self.min_revenue}")
        result = self.enhanced_revenue_prediction(historical_data, 'DEMO_COMMERCIAL', 30)
        
        if result:
            print(f"\n📈 DEMONSTRATION RESULTS:")
            print(f"   🎯 Revenue target: {'✅ Met' if result['meets_revenue_constraint'] else '❌ Not Met'}")
            print(f"   💰 Average daily revenue: {result['average_daily_revenue']:.2f}")
            print(f"   📊 Total forecast revenue: {result['total_estimated_revenue']:.2f}")
            
            if result['revenue_shortfall'] > 0:
                print(f"   ⚠️ Revenue shortfall: {result['revenue_shortfall']:.2f}")
            
            print(f"\n💡 Key Recommendations:")
            for i, rec in enumerate(result['recommendations'][:3], 1):
                print(f"   {i}. {rec}")
        else:        print("❌ Demo failed to generate results")
        
        return result

# ===================== DUAL DELIVERY OPTIMIZATION - 365 DAYS WITH DATE SELECTION =====================

def dual_delivery_optimization_365_days(commercial_code, selected_date=None, include_revenue_optimization=True, save_results=True):
    """
    Dual delivery optimization system with date selection functionality.
    Uses data from the last 365 days before the selected date for training,
    then predicts the next 365 days after the selected date.
    
    Args:
        commercial_code: Code du commercial à analyser
        selected_date: Date de référence (format YYYY-MM-DD or datetime). If None, uses today
        include_revenue_optimization: Whether to include revenue optimization
        save_results: Whether to save results to CSV and generate visualizations
    
    Returns:
        optimization_results: Comprehensive optimization plan for 365 days
    """
    import logging
    from datetime import datetime, timedelta
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('dual_optimization_365')
    
    # Handle date selection
    if selected_date is None:
        selected_date = datetime.now()
    elif isinstance(selected_date, str):
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d')
    
    # Calculate training and prediction periods
    training_start = selected_date - timedelta(days=365)  # Last 365 days for training
    training_end = selected_date
    prediction_start = selected_date
    prediction_end = selected_date + timedelta(days=365)  # Next 365 days for prediction
    
    print(f"\n🚀 DUAL DELIVERY OPTIMIZATION - 365 DAYS WITH DATE SELECTION")
    print(f"🎯 Commercial: {commercial_code}")
    print(f"📅 Selected Date: {selected_date.strftime('%Y-%m-%d')}")
    print(f"📊 Training Period: {training_start.strftime('%Y-%m-%d')} to {training_end.strftime('%Y-%m-%d')} (365 days)")
    print(f"� Prediction Period: {prediction_start.strftime('%Y-%m-%d')} to {prediction_end.strftime('%Y-%m-%d')} (365 days)")
    print("=" * 90)
    
    try:
        # Initialize Enhanced Prediction System with revenue constraints
        logger.info("Initializing Enhanced Prediction System...")
        enhanced_predictor = EnhancedPredictionSystem(min_revenue=150)  # 150 TND minimum daily revenue
        
        # Get historical data using the training period (last 365 days before selected date)
        logger.info(f"Retrieving training data from {training_start.strftime('%Y-%m-%d')} to {training_end.strftime('%Y-%m-%d')}...")
        
        # Use a wider range for better pattern analysis (add extra 365 days for seasonal analysis)
        extended_start = training_start - timedelta(days=365)
        date_debut = extended_start.strftime('%Y-%m-%d')
        date_fin = training_end.strftime('%Y-%m-%d')
        
        historical_data = get_historical_deliveries(date_debut, date_fin)
        
        if historical_data.empty:
            logger.error("No historical data found")
            print("❌ No historical data available for the training period")
            return None
        
        # Filter for the specific commercial
        commercial_data = historical_data[historical_data['commercial_code'] == commercial_code]
        
        if commercial_data.empty:
            logger.warning(f"No data found for commercial {commercial_code}")
            print(f"⚠️ No historical data found for commercial {commercial_code}")
            
            # List available commercials
            available_commercials = historical_data['commercial_code'].unique()[:10]
            print(f"📋 Available commercials: {', '.join(map(str, available_commercials))}")
            
            # Use the first available commercial as fallback
            if len(available_commercials) > 0:
                commercial_code = available_commercials[0]
                commercial_data = historical_data[historical_data['commercial_code'] == commercial_code]
                print(f"🔄 Using commercial {commercial_code} as fallback")
                logger.info(f"Using fallback commercial: {commercial_code}")
            else:
                return None
        
        # Focus on the main training period (last 365 days before selected date)
        training_data = commercial_data[
            (commercial_data['date'] >= training_start) & 
            (commercial_data['date'] < training_end)
        ]
        
        logger.info(f"Training data: {len(training_data)} records for commercial {commercial_code}")
        logger.info(f"Extended data for patterns: {len(commercial_data)} records from {commercial_data['date'].min()} to {commercial_data['date'].max()}")
        print(f"📊 Training data: {len(training_data)} records from {training_start.strftime('%Y-%m-%d')} to {training_end.strftime('%Y-%m-%d')}")
        print(f"📈 Extended data for pattern analysis: {len(commercial_data)} records")
        
        # Analyze seasonal patterns using all available data
        logger.info("Analyzing seasonal patterns...")
        if hasattr(enhanced_predictor, 'analyze_seasonal_patterns'):
            seasonal_report = enhanced_predictor.analyze_seasonal_patterns(historical_data)
            print(f"🌟 Seasonal patterns analyzed for enhanced predictions")
        
        # ======== PART 1: VISIT PREDICTIONS (365 days) ========
        logger.info("Generating visit predictions for 365 days...")
        
        # Prepare visits data for SARIMA using training data
        visit_time_series = prepare_data_for_sarima(
            training_data,  # Use focused training data (last 365 days before selected date)
            commercial_code, 
            metric='nb_clients_visites', 
            freq='D'  # Daily frequency for detailed 365-day view
        )
        
        if len(visit_time_series) < 14:  # Need at least 2 weeks of data
            logger.warning("Insufficient daily data, using extended dataset with weekly aggregation")
            visit_time_series = prepare_data_for_sarima(
                commercial_data,  # Use extended dataset for better patterns
                commercial_code, 
                metric='nb_clients_visites', 
                freq='W'
            )
            if len(visit_time_series) < 10:
                logger.error("Insufficient data for predictions")
                print("❌ Insufficient historical data for reliable predictions")
                return None
        
        # Identify optimal SARIMA parameters for visits
        visit_params = identify_sarima_parameters(
            visit_time_series,
            seasonal_period=7 if visit_time_series.index.freq == 'D' else 52,
            business_constraints={
                'min_forecast_accuracy': 0.70,
                'max_computation_time': 120,
                'prefer_simpler_models': True,
                'seasonal_importance': 0.8
            }
        )
        
        # Generate visit predictions
        visit_forecast, visit_model, visit_metrics = fit_sarima_and_predict(
            visit_time_series,
            visit_params,
            forecast_steps=365 if visit_time_series.index.freq == 'D' else 52,  # 365 days or 52 weeks
            prediction_type='visits',
            enhanced_predictor=enhanced_predictor
        )
        
        logger.info(f"Visit predictions generated: {len(visit_forecast)} periods")
        print(f"✅ Visit predictions: {len(visit_forecast)} periods with quality score {visit_metrics.get('prediction_quality_score', 0):.1f}/100")
        
        # ======== PART 2: REVENUE OPTIMIZATION ========
        revenue_results = None
        
        if include_revenue_optimization:
            logger.info("Generating revenue optimization for 365 days...")
            
            # Prepare revenue data for SARIMA using training data
            revenue_time_series = prepare_data_for_sarima(
                training_data,  # Use focused training data
                commercial_code,
                metric='valeur_totale',
                freq='D' if len(training_data) > 50 else 'W'
            )
            
            # If insufficient training data, use extended dataset
            if len(revenue_time_series) < 10:
                revenue_time_series = prepare_data_for_sarima(
                    commercial_data,  # Use extended dataset
                    commercial_code,
                    metric='valeur_totale',
                    freq='D' if len(commercial_data) > 100 else 'W'
                )
            
            if len(revenue_time_series) >= 10:
                # Identify optimal SARIMA parameters for revenue
                revenue_params = identify_sarima_parameters(
                    revenue_time_series,
                    seasonal_period=7 if revenue_time_series.index.freq == 'D' else 52,
                    business_constraints={
                        'min_forecast_accuracy': 0.75,
                        'max_computation_time': 120,
                        'prefer_simpler_models': True,
                        'seasonal_importance': 0.9
                    },
                    revenue_weight=0.4
                )
                
                # Generate revenue predictions
                revenue_forecast, revenue_model, revenue_metrics = fit_sarima_and_predict(
                    revenue_time_series,
                    revenue_params,
                    forecast_steps=365 if revenue_time_series.index.freq == 'D' else 52,
                    prediction_type='revenue',
                    enhanced_predictor=enhanced_predictor
                )
                
                logger.info(f"Revenue predictions generated: {len(revenue_forecast)} periods")
                print(f"✅ Revenue predictions: {len(revenue_forecast)} periods")
                
                # Enhanced revenue prediction with constraints
                revenue_results = enhanced_predictor.enhanced_revenue_prediction(
                    historical_data, commercial_code, forecast_steps=365
                )
            else:
                logger.warning("Insufficient data for revenue predictions")
                print("⚠️ Insufficient data for revenue predictions, using visit-based estimation")
        
        # ======== PART 3: CREATE COMPREHENSIVE 365-DAY PLAN ========
        logger.info("Creating comprehensive 365-day optimization plan...")
        
        # Generate future dates starting from the selected date (prediction period)
        future_dates = pd.date_range(start=prediction_start, periods=365, freq='D')
        
        # Create the comprehensive optimization plan
        optimization_plan = pd.DataFrame({
            'date': future_dates,
            'commercial_code': commercial_code,
            'day_of_week': future_dates.day_name(),
            'month': future_dates.month_name(),
            'quarter': future_dates.quarter,
            'day_of_year': future_dates.dayofyear
        })
        
        # Add visit predictions (map from forecast periods to daily)
        if visit_time_series.index.freq == 'D':
            # Direct daily mapping
            optimization_plan['predicted_visits'] = visit_forecast.values[:365]
            optimization_plan['visits_lower_ci'] = visit_metrics['forecast_lower'].values[:365]
            optimization_plan['visits_upper_ci'] = visit_metrics['forecast_upper'].values[:365]
        else:
            # Weekly to daily mapping - distribute weekly visits across 7 days
            daily_visits = []
            daily_lower = []
            daily_upper = []
            
            for i in range(365):
                week_index = min(i // 7, len(visit_forecast) - 1)
                # Distribute weekly visits with some variation
                base_daily = visit_forecast.iloc[week_index] / 7
                # Add day-of-week variation (weekdays typically have more visits)
                day_of_week = future_dates[i].weekday()  # 0=Monday, 6=Sunday
                if day_of_week < 5:  # Weekdays
                    daily_multiplier = 1.2
                else:  # Weekends
                    daily_multiplier = 0.6
                
                daily_visits.append(max(0, base_daily * daily_multiplier))
                daily_lower.append(max(0, visit_metrics['forecast_lower'].iloc[week_index] / 7 * daily_multiplier))
                daily_upper.append(visit_metrics['forecast_upper'].iloc[week_index] / 7 * daily_multiplier)
            
            optimization_plan['predicted_visits'] = daily_visits
            optimization_plan['visits_lower_ci'] = daily_lower
            optimization_plan['visits_upper_ci'] = daily_upper
        
        # Add revenue estimates
        if revenue_results:
            # Use enhanced revenue predictions
            optimization_plan['predicted_revenue'] = revenue_results['estimated_daily_revenue'][:365]
            optimization_plan['revenue_lower_ci'] = revenue_results['confidence_intervals']['revenue_lower'][:365]
            optimization_plan['revenue_upper_ci'] = revenue_results['confidence_intervals']['revenue_upper'][:365]
        else:
            # Estimate revenue from visits
            revenue_per_visit = 150  # Default estimate
            optimization_plan['predicted_revenue'] = optimization_plan['predicted_visits'] * revenue_per_visit
            optimization_plan['revenue_lower_ci'] = optimization_plan['visits_lower_ci'] * revenue_per_visit
            optimization_plan['revenue_upper_ci'] = optimization_plan['visits_upper_ci'] * revenue_per_visit
        
        # Add business recommendations
        optimization_plan['confidence_level'] = optimization_plan.apply(
            lambda row: 'High' if (row['visits_upper_ci'] - row['visits_lower_ci']) < 2 
            else 'Medium' if (row['visits_upper_ci'] - row['visits_lower_ci']) < 4 
            else 'Low', axis=1
        )
        
        optimization_plan['resource_recommendation'] = optimization_plan['predicted_visits'].apply(
            lambda visits: 'High Priority - Extra Resources' if visits > 12
            else 'Medium Priority - Standard Resources' if visits > 6
            else 'Low Priority - Minimal Resources' if visits > 2
            else 'Consider Alternative Strategies'
        )
        
        optimization_plan['revenue_status'] = optimization_plan['predicted_revenue'].apply(
            lambda revenue: '✅ Target Met' if revenue >= 150
            else '⚠️ Below Target' if revenue >= 100
            else '❌ Critical - Action Required'
        )
        
        # Add seasonal insights
        optimization_plan['season'] = optimization_plan['month'].map({
            'January': 'Winter', 'February': 'Winter', 'March': 'Spring',
            'April': 'Spring', 'May': 'Spring', 'June': 'Summer',
            'July': 'Summer', 'August': 'Summer', 'September': 'Fall',
            'October': 'Fall', 'November': 'Fall', 'December': 'Winter'
        })
        
        # Calculate summary statistics
        total_predicted_visits = optimization_plan['predicted_visits'].sum()
        total_predicted_revenue = optimization_plan['predicted_revenue'].sum()
        avg_daily_visits = optimization_plan['predicted_visits'].mean()
        avg_daily_revenue = optimization_plan['predicted_revenue'].mean()
        
        # Identify peak and low periods
        optimization_plan['period_type'] = 'Normal'
        high_threshold = optimization_plan['predicted_visits'].quantile(0.8)
        low_threshold = optimization_plan['predicted_visits'].quantile(0.2)
        
        optimization_plan.loc[optimization_plan['predicted_visits'] >= high_threshold, 'period_type'] = 'Peak'
        optimization_plan.loc[optimization_plan['predicted_visits'] <= low_threshold, 'period_type'] = 'Low'
        
        # ======== PART 4: GENERATE INSIGHTS AND REPORTS ========
        logger.info("Generating insights and recommendations...")
        
        # Monthly summary
        monthly_summary = optimization_plan.groupby('month').agg({
            'predicted_visits': ['sum', 'mean'],
            'predicted_revenue': ['sum', 'mean']
        }).round(2)
        
        # Weekly patterns
        weekly_patterns = optimization_plan.groupby('day_of_week').agg({
            'predicted_visits': 'mean',
            'predicted_revenue': 'mean'
        }).round(2)
        
        # Quarterly breakdown
        quarterly_summary = optimization_plan.groupby('quarter').agg({
            'predicted_visits': ['sum', 'mean'],
            'predicted_revenue': ['sum', 'mean']
        }).round(2)
        
        # Peak periods analysis
        peak_periods = optimization_plan[optimization_plan['period_type'] == 'Peak']
        low_periods = optimization_plan[optimization_plan['period_type'] == 'Low']
        
        # Create comprehensive results
        optimization_results = {
            'commercial_code': commercial_code,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'forecast_period': f'365 days from {selected_date.strftime("%Y-%m-%d")}',
            'start_date': prediction_start.strftime('%Y-%m-%d'),
            'end_date': prediction_end.strftime('%Y-%m-%d'),
            
            # Daily plan
            'daily_plan': optimization_plan,
            
            # Summary statistics
            'summary': {
                'total_predicted_visits': int(total_predicted_visits),
                'total_predicted_revenue': float(total_predicted_revenue),
                'avg_daily_visits': float(avg_daily_visits),
                'avg_daily_revenue': float(avg_daily_revenue),
                'peak_days': len(peak_periods),
                'low_activity_days': len(low_periods),
                'revenue_target_met_days': len(optimization_plan[optimization_plan['predicted_revenue'] >= 150])
            },
            
            # Periodic summaries
            'monthly_summary': monthly_summary,
            'weekly_patterns': weekly_patterns,
            'quarterly_summary': quarterly_summary,
            
            # Key insights
            'insights': {
                'best_month': monthly_summary[('predicted_visits', 'sum')].idxmax(),
                'worst_month': monthly_summary[('predicted_visits', 'sum')].idxmin(),
                'best_day_of_week': weekly_patterns['predicted_visits'].idxmax(),
                'worst_day_of_week': weekly_patterns['predicted_visits'].idxmin(),
                'peak_periods': peak_periods[['date', 'predicted_visits', 'predicted_revenue']].to_dict('records')[:10],
                'low_periods': low_periods[['date', 'predicted_visits', 'predicted_revenue']].to_dict('records')[:10]
            },
            
            # Model performance
            'model_performance': {
                'visits_model_quality': float(visit_metrics.get('prediction_quality_score', 0)),
                'revenue_optimization_applied': revenue_results is not None,
                'seasonal_adjustments_applied': hasattr(enhanced_predictor, 'seasonal_enhancement_enabled') and enhanced_predictor.seasonal_enhancement_enabled
            }
        }
        
        # ======== PART 5: SAVE RESULTS AND GENERATE VISUALIZATIONS ========
        if save_results:
            logger.info("Saving results and generating visualizations...")
            
            # Save detailed daily plan
            csv_filename = f'dual_optimization_365_days_{commercial_code}_{selected_date.strftime("%Y%m%d")}.csv'
            optimization_plan.to_csv(csv_filename, index=False)
            print(f"📁 Detailed plan saved: {csv_filename}")
            
            # Save summary report
            summary_filename = f'optimization_summary_{commercial_code}_{selected_date.strftime("%Y%m%d")}.txt'
            with open(summary_filename, 'w', encoding='utf-8') as f:
                f.write(f"DUAL DELIVERY OPTIMIZATION REPORT - 365 DAYS\n")
                f.write(f"=" * 60 + "\n\n")
                f.write(f"Commercial: {commercial_code}\n")
                f.write(f"Analysis Date: {optimization_results['analysis_date']}\n")
                f.write(f"Forecast Period: {optimization_results['start_date']} to {optimization_results['end_date']}\n\n")
                
                f.write(f"SUMMARY STATISTICS:\n")
                f.write(f"Total Predicted Visits: {optimization_results['summary']['total_predicted_visits']:,}\n")
                f.write(f"Total Predicted Revenue: {optimization_results['summary']['total_predicted_revenue']:,.2f} TND\n")
                f.write(f"Average Daily Visits: {optimization_results['summary']['avg_daily_visits']:.1f}\n")
                f.write(f"Average Daily Revenue: {optimization_results['summary']['avg_daily_revenue']:.2f} TND\n")
                f.write(f"Peak Activity Days: {optimization_results['summary']['peak_days']}\n")
                f.write(f"Low Activity Days: {optimization_results['summary']['low_activity_days']}\n")
                f.write(f"Days Meeting Revenue Target: {optimization_results['summary']['revenue_target_met_days']}\n\n")
                
                f.write(f"KEY INSIGHTS:\n")
                f.write(f"Best Month: {optimization_results['insights']['best_month']}\n")
                f.write(f"Worst Month: {optimization_results['insights']['worst_month']}\n")
                f.write(f"Best Day of Week: {optimization_results['insights']['best_day_of_week']}\n")
                f.write(f"Worst Day of Week: {optimization_results['insights']['worst_day_of_week']}\n")
            
            print(f"📊 Summary report saved: {summary_filename}")
            
            # Generate visualization
            try:
                plt.figure(figsize=(20, 15))
                
                # Plot 1: Daily visits over 365 days
                plt.subplot(3, 2, 1)
                plt.plot(optimization_plan['date'], optimization_plan['predicted_visits'], 
                        color='blue', linewidth=1, alpha=0.8)
                plt.fill_between(optimization_plan['date'], 
                               optimization_plan['visits_lower_ci'], 
                               optimization_plan['visits_upper_ci'], 
                               alpha=0.2, color='blue')
                plt.title(f'Daily Visits Prediction - 365 Days\nCommercial {commercial_code}')
                plt.ylabel('Predicted Visits')
                plt.xticks(rotation=45)
                plt.grid(True, alpha=0.3)
                
                # Plot 2: Daily revenue over 365 days
                plt.subplot(3, 2, 2)
                plt.plot(optimization_plan['date'], optimization_plan['predicted_revenue'], 
                        color='green', linewidth=1, alpha=0.8)
                plt.fill_between(optimization_plan['date'], 
                               optimization_plan['revenue_lower_ci'], 
                               optimization_plan['revenue_upper_ci'], 
                               alpha=0.2, color='green')
                plt.axhline(y=150, color='red', linestyle='--', label='Revenue Target (150 TND)')
                plt.title('Daily Revenue Prediction - 365 Days')
                plt.ylabel('Predicted Revenue (TND)')
                plt.xticks(rotation=45)
                plt.legend()
                plt.grid(True, alpha=0.3)
                
                # Plot 3: Monthly aggregation
                plt.subplot(3, 2, 3)
                monthly_data = optimization_plan.groupby('month').agg({
                    'predicted_visits': 'sum',
                    'predicted_revenue': 'sum'
                })
                month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                              'July', 'August', 'September', 'October', 'November', 'December']
                monthly_data = monthly_data.reindex(month_order)
                
                bars = plt.bar(monthly_data.index, monthly_data['predicted_visits'], color='skyblue', alpha=0.7)
                plt.title('Monthly Total Visits')
                plt.ylabel('Total Visits')
                plt.xticks(rotation=45)
                plt.grid(True, alpha=0.3)
                
                # Plot 4: Weekly patterns
                plt.subplot(3, 2, 4)
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                weekly_data = optimization_plan.groupby('day_of_week')['predicted_visits'].mean().reindex(day_order)
                
                bars = plt.bar(weekly_data.index, weekly_data.values, color='orange', alpha=0.7)
                plt.title('Average Visits by Day of Week')
                plt.ylabel('Average Visits')
                plt.xticks(rotation=45)
                plt.grid(True, alpha=0.3)
                
                # Plot 5: Quarterly comparison
                plt.subplot(3, 2, 5)
                quarterly_data = optimization_plan.groupby('quarter').agg({
                    'predicted_visits': 'sum',
                    'predicted_revenue': 'sum'
                })
                
                x = range(len(quarterly_data))
                width = 0.35
                
                plt.bar([i - width/2 for i in x], quarterly_data['predicted_visits'], 
                       width, label='Visits', color='lightcoral', alpha=0.7)
                plt.bar([i + width/2 for i in x], quarterly_data['predicted_revenue']/10, 
                       width, label='Revenue (x10)', color='lightgreen', alpha=0.7)
                
                plt.title('Quarterly Comparison')
                plt.xlabel('Quarter')
                plt.ylabel('Total Count')
                plt.xticks(x, [f'Q{i}' for i in quarterly_data.index])
                plt.legend()
                plt.grid(True, alpha=0.3)
                
                # Plot 6: Confidence levels distribution
                plt.subplot(3, 2, 6)
                confidence_counts = optimization_plan['confidence_level'].value_counts()
                plt.pie(confidence_counts.values, labels=confidence_counts.index, autopct='%1.1f%%',
                       colors=['lightgreen', 'yellow', 'lightcoral'])
                plt.title('Prediction Confidence Distribution')
                
                plt.tight_layout()
                
                # Save the visualization
                plot_filename = f'dual_optimization_365_visualization_{commercial_code}_{selected_date.strftime("%Y%m%d")}.png'
                plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
                plt.close()
                
                print(f"📈 Visualization saved: {plot_filename}")
                
            except Exception as plot_error:
                logger.warning(f"Visualization generation failed: {plot_error}")
                print(f"⚠️ Could not generate visualization: {plot_error}")
        
        # ======== FINAL SUMMARY ========
        logger.info("Dual optimization analysis completed successfully")
        
        print(f"\n🎉 DUAL DELIVERY OPTIMIZATION COMPLETED!")
        print(f"📅 Period: {optimization_results['start_date']} to {optimization_results['end_date']}")
        print(f"🎯 Commercial: {commercial_code}")
        print(f"\n📊 KEY RESULTS:")
        print(f"   📈 Total Visits (365 days): {optimization_results['summary']['total_predicted_visits']:,}")
        print(f"   💰 Total Revenue (365 days): {optimization_results['summary']['total_predicted_revenue']:,.2f} TND")
        print(f"   📅 Daily Average Visits: {optimization_results['summary']['avg_daily_visits']:.1f}")
        print(f"   💵 Daily Average Revenue: {optimization_results['summary']['avg_daily_revenue']:.2f} TND")
        print(f"   🏆 Best Month: {optimization_results['insights']['best_month']}")
        print(f"   📉 Worst Month: {optimization_results['insights']['worst_month']}")
        print(f"   ⭐ Best Day: {optimization_results['insights']['best_day_of_week']}")
        print(f"   📊 Model Quality: {optimization_results['model_performance']['visits_model_quality']:.1f}/100")
        
        if optimization_results['summary']['revenue_target_met_days'] < 300:
            print(f"\n⚠️ ALERT: Only {optimization_results['summary']['revenue_target_met_days']}/365 days meet revenue target")
            print(f"💡 Consider strategies to improve daily revenue performance")
        else:
            print(f"\n✅ EXCELLENT: {optimization_results['summary']['revenue_target_met_days']}/365 days meet revenue target")
        
        # Save results to JSON if requested
        if save_results:
            json_saved = save_dual_optimization_to_json(optimization_results, commercial_code)
            if json_saved:
                print(f"💾 Results exported to JSON successfully")
        
        return optimization_results
        
    except Exception as e:
        logger.error(f"Error in dual delivery optimization: {str(e)}")
        print(f"❌ Error in dual delivery optimization: {str(e)}")
        return None

# ===================== UTILITY FUNCTIONS FOR 365-DAY OPTIMIZATION =====================

def get_commercial_list(reference_date=None):
    """
    Get list of available commercials from the database
    
    Args:
        reference_date: Optional reference date to filter commercials that have data 
                       in the training period (365 days before this date)
    
    Returns:
        List of commercial codes with basic statistics
    """
    try:
        conn = get_db_connection()
        
        if reference_date:
            # If reference date provided, filter for commercials with data in training period
            if isinstance(reference_date, str):
                reference_date = datetime.strptime(reference_date, '%Y-%m-%d')
            
            training_start = reference_date - timedelta(days=365)
            training_end = reference_date
            
            query = """
            SELECT 
                commercial_code,
                COUNT(*) as total_records,
                COUNT(DISTINCT client_code) as unique_clients,
                MIN(date) as first_record,
                MAX(date) as last_record,
                AVG(net_a_payer) as avg_transaction_value,
                COUNT(CASE WHEN date BETWEEN %s AND %s THEN 1 END) as training_period_records
            FROM entetecommercials 
            GROUP BY commercial_code 
            HAVING COUNT(CASE WHEN date BETWEEN %s AND %s THEN 1 END) >= 30  -- At least 30 records in training period
            ORDER BY training_period_records DESC, total_records DESC
            """
            
            df = pd.read_sql(query, conn, params=(
                training_start.strftime('%Y-%m-%d'),
                training_end.strftime('%Y-%m-%d'),
                training_start.strftime('%Y-%m-%d'),
                training_end.strftime('%Y-%m-%d')
            ))
        else:
            # Original query for all-time data
            query = """
            SELECT 
                commercial_code,
                COUNT(*) as total_records,
                COUNT(DISTINCT client_code) as unique_clients,
                MIN(date) as first_record,
                MAX(date) as last_record,
                AVG(net_a_payer) as avg_transaction_value
            FROM entetecommercials 
            GROUP BY commercial_code 
            HAVING COUNT(*) >= 30  -- Only commercials with substantial data
            ORDER BY total_records DESC
            """
            
            df = pd.read_sql(query, conn)
        
        conn.dispose()
        
        return df.to_dict('records')
        
    except Exception as e:
        print(f"Error retrieving commercial list: {e}")
        return []

def run_interactive_365_optimization():
    """
    Interactive function to run 365-day optimization with user selection and date selection
    """
    print(f"\n🎯 INTERACTIVE 365-DAY DELIVERY OPTIMIZATION WITH DATE SELECTION")
    print("=" * 70)
    
    # Step 1: Date Selection
    print("\n📅 STEP 1: Select Reference Date")
    print("-" * 40)
    print("Choose a reference date for prediction:")
    print("• Training period: 365 days BEFORE this date")
    print("• Prediction period: 365 days AFTER this date")
    
    selected_date = None
    while True:
        date_input = input(f"\nEnter date (YYYY-MM-DD) or 'today' for current date: ").strip()
        
        if date_input.lower() == 'today':
            selected_date = datetime.now()
            break
        elif date_input == '':
            selected_date = datetime.now()
            break
        else:
            try:
                selected_date = datetime.strptime(date_input, '%Y-%m-%d')
                break
            except ValueError:
                print("❌ Invalid date format. Please use YYYY-MM-DD")
                continue
    
    print(f"✅ Selected date: {selected_date.strftime('%Y-%m-%d')}")
    print(f"� Training period: {(selected_date - timedelta(days=365)).strftime('%Y-%m-%d')} to {selected_date.strftime('%Y-%m-%d')}")
    print(f"🔮 Prediction period: {selected_date.strftime('%Y-%m-%d')} to {(selected_date + timedelta(days=365)).strftime('%Y-%m-%d')}")
    
    # Step 2: Get available commercials for this date
    print(f"\n📋 STEP 2: Retrieving commercials with data in training period...")
    commercials = get_commercial_list(reference_date=selected_date)
    
    if not commercials:
        print("❌ No commercials found with sufficient data in the training period")
        print("💡 Try selecting a more recent date or check your database")
        return None
    
    # Display commercials
    print(f"\n📊 Available Commercials ({len(commercials)} found):")
    print("-" * 80)
    print(f"{'Code':<10} {'Records':<10} {'Clients':<8} {'First Record':<12} {'Last Record':<12} {'Avg Value':<10}")
    print("-" * 80)
    
    for i, comm in enumerate(commercials[:20], 1):  # Show top 20
        print(f"{str(comm['commercial_code']):<10} "
              f"{comm['total_records']:<10} "
              f"{comm['unique_clients']:<8} "
              f"{str(comm['first_record'])[:10]:<12} "
              f"{str(comm['last_record'])[:10]:<12} "
              f"{comm['avg_transaction_value']:<10.2f}")
    
    if len(commercials) > 20:
        print(f"... and {len(commercials) - 20} more")
    
    # User selection
    while True:
        try:
            selection = input(f"\n🎯 Enter commercial code (or 'auto' for best option): ").strip()
            
            if selection.lower() == 'auto':
                # Select the commercial with the most recent and substantial data
                selected_commercial = commercials[0]['commercial_code']
                print(f"🤖 Auto-selected commercial: {selected_commercial}")
                break
            elif selection == '':
                print("❌ Please enter a commercial code")
                continue
            else:
                # Check if the entered commercial exists
                matching_commercial = next((c for c in commercials if str(c['commercial_code']) == selection), None)
                if matching_commercial:
                    selected_commercial = selection
                    print(f"✅ Selected commercial: {selected_commercial}")
                    break
                else:
                    print(f"❌ Commercial '{selection}' not found. Please try again.")
                    continue
                    
        except KeyboardInterrupt:
            print(f"\n❌ Operation cancelled by user")
            return None
    
    # Ask for additional options
    try:
        include_revenue = input(f"\n💰 Include revenue optimization? (Y/n): ").strip().lower()
        include_revenue_optimization = include_revenue != 'n'
        
        save_files = input(f"💾 Save results to files? (Y/n): ").strip().lower()
        save_results = save_files != 'n'
        
        print(f"\n🚀 Starting 365-day optimization for commercial {selected_commercial}...")
        print(f"� Reference date: {selected_date.strftime('%Y-%m-%d')}")
        print(f"�💰 Revenue optimization: {'✅ Enabled' if include_revenue_optimization else '❌ Disabled'}")
        print(f"💾 Save results: {'✅ Enabled' if save_results else '❌ Disabled'}")
        
        # Run the optimization with the selected date
        results = dual_delivery_optimization_365_days(
            commercial_code=selected_commercial,
            selected_date=selected_date,
            include_revenue_optimization=include_revenue_optimization,
            save_results=save_results
        )
        
        return results
        
    except KeyboardInterrupt:
        print(f"\n❌ Operation cancelled by user")
        return None
    except Exception as e:
        print(f"❌ Error during optimization: {e}")
        return None
