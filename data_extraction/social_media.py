# data_extraction/social_media.py
import pandas as pd
import os
import logging
from data_utils import clean_data_for_sheets_sm
from config import OUTPUT_DIR
from google_sheets import save_data

def load_social_media_data(file_path, platform):
    """Load social media data from CSV/Excel"""
    try:
        if file_path.endswith('.csv'):
            data = pd.read_csv(file_path)
        else:
            data = pd.read_excel(file_path)
            
        # Standardize column names
        data.columns = data.columns.str.lower().str.replace(' ', '_')
        
        # Platform-specific processing
        if platform == 'facebook':
            data['date'] = pd.to_datetime(data['publish_time']).dt.date
        elif platform == 'instagram':
            data['date'] = pd.to_datetime(data['date']).dt.date
        elif platform == 'linkedin':
            data['date'] = pd.to_datetime(data['created_date']).dt.date
            
        return data
        
    except Exception as e:
        logging.error(f"Error loading {platform} data: {e}")
        return pd.DataFrame()

def fetch_social_media_data(sheets_service=None):
    platforms = {
        'facebook': 'FacebookData.csv',
        'instagram': 'InstagramData.csv',
        'linkedin': 'LinkedInData.xlsx',
        'youtube': 'YouTubeData.csv',
        'twitter': 'TwitterData.csv'
    }
    
    results = {}
    
    for platform, filename in platforms.items():
        try:
            filepath = os.path.join('analytics_data', filename)
            
            if not os.path.exists(filepath):
                logging.warning(f"{platform} data file not found: {filepath}")
                continue
                
            data = load_social_media_data(filepath, platform)
            if not data.empty:
                results[platform] = clean_data_for_sheets_sm(data)
            
        except Exception as e:
            logging.error(f"Error processing {platform} data: {str(e)}")
    
    return results

def load_linkedin_excel_data(file_path):
    """Load LinkedIn data from Excel file"""
    try:
        # Read all sheets from the Excel file
        xls = pd.ExcelFile(file_path)
        
        # Load metrics sheet
        metrics_df = pd.read_excel(xls, sheet_name='Metrics')
        metrics_df['Date'] = pd.to_datetime(metrics_df['Date'])
        
        # Load posts sheet
        posts_df = pd.read_excel(xls, sheet_name='Posts')
        posts_df['Created date'] = pd.to_datetime(posts_df['Created date'])
        
        return metrics_df, posts_df
        
    except Exception as e:
        logging.error(f"Error loading LinkedIn data: {e}")
        return pd.DataFrame(), pd.DataFrame()