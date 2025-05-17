from googleapiclient.errors import HttpError
import os
from config import SPREADSHEET_ID, OUTPUT_DIR

def get_sheet_id(sheets_service, sheet_name):
    """Get numeric sheet ID from sheet name"""
    try:
        spreadsheet = sheets_service.spreadsheets().get(
            spreadsheetId=SPREADSHEET_ID,
            fields="sheets(properties(title,sheetId))"
        ).execute()
        
        for sheet in spreadsheet.get('sheets', []):
            if sheet['properties']['title'] == sheet_name:
                return sheet['properties']['sheetId']
        
        return create_sheet(sheets_service, sheet_name)
        
    except Exception as e:
        print(f"⚠️ Error getting sheet ID: {e}")
        return None

def create_sheet(sheets_service, sheet_name):
    """Create new sheet and return its ID"""
    try:
        body = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': sheet_name,
                        'gridProperties': {
                            'frozenRowCount': 1,
                            'rowCount': 1000,
                            'columnCount': 20
                        },
                        'tabColor': {
                            'red': 0.2,
                            'green': 0.6,
                            'blue': 0.8
                        }
                    }
                }
            }]
        }
        result = sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=body
        ).execute()
        
        return result['replies'][0]['addSheet']['properties']['sheetId']
        
    except Exception as e:
        print(f"⚠️ Error creating sheet: {e}")
        return None

def save_data(data, filename, sheets_service):
    """Save data to local CSV and Google Sheet"""
    try:
        if data is None or data.empty:
            print("⚠️ No data to save")
            return False
            
        sheet_name = os.path.splitext(filename)[0]
        local_path = os.path.join(OUTPUT_DIR, filename)
        
        # Save locally
        data.to_csv(local_path, index=False)
        print(f"📁 Local save: {local_path}")
        
        # Prepare Google Sheets update
        sheet_id = get_sheet_id(sheets_service, sheet_name)
        if sheet_id is None:
            return False
        
        values = data.fillna('').astype(str).values.tolist()
        values = [[str(x).encode('ascii', 'ignore').decode('ascii') for x in row] 
                for row in values]
        values = [data.columns.tolist()] + data.values.tolist()
        
        # Clear existing data
        sheets_service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A:Z",
        ).execute()
        
        # Update with new data
        result = sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A1",
            valueInputOption='USER_ENTERED',
            body={'values': values}
        ).execute()
        
        # Apply formatting
        try:
            format_body = {
                'requests': [
                    {
                        'repeatCell': {
                            'range': {
                                'sheetId': sheet_id,
                                'startRowIndex': 0,
                                'endRowIndex': 1
                            },
                            'cell': {
                                'userEnteredFormat': {
                                    'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.6},
                                    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
                                }
                            },
                            'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                        }
                    },
                    {
                        'autoResizeDimensions': {
                            'dimensions': {
                                'sheetId': sheet_id,
                                'dimension': 'COLUMNS',
                                'startIndex': 0,
                                'endIndex': len(data.columns)
                            }
                        }
                    }
                ]
            }
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body=format_body
            ).execute()
        except Exception as e:
            print(f"⚠️ Formatting skipped: {e}")
        
        print(f"📊 Updated {sheet_name} ({result['updatedCells']} cells)")
        return True
        
    except Exception as e:
        print(f"❌ Failed to save {filename}: {e}")
        return False