# data_processor.py
import pandas as pd
import re
from datetime import datetime

class DataProcessor:
    @staticmethod
    def parse_quantity_string(quantity_str):
        """Parse quantity strings like '3packs (200per pack)' and return total units only"""
        try:
            # Extract numbers from string
            match = re.search(r'(\d+)\s*packs?\s*\((\d+)\s*per pack\)', str(quantity_str).lower())
            if match:
                packs = int(match.group(1))
                per_pack = int(match.group(2))
                return packs * per_pack  # Return total units only
            return 0
        except:
            return 0
    
    @staticmethod
    def load_excel_data(file_path):
        """Load and process Excel data - returns units only"""
        df = pd.read_excel(file_path)
        
        # Process data with units only
        parsed_data = []
        for index, row in df.iterrows():
            # Skip rows with missing item names
            if pd.isna(row.get('Item')):
                continue
                
            # Get total units - use the value from 'Total Units' column
            total_units = 0
            if 'Total Units' in row and not pd.isna(row['Total Units']):
                try:
                    total_units = int(row['Total Units'])
                except:
                    total_units = 0
            
            # Extract category from item name (more comprehensive)
            item_lower = str(row['Item']).lower()
            
            if any(x in item_lower for x in ['glove', 'mask', 'gown']):
                category = 'PPE'
            elif any(x in item_lower for x in ['silica', 'desiccant']):
                category = 'Desiccants'
            elif any(x in item_lower for x in ['needle', 'syringe', 'lancet']):
                category = 'Medical Devices'
            elif any(x in item_lower for x in ['tube', 'vial', 'pipette', 'petri', 'falcon']):
                category = 'Labware'
            elif any(x in item_lower for x in ['agar', 'broth', 'medium', 'buffer', 'solution', 'acid', 'base']):
                category = 'Reagents'
            elif any(x in item_lower for x in ['paper', 'filter', 'slide', 'cover', 'container']):
                category = 'Consumables'
            elif any(x in item_lower for x in ['methanol', 'chloroform', 'glycerol', 'giemsa', 'tryzol']):
                category = 'Chemicals'
            elif any(x in item_lower for x in ['scale', 'thermometer', 'microscope', 'pipette aid']):
                category = 'Equipment'
            elif any(x in item_lower for x in ['box', 'bag', 'rack', 'holder']):
                category = 'Packaging'
            else:
                category = 'General Supplies'
            
            # Generate item ID
            item_id = f"BIO-{category[:3].upper()}-{str(index + 1).zfill(4)}"
            
            # Handle expiry date - make it optional
            expiry_date = None
            if 'Expiry Date' in row and not pd.isna(row['Expiry Date']):
                try:
                    # Try to parse date
                    if isinstance(row['Expiry Date'], (datetime, pd.Timestamp)):
                        expiry_date = row['Expiry Date'].strftime('%Y-%m-%d')
                    else:
                        expiry_date = str(row['Expiry Date'])
                except:
                    expiry_date = None
            
            parsed_data.append({
                'item_id': item_id,
                'item_name': str(row['Item']).strip(),
                'category': category,
                'quantity': int(total_units),  # Store as quantity (units)
                'unit': str(row.get('Unit', 'Units')).strip(),
                'expiry_date': expiry_date,
                'storage_location': 'Main Store',
                'supplier': 'Standard Supplier',
                'reorder_level': 50,  # Default reorder level in units
                'status': 'Active'
            })
        
        return pd.DataFrame(parsed_data)
    
    @staticmethod
    def calculate_metrics(df):
        """Calculate key metrics from data - simplified for units only"""
        if df.empty:
            return {}
        
        # Use 'quantity' instead of 'packs' and 'total_units'
        metrics = {
            'total_items': len(df),
            'total_units': df['quantity'].sum() if 'quantity' in df.columns else 0,
            'categories': df['category'].nunique(),
            'avg_units_per_item': df['quantity'].mean() if 'quantity' in df.columns else 0,
            'low_stock_count': (df['quantity'] <= df['reorder_level']).sum() if 'quantity' in df.columns and 'reorder_level' in df.columns else 0
        }
        
        # Expiry analysis
        if 'expiry_date' in df.columns:
            df['expiry_date'] = pd.to_datetime(df['expiry_date'], errors='coerce')
            df['days_to_expiry'] = (df['expiry_date'] - pd.Timestamp.now()).dt.days
            metrics['expired_items'] = (df['days_to_expiry'] <= 0).sum()
            metrics['expiring_soon'] = ((df['days_to_expiry'] > 0) & (df['days_to_expiry'] <= 30)).sum()
        else:
            metrics['expired_items'] = 0
            metrics['expiring_soon'] = 0
        
        return metrics