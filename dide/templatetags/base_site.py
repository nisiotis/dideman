from django.template import Library
from dideman.dide.util.settings import SETTINGS

register = Library()


@register.simple_tag
def get_setting(name):
    return SETTINGS[name]
    

@register.simple_tag
def get_index(l, i):
    return l[i]
