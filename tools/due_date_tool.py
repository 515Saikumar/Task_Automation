import os
import dateparser
from datetime import datetime, date
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# ==========================================
# SPRINT CONFIGURATION
# ==========================================
def get_sprint_dates():
    """Fetches the active sprint dates dynamically from the .env file."""
    start_str = os.getenv("SPRINT_START", "2026-08-24")
    end_str = os.getenv("SPRINT_END", "2026-09-10")
    
    try:
        sprint_start = datetime.strptime(start_str, "%Y-%m-%d").date()
        sprint_end = datetime.strptime(end_str, "%Y-%m-%d").date()
        return sprint_start, sprint_end
    except ValueError:
        return date(2026, 8, 10), date(2026, 8, 24)

# ==========================================
# VALIDATION LOGIC
# ==========================================
def validate_due_date(raw_due_date_input):
    """
    Parses natural language dates (e.g., "Monday", "tomorrow") and 
    validates if they fall within the active sprint.
    """
    try:
        # 1. Normalize the input into a pure Python 'date' object
        if isinstance(raw_due_date_input, datetime):
            due_date = raw_due_date_input.date()
            
        elif isinstance(raw_due_date_input, date):
            due_date = raw_due_date_input
            
        elif isinstance(raw_due_date_input, str):
            # --- THE FIX: Use dateparser to read human text offline ---
            # settings={'PREFER_DATES_FROM': 'future'} ensures "Monday" 
            # means *next* Monday, not the one in the past.
            parsed_datetime = dateparser.parse(
                str(raw_due_date_input), 
                settings={'PREFER_DATES_FROM': 'future'}
            )
            
            if not parsed_datetime:
                print(f"⚠️ Could not understand the date string: {raw_due_date_input}")
                return False
                
            due_date = parsed_datetime.date()
        else:
            return False

        # 2. Grab your dynamic sprint dates
        sprint_start, sprint_end = get_sprint_dates()
        
        # 3. Check if it falls within the window safely
        is_valid = sprint_start <= due_date <= sprint_end
        
        # We can return the clean date string so your UI can display it perfectly
        return {
            "clean_date": due_date.strftime("%Y-%m-%d"),
            "is_valid": is_valid
        }
        
    except Exception as e:
        print(f"⚠️ Date Validation Error: {e}")
        return {
            "clean_date": datetime.now().strftime("%Y-%m-%d"),
            "is_valid": False
        }