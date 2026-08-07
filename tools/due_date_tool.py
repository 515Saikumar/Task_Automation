from datetime import datetime

# ==========================================
# SPRINT CONFIGURATION
# ==========================================
SPRINT_START = datetime(2026, 7, 15)
SPRINT_END = datetime(2026, 7, 30)

def validate_due_date(due_date_input):
    """
    Validates if a given date falls within the active sprint.
    Handles both raw strings and pre-formatted datetime objects safely.
    """
    try:
        # 1. If it's already a datetime object, convert it to string first 
        if isinstance(due_date_input, datetime):
            due_date_str = due_date_input.strftime("%Y-%m-%d")
        else:
            due_date_str = str(due_date_input)

        # 2. Convert cleanly back to a datetime object
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
        
        # 3. Check if it falls within the sprint window
        return SPRINT_START <= due_date <= SPRINT_END
        
    except ValueError:
        return False