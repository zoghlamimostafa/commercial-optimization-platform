import pandas as pd
import numpy as np
from datetime import datetime
import geopy.distance
from sklearn.ensemble import RandomForestRegressor
from historical_analysis import analyze_sales_trends
import json

def calculate_distance(coord1, coord2):
    """
    Calculate distance between two GPS coordinates in kilometers.
    
    Args:
        coord1 (tuple): (latitude, longitude) of first point
        coord2 (tuple): (latitude, longitude) of second point
    
    Returns:
        float: Distance in kilometers
    """
    return geopy.distance.geodesic(coord1, coord2).km

def get_optimal_route(commercial_location, client_locations):
    """
    Determine optimal delivery route using nearest neighbor algorithm.
    
    Args:
        commercial_location (tuple): (latitude, longitude) of delivery agent
        client_locations (dict): Dictionary of client_code: (latitude, longitude)
    
    Returns:
        list: Ordered list of client codes representing optimal route
    """
    unvisited = client_locations.copy()
    route = []
    current_pos = commercial_location

    while unvisited:
        # Find nearest unvisited client
        distances = {code: calculate_distance(current_pos, coord) 
                    for code, coord in unvisited.items()}
        nearest = min(distances.items(), key=lambda x: x[1])[0]
        
        route.append(nearest)
        current_pos = unvisited[nearest]
        del unvisited[nearest]

    return route

from demand_prediction import generate_demand_predictions

def predict_client_products(historical_data, client_code, delivery_date):
    """
    Predict products and quantities a client is likely to need.
    
    Args:
        historical_data (pd.DataFrame): Historical sales data
        client_code (str): Client identifier
        delivery_date (datetime): Planned delivery date
    
    Returns:
        dict: Dictionary of predicted product quantities
    """    
    # Get unique products from historical data
    products = historical_data["produit_code"].unique()
    
    # Generate predictions using SARIMA
    predictions = generate_demand_predictions(
        historical_data,
        [client_code],
        products, 
        delivery_date
    )
    
    return predictions.get(client_code, {})

def generate_delivery_plan(commercial_code, delivery_date, historical_data, locations_data):
    """
    Generate complete delivery plan with route and product predictions.
    
    Args:
        commercial_code (str): Delivery agent identifier
        delivery_date (datetime): Planned delivery date
        historical_data (pd.DataFrame): Historical sales data
        locations_data (dict): Dictionary containing GPS coordinates for commercial and clients
    
    Returns:
        dict: Complete delivery plan with route and predictions
    """
    # Get commercial location
    commercial_location = locations_data.get("commercials", {}).get(commercial_code)
    if not commercial_location:
        # Use default location for Ariana, Tunisia if commercial location not found
        commercial_location = (36.862499, 10.195556)  # Default to Ariana coordinates (Clediss location)
        print(f"Warning: Using default location for commercial {commercial_code}")

    # Get clients for the same day/month in previous years
    MAX_CLIENTS_PER_DAY = 200
    if "date" in historical_data.columns:
        if not pd.api.types.is_datetime64_dtype(historical_data["date"]):
            historical_data["date"] = pd.to_datetime(historical_data["date"], errors="coerce")
        day = delivery_date.day
        month = delivery_date.month
        years = historical_data["date"].dt.year.unique()
        years = [y for y in years if y != delivery_date.year]
        # Count frequency of each client on this day/month in previous years
        client_counts = {}
        for y in years:
            mask = (
                (historical_data["date"].dt.year == y) &
                (historical_data["date"].dt.month == month) &
                (historical_data["date"].dt.day == day)
            )
            clients = historical_data[mask]["client_code"].values
            for c in clients:
                client_counts[c] = client_counts.get(c, 0) + 1
        # Sort clients by frequency (descending), then by client code
        sorted_clients = sorted(client_counts.items(), key=lambda x: (-x[1], str(x[0])))
        scheduled_clients = [c for c, _ in sorted_clients]
        # Limit to MAX_CLIENTS_PER_DAY
        if len(scheduled_clients) > MAX_CLIENTS_PER_DAY:
            scheduled_clients = scheduled_clients[:MAX_CLIENTS_PER_DAY]
    else:
        scheduled_clients = []
    print(f"Found {len(scheduled_clients)} potential clients for this day in previous years (limited to {MAX_CLIENTS_PER_DAY})")

    if len(scheduled_clients) == 0:
        return {
            "commercial_code": commercial_code,
            "delivery_date": delivery_date.strftime("%Y-%m-%d"),
            "route": [],
            "packing_list": {},
            "total_distance": 0,
            "message": "No clients found for this day in previous years"
        }
    
    # Get client locations
    client_locations = {
        client: locations_data.get("clients", {}).get(client)
        for client in scheduled_clients
        if locations_data.get("clients", {}).get(client) is not None
    }
    
    print(f"Found {len(client_locations)} clients with valid locations")
    
    if not client_locations:
        # If no client locations found, return an empty plan
        return {
            "commercial_code": commercial_code,
            "delivery_date": delivery_date.strftime("%Y-%m-%d"),
            "route": [],
            "packing_list": {},
            "total_distance": 0,
            "message": "No valid client locations found for the specified date"
        }

    # Calculate optimal route
    route = get_optimal_route(commercial_location, client_locations)

    # Generate predictions for each client
    delivery_plan = {
        "commercial_code": commercial_code,
        "delivery_date": delivery_date.strftime("%Y-%m-%d"),
        "route": []
    }

    total_products = {}
    for client_code in route:
        predictions = predict_client_products(historical_data, client_code, delivery_date)
        
        # Add to route with distance from previous point
        prev_point = commercial_location if not delivery_plan["route"] else client_locations[delivery_plan["route"][-1]["client_code"]]
        distance = calculate_distance(prev_point, client_locations[client_code])
        
        delivery_plan["route"].append({
            "client_code": client_code,
            "location": client_locations[client_code],
            "distance": round(distance, 2),
            "predicted_products": predictions
        })

        # Aggregate products for packing list
        for product, qty in predictions.items():
            total_products[product] = total_products.get(product, 0) + qty

    delivery_plan["packing_list"] = total_products
    delivery_plan["total_distance"] = round(sum(stop["distance"] for stop in delivery_plan["route"]), 2)

    return delivery_plan
