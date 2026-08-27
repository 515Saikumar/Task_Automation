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
    """
    Automatically calculates the current 2-week sprint window based on a fixed epoch.
    If SPRINT_START and SPRINT_END are provided in .env, they will override the auto-calculation.
    """
    from datetime import timedelta
    start_str = os.getenv("SPRINT_START")
    end_str = os.getenv("SPRINT_END")
    
    if start_str and end_str:
        try:
            sprint_start = datetime.strptime(start_str, "%Y-%m-%d").date()
            sprint_end = datetime.strptime(end_str, "%Y-%m-%d").date()
            return sprint_start, sprint_end
        except ValueError:
            pass
            
    # Auto-calculate perfectly synchronized 2-week sprints forever
    # Epoch: August 10, 2026 (A known Monday sprint start)
    epoch = date(2026, 8, 10)
    today = date.today()
    
    # Calculate how many 14-day cycles have passed since the epoch
    delta_days = (today - epoch).days
    cycles = max(0, delta_days // 14)
        
    sprint_start = epoch + timedelta(days=cycles * 14)
    sprint_end = sprint_start + timedelta(days=14)
    
    return sprint_start, sprint_end

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