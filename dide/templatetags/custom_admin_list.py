from django.template import Library

register = Library()


@register.inclusion_tag('admin/filter.html')
def admin_list_filter(cl, spec):
    if hasattr(spec, 'list_filter_context'):
        dic = spec.list_filter_context(cl)
    else:
        dic = {'title': spec.title, 'choices': list(spec.choices(cl))}
    return dic


@register.filter('is_free_date_filter')
def is_free_date_filter(spec):
    return spec.template_name == 'free_date_filter'


@register.inclusion_tag('admin/free_date_filter.html')
def free_date_filter(cl, spec):
    return {'title': spec.title, 'url_from_value': spec.url_from_value,
            'url_to_value': spec.url_to_value,
            'parameter_name': spec.parameter_name, 'cl': cl}
