"""
Export Utilities Module
Centralized export functionality for all project components
"""

import pandas as pd
import json
import io
import os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
import mysql.connector
from flask import send_file, jsonify

def get_db_connection():
    """Get database connection"""
    return mysql.connector.connect(
        host='127.0.0.1',
        database='pfe1',
        user='root',
        password=''
    )

class ExportManager:
    """Centralized export manager for all data types"""
    
    def __init__(self):
        self.export_dir = "exports"
        self.ensure_export_directory()
    
    def ensure_export_directory(self):
        """Ensure export directory exists"""
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)
    
    def export_to_excel(self, data_dict, filename_prefix="export", sheets_config=None):
        """
        Export data to Excel with multiple sheets
        
        Args:
            data_dict: Dictionary with sheet_name: dataframe pairs
            filename_prefix: Prefix for filename
            sheets_config: Configuration for sheet formatting
        
        Returns:
            io.BytesIO: Excel file in memory
        """
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # Define formats
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'bg_color': '#4472C4',
                'font_color': 'white',
                'border': 1
            })
            
            date_format = workbook.add_format({
                'num_format': 'dd/mm/yyyy',
                'border': 1
            })
            
            number_format = workbook.add_format({
                'num_format': '#,##0.00',
                'border': 1
            })
            
            for sheet_name, df in data_dict.items():
                if df is not None and not df.empty:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    worksheet = writer.sheets[sheet_name]
                    
                    # Apply header format
                    for col_num, value in enumerate(df.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    
                    # Auto-adjust column widths
                    for idx, col in enumerate(df.columns):
                        max_length = max(
                            df[col].astype(str).map(len).max(),
                            len(col)
                        ) + 2
                        worksheet.set_column(idx, idx, min(max_length, 50))
                    
                    # Apply number format to numeric columns
                    for idx, col in enumerate(df.columns):
                        if df[col].dtype in ['float64', 'int64']:
                            worksheet.set_column(idx, idx, None, number_format)
        
        output.seek(0)
        return output
    
    def export_to_csv(self, df, filename_prefix="export"):
        """Export DataFrame to CSV"""
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8')
        return output.getvalue()
    
    def export_to_json(self, data, filename_prefix="export"):
        """Export data to JSON with metadata"""
        export_data = {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "export_type": filename_prefix,
                "version": "1.0"
            },
            "data": data
        }
        
        filename = f"{self.export_dir}/{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        return filename

def export_clients_data():
    """Export all clients data"""
    try:
        conn = get_db_connection()
        
        # Main clients data
        clients_query = """
        SELECT 
            client_code,
            nom_client,
            adresse,
            ville,
            COUNT(DISTINCT commercial_code) as nombre_commerciaux,
            COUNT(*) as total_commandes,
            SUM(net_a_payer) as chiffre_affaires_total,
            AVG(net_a_payer) as commande_moyenne,
            MIN(date) as premiere_commande,
            MAX(date) as derniere_commande
        FROM entetecommercials 
        WHERE client_code IS NOT NULL AND nom_client IS NOT NULL
        GROUP BY client_code, nom_client, adresse, ville
        ORDER BY chiffre_affaires_total DESC
        """
        
        clients_df = pd.read_sql(clients_query, conn)
        
        # Clients by commercial
        clients_commercial_query = """
        SELECT 
            commercial_code,
            client_code,
            nom_client,
            COUNT(*) as commandes,
            SUM(net_a_payer) as ca_total,
            MAX(date) as derniere_visite
        FROM entetecommercials 
        WHERE client_code IS NOT NULL AND commercial_code IS NOT NULL
        GROUP BY commercial_code, client_code, nom_client
        ORDER BY commercial_code, ca_total DESC
        """
        
        clients_commercial_df = pd.read_sql(clients_commercial_query, conn)
        
        # Top products by client
        products_clients_query = """
        SELECT 
            client_code,
            nom_client,
            produit_code,
            SUM(quantite) as quantite_totale,
            SUM(net_a_payer) as ca_produit
        FROM entetecommercials 
        WHERE client_code IS NOT NULL AND produit_code IS NOT NULL
        GROUP BY client_code, nom_client, produit_code
        ORDER BY client_code, ca_produit DESC
        """
        
        products_clients_df = pd.read_sql(products_clients_query, conn)
        conn.close()
        
        export_manager = ExportManager()
        
        # Prepare data for Excel export
        data_dict = {
            'Clients_Resume': clients_df,
            'Clients_par_Commercial': clients_commercial_df,
            'Produits_par_Client': products_clients_df
        }
        
        return export_manager.export_to_excel(data_dict, "clients_analysis")
        
    except Exception as e:
        print(f"Error exporting clients data: {str(e)}")
        return None

def export_commercials_data():
    """Export all commercials data"""
    try:
        conn = get_db_connection()
        
        # Commercials performance
        commercials_query = """
        SELECT 
            commercial_code,
            COUNT(DISTINCT client_code) as nombre_clients,
            COUNT(*) as total_visites,
            SUM(net_a_payer) as chiffre_affaires_total,
            AVG(net_a_payer) as ca_moyen_par_visite,
            MIN(date) as premiere_visite,
            MAX(date) as derniere_visite,
            COUNT(DISTINCT DATE_FORMAT(date, '%Y-%m')) as mois_actifs
        FROM entetecommercials 
        WHERE commercial_code IS NOT NULL
        GROUP BY commercial_code
        ORDER BY chiffre_affaires_total DESC
        """
        
        commercials_df = pd.read_sql(commercials_query, conn)
        
        # Monthly performance
        monthly_query = """
        SELECT 
            commercial_code,
            DATE_FORMAT(date, '%Y-%m') as mois,
            COUNT(*) as visites,
            COUNT(DISTINCT client_code) as clients_uniques,
            SUM(net_a_payer) as ca_mensuel
        FROM entetecommercials 
        WHERE commercial_code IS NOT NULL
        GROUP BY commercial_code, DATE_FORMAT(date, '%Y-%m')
        ORDER BY commercial_code, mois
        """
        
        monthly_df = pd.read_sql(monthly_query, conn)
        
        # Product performance by commercial
        products_query = """
        SELECT 
            commercial_code,
            produit_code,
            SUM(quantite) as quantite_totale,
            SUM(net_a_payer) as ca_produit,
            COUNT(DISTINCT client_code) as clients_touches
        FROM entetecommercials 
        WHERE commercial_code IS NOT NULL AND produit_code IS NOT NULL
        GROUP BY commercial_code, produit_code
        ORDER BY commercial_code, ca_produit DESC
        """
        
        products_df = pd.read_sql(products_query, conn)
        conn.close()
        
        export_manager = ExportManager()
        
        data_dict = {
            'Commerciaux_Performance': commercials_df,
            'Performance_Mensuelle': monthly_df,
            'Produits_par_Commercial': products_df
        }
        
        return export_manager.export_to_excel(data_dict, "commercials_analysis")
        
    except Exception as e:
        print(f"Error exporting commercials data: {str(e)}")
        return None

def export_products_data():
    """Export all products data"""
    try:
        conn = get_db_connection()
        
        # Products performance
        products_query = """
        SELECT 
            produit_code,
            COUNT(DISTINCT client_code) as nombre_clients,
            COUNT(DISTINCT commercial_code) as nombre_commerciaux,
            SUM(quantite) as quantite_totale,
            SUM(net_a_payer) as chiffre_affaires_total,
            AVG(net_a_payer) as prix_moyen,
            MIN(date) as premiere_vente,
            MAX(date) as derniere_vente
        FROM entetecommercials 
        WHERE produit_code IS NOT NULL
        GROUP BY produit_code
        ORDER BY chiffre_affaires_total DESC
        """
        
        products_df = pd.read_sql(products_query, conn)
        
        # Monthly trends
        monthly_products_query = """
        SELECT 
            produit_code,
            DATE_FORMAT(date, '%Y-%m') as mois,
            SUM(quantite) as quantite_mensuelle,
            SUM(net_a_payer) as ca_mensuel,
            COUNT(DISTINCT client_code) as clients_uniques
        FROM entetecommercials 
        WHERE produit_code IS NOT NULL
        GROUP BY produit_code, DATE_FORMAT(date, '%Y-%m')
        ORDER BY produit_code, mois
        """
        
        monthly_products_df = pd.read_sql(monthly_products_query, conn)
        
        # Top clients per product
        clients_products_query = """
        SELECT 
            produit_code,
            client_code,
            nom_client,
            SUM(quantite) as quantite_totale,
            SUM(net_a_payer) as ca_total,
            COUNT(*) as nombre_commandes
        FROM entetecommercials 
        WHERE produit_code IS NOT NULL AND client_code IS NOT NULL
        GROUP BY produit_code, client_code, nom_client
        ORDER BY produit_code, ca_total DESC
        """
        
        clients_products_df = pd.read_sql(clients_products_query, conn)
        conn.close()
        
        export_manager = ExportManager()
        
        data_dict = {
            'Produits_Performance': products_df,
            'Tendances_Mensuelles': monthly_products_df,
            'Clients_par_Produit': clients_products_df
        }
        
        return export_manager.export_to_excel(data_dict, "products_analysis")
        
    except Exception as e:
        print(f"Error exporting products data: {str(e)}")
        return None

def export_global_dashboard_data():
    """Export global dashboard data"""
    try:
        conn = get_db_connection()
        
        # Global KPIs
        kpis_query = """
        SELECT 
            COUNT(DISTINCT client_code) as total_clients,
            COUNT(DISTINCT commercial_code) as total_commerciaux,
            COUNT(DISTINCT produit_code) as total_produits,
            COUNT(*) as total_transactions,
            SUM(net_a_payer) as chiffre_affaires_global,
            AVG(net_a_payer) as transaction_moyenne,
            MIN(date) as premiere_transaction,
            MAX(date) as derniere_transaction
        FROM entetecommercials
        """
        
        kpis_df = pd.read_sql(kpis_query, conn)
        
        # Daily activity
        daily_query = """
        SELECT 
            date,
            COUNT(*) as transactions,
            COUNT(DISTINCT client_code) as clients_actifs,
            COUNT(DISTINCT commercial_code) as commerciaux_actifs,
            SUM(net_a_payer) as ca_journalier
        FROM entetecommercials 
        GROUP BY date
        ORDER BY date DESC
        LIMIT 365
        """
        
        daily_df = pd.read_sql(daily_query, conn)
        
        # Top performers
        top_clients_query = """
        SELECT 
            client_code,
            nom_client,
            SUM(net_a_payer) as ca_total,
            COUNT(*) as transactions
        FROM entetecommercials 
        WHERE client_code IS NOT NULL
        GROUP BY client_code, nom_client
        ORDER BY ca_total DESC
        LIMIT 50
        """
        
        top_clients_df = pd.read_sql(top_clients_query, conn)
        
        conn.close()
        
        export_manager = ExportManager()
        
        data_dict = {
            'KPIs_Globaux': kpis_df,
            'Activite_Quotidienne': daily_df,
            'Top_50_Clients': top_clients_df
        }
        
        return export_manager.export_to_excel(data_dict, "dashboard_global")
        
    except Exception as e:
        print(f"Error exporting dashboard data: {str(e)}")
        return None
