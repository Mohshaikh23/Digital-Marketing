import pandas as pd

# data_extraction/data_cleaning.py
def clean_data_for_sheets(data: pd.DataFrame) -> pd.DataFrame:
    """Enhanced data cleaning for Google Sheets"""
    if data is None or data.empty:
        return data
        
    def clean_string(value):
        if pd.isna(value):
            return ""
        if isinstance(value, str):
            # Remove problematic characters
            value = (value.replace('\n', ' ')
                      .replace('\r', '')
                      .replace('"', "'")  # Replace double quotes with single
                      .strip())
            # Remove non-ASCII characters
            value = value.encode('ascii', 'ignore').decode('ascii')
            # Remove any remaining control characters
            return ''.join(char for char in value if 31 < ord(char) < 127)
        return value
        
    return data.map(clean_string)


# Alias for social media specific cleaning (if needed)
clean_data_for_sheets_sm = clean_data_for_sheets

