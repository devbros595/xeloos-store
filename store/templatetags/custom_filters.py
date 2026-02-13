from django import template

register = template.Library()

@register.filter
def splitlines(value):
    """
    Splits the string by newline characters and returns a list.
    Usage in template: {{ value|splitlines }}
    """
    if not value:
        return []
    return value.splitlines()
