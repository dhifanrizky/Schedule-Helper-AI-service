from langchain.tools import tool

from app.services import calendar

calendar = calendar.CalendarService()

@tool
def fetch_calendar_by_date(target_date: str):
    """
    Retrieve calendar events on a specific date.

    Args:
        target_date (str): Date in YYYY-MM-DD format

    Returns:
        A formatted list of calendar events on the specified date.
    """
    return calendar.fetch_calendar_by_date(target_date=target_date)

@tool
def fetch_calendar_by_range(back: int, ahead: int):
    """
    Retrieve calendar events within a time range relative to the current date.

    Args:
        back (int): Number of days before today to include
        ahead (int): Number of days after today to include

    Returns:
        A formatted list of calendar events within the specified range.
    """
    return calendar.fetch_calendar_by_range(days_back=back, days_ahead=ahead)

