from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Fetches a value from a dictionary by its key."""
    try:
        return dictionary.get(key, None)
    except AttributeError:
        return None
