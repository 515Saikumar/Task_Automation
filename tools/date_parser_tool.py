from datetime import datetime, timedelta


def normalize_date(date_text):

    today = datetime.today()

    # Handle missing dates
    if not date_text:
        return "Not Specified"


    date_text = date_text.lower()


    if "tomorrow" in date_text:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")


    if "friday" in date_text:

        days_ahead = 4 - today.weekday()

        if days_ahead <= 0:
            days_ahead += 7

        return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")


    if "monday" in date_text:

        days_ahead = 0 - today.weekday()

        if days_ahead <= 0:
            days_ahead += 7

        return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")


    if "next week" in date_text:
        return (today + timedelta(days=7)).strftime("%Y-%m-%d")


    return date_text