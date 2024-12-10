from django import template

register = template.Library()

@register.filter
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})
@register.filter
def replace_underscore(value):
    """Thay thế dấu gạch dưới (_) thành dấu cách ( )"""
    if isinstance(value, str):
        return value.replace('_', ' ')
    return value