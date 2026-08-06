from datetime import datetime

SPRINT_START = datetime(2026, 7, 15)
SPRINT_END = datetime(2026, 7, 30)

def validate_due_date(due_date):
    return SPRINT_START <= due_date <= SPRINT_END