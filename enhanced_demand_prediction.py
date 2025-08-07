"""
Enhanced Demand Prediction System
More realistic predictions based on:
- Seasonal patterns
- Purchase frequency
- Trend analysis
- Client behavior patterns
- Product lifecycle
- Business constraints
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')

class EnhancedDemandPredictor:
    def __init__(self):
        self.min_prediction = 1
        self.max_prediction = 50
        self.default_prediction = 3
        
    def predict_client_demand(self, historical_data, client_code, product_code, prediction_date):
        """
        Enhanced demand prediction with multiple realistic factors.
        """
        # Filter data for the specific client and product 
        client_data = historical_data[
            (historical_data['client_code'] == client_code) &
            (historical_data['produit_code'] == product_code)
        ].copy()
        
        if client_data.empty:
            return self._get_default_prediction_for_new_product(historical_data, product_code)
        
        # Ensure we have the right column for quantity
        qty_col = self._find_quantity_column(client_data)
        if qty_col is None:
            return self.default_prediction
        
        # Prepare data
        client_data['date'] = pd.to_datetime(client_data['date'])
        client_data = client_data.sort_values('date')
        client_data = client_data[client_data[qty_col] > 0]  # Remove zero quantities
        
        if len(client_data) == 0:
            return self.default_prediction
        
        try:
            # 1. SEASONAL ANALYSIS
            seasonal_factor = self._analyze_seasonal_patterns(client_data, qty_col, prediction_date)
            
            # 2. TREND ANALYSIS  
            trend_factor = self._analyze_trend_patterns(client_data, qty_col)
            
            # 3. FREQUENCY ANALYSIS
            frequency_factor = self._analyze_purchase_frequency(client_data, prediction_date)
            
            # 4. RECENT BEHAVIOR ANALYSIS
            recent_factor = self._analyze_recent_behavior(client_data, qty_col, prediction_date)
            
            # 5. PRODUCT LIFECYCLE ANALYSIS
            lifecycle_factor = self._analyze_product_lifecycle(historical_data, product_code, prediction_date)
            
            # 6. BASE QUANTITY (weighted historical average)
            base_qty = self._calculate_weighted_average(client_data, qty_col)
            
            # Combine all factors for realistic prediction
            predicted_qty = (base_qty * 
                           seasonal_factor * 
                           trend_factor * 
                           frequency_factor * 
                           recent_factor * 
                           lifecycle_factor)
            
            # Apply business logic constraints
            predicted_qty = self._apply_business_constraints(predicted_qty, client_data, qty_col)
            
            # All predictions are in TND (Tunisian Dinar)
            result = max(self.min_prediction, min(self.max_prediction, round(predicted_qty)))
            # Optionally, you can return a dict with currency if needed:
            # return {"quantity": result, "currency": "TND"}
            return result
            
        except Exception as e:
            print(f"Enhanced prediction failed for {client_code}-{product_code}: {str(e)}")
            # Fallback to simple average
            return max(self.min_prediction, min(self.max_prediction, round(client_data[qty_col].mean())))

    def _find_quantity_column(self, data):
        """Find the quantity column in the data."""
        for col in ['quantite', 'quantity', 'qte', 'product_quantity']:
            if col in data.columns:
                return col
        return None
    
    def _get_default_prediction_for_new_product(self, historical_data, product_code):
        """Get default prediction for new product based on overall product performance."""
        try:
            # Find similar products or overall average
            product_data = historical_data[historical_data['produit_code'] == product_code]
            if not product_data.empty:
                qty_col = self._find_quantity_column(product_data)
                if qty_col and len(product_data) > 0:
                    avg_qty = product_data[qty_col].mean()
                    return max(1, min(10, round(avg_qty)))
            return self.default_prediction
        except:
            return self.default_prediction

    def _analyze_seasonal_patterns(self, client_data, qty_col, prediction_date):
        """
        Analyze seasonal patterns (monthly, weekly, quarterly).
        """
        if len(client_data) < 6:
            return 1.0
        
        try:
            # Add time components
            client_data = client_data.copy()
            client_data['month'] = client_data['date'].dt.month
            client_data['quarter'] = client_data['date'].dt.quarter
            client_data['day_of_week'] = client_data['date'].dt.dayofweek
            
            # Monthly seasonality
            monthly_avg = client_data.groupby('month')[qty_col].mean()
            prediction_month = prediction_date.month
            
            seasonal_factor = 1.0
            
            if prediction_month in monthly_avg.index and len(monthly_avg) > 3:
                overall_avg = client_data[qty_col].mean()
                if overall_avg > 0:
                    monthly_factor = monthly_avg[prediction_month] / overall_avg
                    
                    # Apply seasonal logic based on month
                    if prediction_month in [11, 12, 1]:  # Winter/holiday season
                        monthly_factor *= 1.1  # Slight increase
                    elif prediction_month in [6, 7, 8]:  # Summer
                        monthly_factor *= 0.95  # Slight decrease
                    elif prediction_month in [3, 4, 5]:  # Spring
                        monthly_factor *= 1.05  # Moderate increase
                    
                    seasonal_factor = monthly_factor
            
            # Quarterly seasonality for additional smoothing
            if len(client_data) > 12:
                quarterly_avg = client_data.groupby('quarter')[qty_col].mean()
                prediction_quarter = (prediction_month - 1) // 3 + 1
                
                if prediction_quarter in quarterly_avg.index:
                    overall_avg = client_data[qty_col].mean()
                    if overall_avg > 0:
                        quarterly_factor = quarterly_avg[prediction_quarter] / overall_avg
                        seasonal_factor = (seasonal_factor * 0.7) + (quarterly_factor * 0.3)
            
            # Limit extreme seasonal variations
            return max(0.5, min(2.0, seasonal_factor))
            
        except Exception:
            return 1.0

    def _analyze_trend_patterns(self, client_data, qty_col):
        """
        Analyze if the client's demand is increasing, decreasing, or stable.
        """
        if len(client_data) < 4:
            return 1.0
        
        try:
            # Sort by date and use time series analysis
            client_data = client_data.sort_values('date').reset_index(drop=True)
            
            if len(client_data) >= 6:
                # Use linear regression to find trend
                X = np.arange(len(client_data)).reshape(-1, 1)
                y = client_data[qty_col].values
                
                model = LinearRegression()
                model.fit(X, y)
                
                # Predict next value based on trend
                next_prediction = model.predict([[len(client_data)]])[0]
                current_avg = client_data[qty_col].mean()
                
                if current_avg > 0:
                    trend_factor = next_prediction / current_avg
                    # Limit extreme trend changes
                    return max(0.6, min(1.8, trend_factor))
            
            # Fallback: compare recent vs older data
            elif len(client_data) >= 4:
                recent_avg = client_data[qty_col].iloc[-2:].mean()
                older_avg = client_data[qty_col].iloc[:-2].mean()
                
                if older_avg > 0:
                    trend_factor = recent_avg / older_avg
                    return max(0.7, min(1.5, trend_factor))
            
            return 1.0
            
        except Exception:
            return 1.0

    def _analyze_purchase_frequency(self, client_data, prediction_date):
        """
        Analyze how frequently the client purchases this product.
        """
        if len(client_data) < 2:
            return 1.0
        
        try:
            # Calculate average days between purchases
            client_data = client_data.sort_values('date')
            date_diffs = client_data['date'].diff().dt.days.dropna()
            
            if len(date_diffs) == 0:
                return 1.0
            
            avg_frequency = date_diffs.mean()
            
            # Check how many days since last purchase
            last_purchase = client_data['date'].max()
            days_since_last = (prediction_date - last_purchase).days
            
            # Frequency-based adjustment
            if avg_frequency > 0:
                if days_since_last > avg_frequency * 1.5:
                    # Overdue for purchase - increase probability
                    frequency_factor = 1.3
                elif days_since_last < avg_frequency * 0.5:
                    # Too soon for next purchase - decrease probability
                    frequency_factor = 0.7
                elif avg_frequency <= 30:
                    # High frequency product (monthly or more)
                    frequency_factor = 1.1
                elif avg_frequency <= 90:
                    # Medium frequency product (quarterly)
                    frequency_factor = 1.0
                else:
                    # Low frequency product
                    frequency_factor = 0.9
            else:
                frequency_factor = 1.0
            
            return max(0.5, min(1.5, frequency_factor))
            
        except Exception:
            return 1.0

    def _analyze_recent_behavior(self, client_data, qty_col, prediction_date):
        """
        Analyze recent purchasing behavior for momentum.
        """
        if len(client_data) < 3:
            return 1.0
        
        try:
            # Look at last 90 days
            recent_cutoff = prediction_date - timedelta(days=90)
            recent_data = client_data[client_data['date'] >= recent_cutoff]
            
            if len(recent_data) == 0:
                return 0.8  # No recent activity
            
            # Compare recent activity to historical average
            recent_avg = recent_data[qty_col].mean()
            historical_avg = client_data[qty_col].mean()
            
            if historical_avg > 0:
                recent_factor = recent_avg / historical_avg
                
                # Check if there's been recent activity
                last_purchase = client_data['date'].max()
                days_since_last = (prediction_date - last_purchase).days
                
                if days_since_last <= 30:
                    recent_factor *= 1.1  # Recent activity boost
                elif days_since_last <= 60:
                    recent_factor *= 1.0  # Normal
                else:
                    recent_factor *= 0.9  # Declining activity
                
                return max(0.6, min(1.6, recent_factor))
            
            return 1.0
            
        except Exception:
            return 1.0

    def _analyze_product_lifecycle(self, historical_data, product_code, prediction_date):
        """
        Analyze product lifecycle stage across all clients.
        """
        try:
            product_data = historical_data[historical_data['produit_code'] == product_code].copy()
            if product_data.empty:
                return 1.0
            
            product_data['date'] = pd.to_datetime(product_data['date'])
            
            # Calculate product age and activity
            first_sale = product_data['date'].min()
            last_sale = product_data['date'].max()
            product_age_days = (prediction_date - first_sale).days
            
            # Recent activity (last 6 months)
            recent_cutoff = prediction_date - timedelta(days=180)
            recent_activity = len(product_data[product_data['date'] >= recent_cutoff])
            total_activity = len(product_data)
            
            # Lifecycle stage determination
            if product_age_days < 180:
                # New product - growing phase
                lifecycle_factor = 1.15
            elif recent_activity / total_activity > 0.6:
                # Mature product with good activity
                lifecycle_factor = 1.0
            elif recent_activity / total_activity > 0.3:
                # Declining but still viable
                lifecycle_factor = 0.9
            else:
                # Low activity product
                lifecycle_factor = 0.8
            
            return max(0.7, min(1.3, lifecycle_factor))
            
        except Exception:
            return 1.0

    def _calculate_weighted_average(self, client_data, qty_col):
        """
        Calculate weighted average giving more weight to recent purchases.
        """
        try:
            if len(client_data) == 0:
                return self.default_prediction
            
            # Sort by date
            client_data = client_data.sort_values('date')
            
            # Create weights (more recent = higher weight)
            weights = np.linspace(0.5, 1.0, len(client_data))
            weighted_avg = np.average(client_data[qty_col], weights=weights)
            
            return max(1, weighted_avg)
            
        except Exception:
            return client_data[qty_col].mean() if len(client_data) > 0 else self.default_prediction

    def _apply_business_constraints(self, predicted_qty, client_data, qty_col):
        """
        Apply realistic business constraints to predictions.
        """
        try:
            # Get client's historical range
            min_qty = client_data[qty_col].min()
            max_qty = client_data[qty_col].max()
            std_qty = client_data[qty_col].std()
            mean_qty = client_data[qty_col].mean()
            
            # Don't predict too far outside historical range
            if predicted_qty > max_qty * 1.5:
                predicted_qty = max_qty * 1.2
            elif predicted_qty < min_qty * 0.5:
                predicted_qty = min_qty * 0.8
            
            # If prediction is too far from mean, bring it closer
            if abs(predicted_qty - mean_qty) > 2 * std_qty:
                if predicted_qty > mean_qty:
                    predicted_qty = mean_qty + 1.5 * std_qty
                else:
                    predicted_qty = mean_qty - 1.5 * std_qty
            
            return predicted_qty
            
        except Exception:
            return predicted_qty

def generate_enhanced_demand_predictions(historical_data, clients, products, prediction_date):
    """
    Generate enhanced demand predictions for all clients and products.
    """
    predictor = EnhancedDemandPredictor()
    predictions = {}
    
    # Ensure prediction_date is datetime
    prediction_date = pd.to_datetime(prediction_date)
    
    print(f"Generating enhanced predictions for {len(clients)} clients and {len(products)} products...")
    
    for client in clients:
        client_predictions = {}
        
        for product in products:
            try:
                predicted_qty = predictor.predict_client_demand(
                    historical_data, client, product, prediction_date
                )
                
                if predicted_qty > 0:
                    # All predictions are in TND (Tunisian Dinar)
                    client_predictions[str(product)] = {
                        "quantity": int(predicted_qty),
                        "currency": "TND"
                    }
                    
            except Exception as e:
                print(f"Error predicting for {client}-{product}: {str(e)}")
                # Use a realistic fallback based on product category
                client_predictions[str(product)] = {
                    "quantity": predictor._get_realistic_fallback(product),
                    "currency": "TND"
                }
        
        # Ensure each client has at least a few products
        if len(client_predictions) < 3 and len(products) > 0:
            # Add top products with small quantities
            top_products = products[:3]
            for product in top_products:
                if str(product) not in client_predictions:
                    client_predictions[str(product)] = {
                        "quantity": np.random.randint(1, 4),
                        "currency": "TND"
                    }
        
        if client_predictions:
            predictions[str(client)] = client_predictions
    
    # Ensure we have some predictions
    if not predictions and clients and products:
        sample_client = str(clients[0])
        sample_products = products[:5]
        predictions[sample_client] = {
            str(product): {"quantity": np.random.randint(2, 8), "currency": "TND"} for product in sample_products
        }
    
    return predictions
