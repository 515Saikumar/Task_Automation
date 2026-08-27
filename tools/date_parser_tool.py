import dateparser
from datetime import datetime, timedelta

def normalize_date(date_text):
    if not date_text:
        return "Not Specified"

    date_text = date_text.lower()
    today = datetime.today()

    # Quick manual overrides for speed and reliability
    if "tomorrow" in date_text:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    if "next week" in date_text:
        return (today + timedelta(days=7)).strftime("%Y-%m-%d")
    if "today" in date_text:
        return today.strftime("%Y-%m-%d")

    # Support all days of the week dynamically!
    weekdays = {
        "monday": 0, "tuesday": 1, "wednesday": 2, 
        "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
    }
    
    for day_name, day_idx in weekdays.items():
        if day_name in date_text:
            days_ahead = day_idx - today.weekday()
            if days_ahead <= 0: # Target is next week
                days_ahead += 7
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    # If no basic keywords match, use dateparser's powerful search 
    # to extract things like "in 3 days", "Oct 12th", etc.
    try:
        from dateparser.search import search_dates
        found_dates = search_dates(date_text, settings={'PREFER_DATES_FROM': 'future'})
        if found_dates:
            # found_dates is a list of tuples: [('in 3 days', datetime.datetime(...))]
            return found_dates[0][1].strftime("%Y-%m-%d")
    except Exception:
        pass

    # Return the original text if no date could be found
    return date_text