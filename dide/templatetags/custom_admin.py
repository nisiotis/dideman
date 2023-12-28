from django.template import Library
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.contrib.admin.views.main import PAGE_VAR
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

@register.inclusion_tag('admin/dide/administrativeleave/submit_line.html', takes_context=True)
@register.inclusion_tag('admin/dide/permanentleave/submit_line.html', takes_context=True)
@register.inclusion_tag('admin/dide/nonpermanentleave/submit_line.html', takes_context=True)
def submit_row(context):
    """
    Displays the row of buttons for delete and save.
    """
    opts = context['opts']
    change = context['change']
    is_popup = context['is_popup']
    save_as = context['save_as']
    
    #if context['original'].__class__.__name__ == "NonPermanentLeave":
    if context['opts'].object_name == "PermanentLeave":
        sub_url = "permanentleave"
    elif context['opts'].object_name == "AdministrativeLeave":
        sub_url = "administrativeleave"
    else:
        sub_url = "nonpermanentleave"
    
    return {
        'sub_url': sub_url,
        'onclick_attrib': (change
                            and 'onclick="submitOrderForm();"' or ''),
        'show_delete_link': (not is_popup and context['has_delete_permission']
                              and (change or context.get('show_delete', True))),
        'show_save_as_new': not is_popup and change and save_as,
        'show_save_and_add_another': context['has_add_permission'] and
                            not is_popup and (not save_as or context['add']),
        'show_save_and_continue': not is_popup and context['has_change_permission'],
        'is_popup': is_popup,
        'show_save': True,
        'show_print': not context['add'],
        'object_id': context['object_id'] if 'object_id' in context else None,
        'form_id': opts.model_name + '_form'
    }


@register.simple_tag
def paginator_number_with_qs_params(cl, i):
    """
    Generates an individual page index link in a paginated list.
    """
    if i == '.':
        return u'... '
    elif i == cl.page_num:
        return mark_safe(u'<span class="this-page">%d</span> ' % (i+1))
    else:
        qd = cl.request.GET.copy()
        qd[PAGE_VAR] = i;
        return u'<a href="?%s"%s>%d</a> ' % (qd.urlencode(), (i == cl.paginator.num_pages-1 and ' class="end"' or ''), i+1)
