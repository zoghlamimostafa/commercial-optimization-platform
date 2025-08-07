import pandas as pd
import numpy as np

def clean_sales_data(file_path):
    """
    Cleans and preprocesses historical sales data.

    Args:
        file_path (str): Path to the sales data file (CSV or Excel).

    Returns:
        pd.DataFrame: Cleaned and preprocessed sales data.
    """
    # Load data
    try:
        if file_path.endswith('.csv'):
            data = pd.read_csv(file_path)
        elif file_path.endswith(('.xls', '.xlsx')):
            data = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format. Please provide a CSV or Excel file.")
    except Exception as e:
        raise Exception(f"Error loading file: {e}")

    # Drop duplicates
    data = data.drop_duplicates()    # Handle missing values
    data = data.fillna({
        'client_code': 'UNKNOWN',
        'produit_code': 'UNKNOWN',
        'net_a_payer': 0,
        'quantite': 0
    })

    # Convert date column to datetime
    if 'date' in data.columns:
        data['date'] = pd.to_datetime(data['date'], errors='coerce')
        data = data.dropna(subset=['date'])  # Drop rows with invalid dates

    # Remove negative or zero values in key columns
    data = data[(data['net_a_payer'] > 0) & (data['quantite'] > 0)]

    # Add derived columns (e.g., month, year)
    data['month'] = data['date'].dt.month
    data['year'] = data['date'].dt.year

    return data

# Example usage
if __name__ == "__main__":
    file_path = "path_to_sales_data.csv"  # Replace with actual file path
    cleaned_data = clean_sales_data(file_path)
    print(cleaned_data.head())

def clean_dataframe(data):
    """
    Cleans and preprocesses historical sales data from a DataFrame.

    Args:
        data (pd.DataFrame): DataFrame containing sales data.

    Returns:
        pd.DataFrame: Cleaned and preprocessed sales data.
    """
    # Drop duplicates
    data = data.drop_duplicates()

    # Handle missing values with flexible column names
    fill_values = {}
    if 'client_code' in data.columns:
        fill_values['client_code'] = 'UNKNOWN'
    if 'produit_code' in data.columns:
        fill_values['produit_code'] = 'UNKNOWN'
    if 'net_a_payer' in data.columns:
        fill_values['net_a_payer'] = 0
    if 'daily_revenue' in data.columns:
        fill_values['daily_revenue'] = 0
    if 'quantite' in data.columns:
        fill_values['quantite'] = 0
    if 'nombre_visites' in data.columns:
        fill_values['nombre_visites'] = 0
    
    data = data.fillna(fill_values)

    # Convert date column to datetime
    if 'date' in data.columns:
        data['date'] = pd.to_datetime(data['date'], errors='coerce')
        data = data.dropna(subset=['date'])  # Drop rows with invalid dates

    # Remove negative or zero values in key columns (flexible)
    filter_conditions = []
    if 'net_a_payer' in data.columns:
        filter_conditions.append(data['net_a_payer'] > 0)
    if 'daily_revenue' in data.columns:
        filter_conditions.append(data['daily_revenue'] > 0)
    if 'quantite' in data.columns:
        filter_conditions.append(data['quantite'] > 0)
    if 'nombre_visites' in data.columns:
        filter_conditions.append(data['nombre_visites'] > 0)
    
    # Apply filters if any conditions exist
    if filter_conditions:
        combined_condition = filter_conditions[0]
        for condition in filter_conditions[1:]:
            combined_condition = combined_condition & condition
        data = data[combined_condition]

    # Add derived columns (e.g., month, year)
    if 'date' in data.columns:
        data['month'] = data['date'].dt.month
        data['year'] = data['date'].dt.year

    return data
