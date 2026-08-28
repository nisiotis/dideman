from django.template import Library
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.contrib.admin.templatetags.admin_list import paginator_number
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

# Εδώ υπήρχαν τρία στοιβαγμένα inclusion_tag για την ίδια συνάρτηση. Κάθε
# κλήση καταχωρεί την ετικέτα με το ίδιο όνομα («submit_row»), οπότε μόνο η
# τελευταία που εφαρμόζεται —η πάνω-πάνω, administrativeleave— ίσχυε ποτέ. Οι
# άλλες δύο ήταν νεκρές: το permanentleave/submit_line.html είναι ολόιδιο με
# αυτό που χρησιμοποιείται, ενώ το nonpermanentleave/submit_line.html δεν
# υπάρχει καν στον δίσκο — αν άλλαζε η σειρά, η ετικέτα θα έσκαγε με
# TemplateDoesNotExist. Το πρότυπο είναι έτσι κι αλλιώς γενικό: το sub_url
# υπολογίζεται εδώ, στον χρόνο εκτέλεσης.
@register.inclusion_tag('admin/dide/administrativeleave/submit_line.html', takes_context=True)
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
    """Σύνδεσμος σελίδας που κρατάει τις παραμέτρους του querystring.

    Γράφτηκε επειδή το paginator_number του Django έχανε τις πολλαπλές
    τιμές των φίλτρων: το ChangeList.params ήταν dict(request.GET.items())
    και κρατούσε μία τιμή ανά παράμετρο. Σήμερα το filter_params είναι
    dict(request.GET.lists()) και το get_query_string κάνει urlencode με
    doseq=True, οπότε το ίδιο το Django τις διατηρεί.

    Έμεναν τρία σπασίματα σε αυτή την υλοποίηση:
    * το ChangeList δεν κρατά πια request (ούτε ποτέ το τεκμηρίωσε), οπότε
      το cl.request.GET σήκωνε AttributeError·
    * το cl.page_num μετράει από το 1 από το Django 3.0 και μετά, οπότε το
      i+1 έδειχνε λάθος αριθμό και το «τρέχουσα σελίδα» δεν ταίριαζε ποτέ·
    * το page_range δίνει paginator.ELLIPSIS («…») και όχι '.'.

    Αντί να ξαναγραφτούν και τα τρία, η ετικέτα παραπέμπει στο ίδιο το
    Django, που πλέον κάνει ακριβώς ό,τι χρειαζόταν.
    """
    return paginator_number(cl, i)
