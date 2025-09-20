# Python ETL Script for Power BI Data Pipeline
# filepath: d:\Neokai\Github_PBI\AgenticPowerBI\etl_global_sales.py

import pandas as pd
import numpy as np
from datetime import datetime

def clean_global_sales():
    try:
        print("Starting ETL process...")
        
        # Read Excel sheets
        print("Reading Excel sheets...")
        orders = pd.read_excel('global_sales.xlsx', sheet_name='Orders')
        returns = pd.read_excel('global_sales.xlsx', sheet_name='Returns')
        people = pd.read_excel('global_sales.xlsx', sheet_name='People')
        
        print(f"Orders shape: {orders.shape}")
        print(f"Returns shape: {returns.shape}")
        print(f"People shape: {people.shape}")
        
        # Clean and standardize Orders
        print("Cleaning Orders data...")
        
        # Remove duplicates
        initial_rows = len(orders)
        orders = orders.drop_duplicates()
        print(f"Removed {initial_rows - len(orders)} duplicate rows")
        
        # Handle missing values in critical columns
        orders = orders.dropna(subset=['Order ID', 'Customer ID', 'Product ID', 'Sales', 'Profit'])
        print(f"Final Orders rows after cleanup: {len(orders)}")
        
        
        # Process date columns (already in datetime format)
        print("Processing date columns...")
        orders['Order Date'] = pd.to_datetime(orders['Order Date'], errors='coerce')
        orders['Ship Date'] = pd.to_datetime(orders['Ship Date'], errors='coerce')
        
        # Create calculated columns
        print("Creating calculated columns...")
        
        # Profit Margin
        orders['Profit Margin'] = np.where(orders['Sales'] != 0, orders['Profit'] / orders['Sales'], 0)
        
        # Sales Category based on order value
        orders['Sales Category'] = pd.cut(orders['Sales'], 
                                        bins=[0, 100, 500, 1500, np.inf], 
                                        labels=['Low', 'Medium', 'High', 'Very High'])
        
        # Customer Tier based on total customer sales
        print("Creating customer tiers...")
        customer_sales = orders.groupby('Customer ID')['Sales'].sum().reset_index()
        customer_sales.rename(columns={'Sales': 'Customer_Total_Sales'}, inplace=True)
        
        # Create quartile-based tiers
        customer_sales['Customer Tier'] = pd.qcut(customer_sales['Customer_Total_Sales'], 
                                                4, 
                                                labels=['Bronze', 'Silver', 'Gold', 'Platinum'],
                                                duplicates='drop')
        
        # Merge customer tier back to orders
        orders = orders.merge(customer_sales[['Customer ID', 'Customer Tier', 'Customer_Total_Sales']], 
                            on='Customer ID', 
                            how='left')
        
        # Join Returns data
        print("Joining returns data...")
        orders = orders.merge(returns[['Order ID', 'Returned']], 
                            on='Order ID', 
                            how='left')
        
        # Since there's no direct salesperson mapping, we'll join People by Region
        print("Joining people data by region...")
        # This creates a region-to-person mapping (approximate)
        orders = orders.merge(people[['Person', 'Region']], 
                            on='Region', 
                            how='left', 
                            suffixes=('', '_Manager'))
        
        # Fill missing values
        print("Filling missing values...")
        orders['Returned'] = orders['Returned'].fillna('No')
        orders['Customer Tier'] = orders['Customer Tier'].fillna('Bronze')
        
        # Create additional useful columns
        orders['Year'] = orders['Order Date'].dt.year
        orders['Month'] = orders['Order Date'].dt.month
        orders['Quarter'] = orders['Order Date'].dt.quarter
        orders['Weekday'] = orders['Order Date'].dt.day_name()
        
        # Calculate delivery time
        orders['Delivery Days'] = (orders['Ship Date'] - orders['Order Date']).dt.days
        
        # Data quality summary
        print("\n=== DATA QUALITY SUMMARY ===")
        print(f"Total rows: {len(orders)}")
        print(f"Date range: {orders['Order Date'].min()} to {orders['Order Date'].max()}")
        print(f"Unique customers: {orders['Customer ID'].nunique()}")
        print(f"Unique products: {orders['Product ID'].nunique()}")
        print(f"Total sales: ${orders['Sales'].sum():,.2f}")
        print(f"Average profit margin: {orders['Profit Margin'].mean():.1%}")
        print(f"Orders with returns: {(orders['Returned'] == 'Yes').sum()}")
        
        # Export cleaned data
        print("\nExporting cleaned data...")
        output_file = 'global_sales_cleaned.csv'
        orders.to_csv(output_file, index=False)
        print(f"✅ Cleaned data exported to: {output_file}")
        
        # Create separate summary tables for Power BI
        print("Creating summary tables...")
        
        # Regional summary
        regional_summary = orders.groupby(['Region', 'Year', 'Quarter']).agg({
            'Sales': 'sum',
            'Profit': 'sum',
            'Order ID': 'nunique',
            'Customer ID': 'nunique'
        }).reset_index()
        regional_summary.columns = ['Region', 'Year', 'Quarter', 'Total_Sales', 'Total_Profit', 'Order_Count', 'Customer_Count']
        regional_summary.to_csv('regional_summary.csv', index=False)
        
        # Customer summary
        customer_summary = orders.groupby('Customer ID').agg({
            'Sales': 'sum',
            'Profit': 'sum',
            'Order ID': 'nunique',
            'Customer Tier': 'first',
            'Customer Name': 'first'
        }).reset_index()
        customer_summary.columns = ['Customer_ID', 'Total_Sales', 'Total_Profit', 'Order_Count', 'Customer_Tier', 'Customer_Name']
        customer_summary.to_csv('customer_summary.csv', index=False)
        
        print("✅ Summary tables created: regional_summary.csv, customer_summary.csv")
        print("✅ ETL process completed successfully!")
        
        return orders
        
    except Exception as e:
        print(f"❌ Error in ETL process: {str(e)}")
        return None

# Run the ETL process
if __name__ == "__main__":
    cleaned_data = clean_global_sales()