from django.template import Library

register = Library()


@register.filter('render_full_filter_select')
def render_full_filter_select(select, name):
    return select.render(name=name, value='')
