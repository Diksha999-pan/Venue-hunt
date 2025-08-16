from django import template
from datetime import datetime

register = template.Library()

@register.filter
def split(value, arg):
    """
    Split a string by argument and return the first part
    """
    return value.split(arg)[0]
