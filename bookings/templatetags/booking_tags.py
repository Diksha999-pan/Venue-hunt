from django import template
from datetime import datetime, date

register = template.Library()

@register.filter
def split(value, arg):
    """
    Split a string by argument and return the first part
    """
    return value.split(arg)[0]

@register.filter
def subtract(value, arg):
    """
    Subtract the arg from the value
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def multiply(value, arg):
    """
    Multiply the value by the arg
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def days_until(event_date):
    """
    Return the number of days until the event date
    """
    if not event_date:
        return 0
        
    today = date.today()
    try:
        # Convert to date if it's a datetime
        if isinstance(event_date, datetime):
            event_date = event_date.date()
            
        # Calculate days until event
        delta = event_date - today
        return delta.days
    except (ValueError, TypeError):
        return 0
