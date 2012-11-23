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
            
@register.inclusion_tag('admin/dide/employeeleave/submit_line.html', takes_context=True)
def submit_row(context):
    """
    Displays the row of buttons for delete and save.
    """
    opts = context['opts']
    change = context['change']
    is_popup = context['is_popup']
    save_as = context['save_as']

    return {
        'onclick_attrib': (opts.get_ordered_objects() and change
                            and 'onclick="submitOrderForm();"' or ''),
        'show_delete_link': (not is_popup and context['has_delete_permission']
                              and (change or context['show_delete'])),
        'show_save_as_new': not is_popup and change and save_as,
        'show_save_and_add_another': context['has_add_permission'] and
                            not is_popup and (not save_as or context['add']),
        'show_save_and_continue': not is_popup and context['has_change_permission'],
        'is_popup': is_popup,
        'show_save': True,
        'show_print': not context['add'],
        'object_id': context['object_id'] if hasattr(context, 'object_id') else None,
        'form_id': opts.module_name + '_form',
    }

