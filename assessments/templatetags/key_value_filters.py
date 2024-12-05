from django import template

register = template.Library()

@register.filter
def get_value_from_dict(dictionary, key):
    """
    Custom template filter to get a value from a dictionary using a key.
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, None)
    return None