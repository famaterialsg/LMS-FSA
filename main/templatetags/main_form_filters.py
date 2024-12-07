from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(value, css_class):
    return value.as_widget(attrs={'class': css_class})
@register.filter
def remove_list(value):
    if isinstance(value, str):
        return value.replace('list', '').strip()
    return value