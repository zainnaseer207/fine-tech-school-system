from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Look up a value in a dict by key inside a Django template."""
    if not dictionary:
        return None
    return dictionary.get(key)