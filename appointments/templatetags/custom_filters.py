from django import template

register = template.Library()

@register.filter
def format_time(value):
    try:
        hours, minutes = map(int, value.split(':'))
        period = "AM" if hours < 12 else "PM"
        hours = hours % 12 or 12
        return f"{hours}:{minutes:02d} {period}"
    except:
        return value

@register.filter
def star_range(value):
    try:
        return range(int(value))
    except (ValueError, TypeError):
        return range(0)

@register.filter
def get_attr(obj, attr_name):
    """
    Template filter to get an attribute of an object dynamically.
    """
    return getattr(obj, attr_name, None)