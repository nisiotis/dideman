# -*- coding: utf-8 -*-
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from dideman.dide.models import Profession, TransferArea, Employee, NonPermanent, Permanent, School, Placement, Administrative
from dideman.private_teachers.models import PrivateTeacher
from dideman.dide.util.settings import SETTINGS
from django import VERSION as djangoversion
from django.utils.translation import gettext as _
from django.utils.text import capfirst
from django.views.decorators.cache import never_cache
from django.utils.cache import add_never_cache_headers
from django.db.models import Q
from django.urls import reverse, NoReverseMatch
from django.core.exceptions import PermissionDenied
from dideman.lib.common import without_accented
from dideman.dide.util.encoding import (ENCODING_CHOICES, DEFAULT_ENCODING,
                                        clean_encoding, charset_name,
                                        bom_for, encode as encode_text)
from io import StringIO
from urllib.parse import urlencode
import csv
import json
import datetime, base64
import os
import xlrd


def identity_key(lastname, firstname, fathername, profession_id):
    """The combination that in practice identifies one person.

    Names are compared case-insensitively, without surrounding
    whitespace and without tonos, so that 'ΆΝΝΑ' and 'ΑΝΝΑ ' count as
    the same person.
    """
    def norm(v):
        return without_accented(str(v if v is not None else '').strip().upper())
    return (norm(lastname), norm(firstname), norm(fathername), norm(profession_id))


def find_duplicates():
    """Permanent/NonPermanent pairs that look like the same person.

    Grouped by identity key rather than compared pairwise, so this is
    linear in the number of employees instead of quadratic.
    """
    permanents = {}
    for p in Permanent.objects.all():
        permanents.setdefault(
            identity_key(p.lastname, p.firstname, p.fathername, p.profession_id),
            []).append(p)

    l = []
    r = 0
    for n in NonPermanent.objects.exclude(vat_number=None):
        key = identity_key(n.lastname, n.firstname, n.fathername, n.profession_id)
        for p in permanents.get(key, []):
            l.append(p)
            r += 1
            l.append(n)

    return l, r

SEARCH_PAGE_SIZE = 25


def elided_page_range(paginator, number, on_each_side=3, on_ends=2):
    """Page numbers around the current one, 0 marking an elision.

    Same shape as the paginator the Django admin change list draws. The
    gap marker is 0 rather than None because the template compares it,
    and page numbers start at 1 so 0 is unambiguous.
    """
    num_pages = paginator.num_pages
    if num_pages <= (on_each_side + on_ends) * 2:
        return list(paginator.page_range)

    page_range = []
    if number > (on_each_side + on_ends + 1):
        page_range.extend(list(range(1, on_ends + 1)))
        page_range.append(0)
        page_range.extend(list(range(number - on_each_side, number + 1)))
    else:
        page_range.extend(list(range(1, number + 1)))

    if number < (num_pages - on_each_side - on_ends):
        page_range.extend(list(range(number + 1, number + on_each_side + 1)))
        page_range.append(0)
        page_range.extend(list(range(num_pages - on_ends + 1, num_pages + 1)))
    else:
        page_range.extend(list(range(number + 1, num_pages + 1)))
    return page_range


def search_query_string(q, category):
    """The q/cat pair that every pagination link has to carry along."""
    params = [('q', q or '')]
    if category:
        params.append(('cat', category))
    return urlencode(params)


def search_result_details(label, o):
    """Flatten one hit into the values the results table shows.

    The four employee models carry different fields, so everything is
    read defensively: an attribute that does not exist on this category
    simply comes back empty instead of breaking the whole page.
    """
    def attr(name, default=''):
        try:
            v = getattr(o, name)
            if callable(v):
                v = v()
        except Exception:
            return default
        return default if v is None else v

    pk = attr('parent_id', None) or o.pk
    app_label = attr('app_label', None)
    object_name = attr('object_name', None)

    # Μόνιμοι/Διοικητικοί έχουν Αρ. Μητρώου, ιδιωτικοί Αρ. Επετηρίδας.
    number = attr('registration_number') or attr('series_number')

    if attr('currently_serves', None) is not None:
        status = 'Υπηρετεί' if attr('currently_serves') else 'Δεν υπηρετεί'
    elif attr('active', None) is not None:
        status = 'Ενεργός' if attr('active') else 'Ανενεργός'
    else:
        status = ''

    return {
        'category': label,
        'id': pk,
        'url': admin_change_url(app_label, object_name.lower(), pk)
               if app_label and object_name else None,
        'lastname': attr('lastname'),
        'firstname': attr('firstname'),
        'fathername': attr('fathername'),
        'profession': attr('profession'),
        'profession_description': attr('profession_description'),
        'number': number,
        'vat_number': attr('vat_number'),
        'amka': attr('social_security_registration_number'),
        'organization': attr('organization_serving'),
        'employment_type': attr('type'),
        'telephone': attr('telephone_number1'),
        'email': attr('email'),
        'date_modified': attr('date_modified', None),
        'status': status,
    }


def search_groups(q, search_model, today, active_nonpermanents, duplicates):
    """Return [(category label, results)] for a search box query."""
    groups = []
    if q == '/photo':
        for model in search_model:
            if model.__name__ in ("Permanent", "NonPermanent", "Administrative"):
                groups.append((model._meta.verbose_name,
                               model.objects.exclude(photo__exact='')
                                            .exclude(photo__isnull=True)))
    elif q == '/nonpermanent':
        groups.append(('Ενεργοί αναπληρωτές', active_nonpermanents))
    elif q == '/dublicates':
        groups.append(('Διπλές Εγγραφές', duplicates))
    elif q == '/lastedit':
        for model in search_model:
            if model.__name__ in ("Permanent", "NonPermanent",
                                  "Administrative", "PrivateTeacher"):
                groups.append((model._meta.verbose_name,
                               model.objects.filter(
                                   date_modified__year=today.year,
                                   date_modified__month=today.month,
                                   date_modified__day=today.day)))
    else:
        for model in search_model:
            if model.__name__ == "Permanent":
                groups.append((model._meta.verbose_name,
                               model.objects.filter(
                                   Q(lastname__istartswith=q.upper()) |
                                   Q(vat_number__istartswith=q) |
                                   Q(registration_number__istartswith=q))))
            elif model.__name__ in ("NonPermanent", "Administrative",
                                    "PrivateTeacher"):
                groups.append((model._meta.verbose_name,
                               model.objects.filter(
                                   Q(lastname__istartswith=q.upper()) |
                                   Q(vat_number__istartswith=q))))
    return groups


# Οι κατηγορίες προσωπικού που εμφανίζονται πρώτες στη λίστα της
# Διεύθυνσης, με το εικονίδιο της καθεμιάς: (σειρά, όνομα εικονιδίου).
# Χρησιμοποιείται μόνο για ταξινόμηση και εμφάνιση -- τα δικαιώματα
# ελέγχονται όπως πριν, οπότε ό,τι δεν επιτρέπεται στον χρήστη δεν
# μπαίνει καν στη λίστα για να προωθηθεί.
FEATURED_MODELS = {
    ('dide', 'permanent'): (0, 'permanent'),
    ('dide', 'nonpermanent'): (1, 'nonpermanent'),
    ('dide', 'administrative'): (2, 'administrative'),
}
UNFEATURED_ORDER = 99

# Εικονίδια για μοντέλα που δεν προωθούνται στην κορυφή της λίστας. Το
# εικονίδιο είναι ανεξάρτητο από τη σειρά: οι τρεις κατηγορίες αδειών
# κρατούν την αλφαβητική τους θέση και απλώς αποκτούν σήμα, κοινό και για
# τις τρεις.
MODEL_ICONS = {
    ('dide', 'permanentleave'): 'leave',
    ('dide', 'nonpermanentleave'): 'leave',
    ('dide', 'administrativeleave'): 'leave',
}

# Εργαλεία που δεν είναι πραγματικά μοντέλα προς περιήγηση αλλά όψεις
# διαχείρισης (proxy models με δική τους διαδρομή στο urls.py). Βγαίνουν
# από τη λίστα μοντέλων και εμφανίζονται ως σύνδεσμοι στο πλαϊνό πλαίσιο.
# Τα δικαιώματα ελέγχονται ακριβώς όπως πριν: ό,τι δεν επιτρέπεται στον
# χρήστη δεν φτάνει καν εδώ.
ADMIN_TOOLS = {
    ('dide', 'importexport'): '/admin/dide/importexport/',
    ('dide', 'geoschool'): '/admin/dide/geoschool/',
}


# Χωρίς @never_cache: η συνάρτηση εγκαθίσταται ως μέθοδος του AdminSite,
# οπότε ο decorator θα έβλεπε το self στη θέση του request. Το AdminSite
# την τυλίγει ήδη με admin_view(cacheable=False), που εφαρμόζει never_cache.
def index(self, request, extra_context=None):
    """
    Displays the main admin index page, which lists all of the installed
    apps that have been registered in this site. Added a search field, used monkey-patch 
    to overide the default index
    """
    app_dict = {}
    search_model = []
    admin_tools = []
    user = request.user
    tot_pho = None
    tot_day_mod = None
    is_super = None
    today = datetime.date.today()
    if user.is_superuser:
        is_super = True
        tot_pho = Employee.objects.exclude(photo__exact='').exclude(photo__isnull=True).count()
        tot_day_mod = Employee.objects.filter(date_modified__year=today.year,
                                                date_modified__month=today.month,
                                                date_modified__day=today.day).count()
    for model, model_admin in list(self._registry.items()):
        if model._meta.app_label == "dide":
            app_label = model._meta.app_label
            app_text = "Διεύθυνση"
        elif model._meta.app_label == "auth":
            app_label = model._meta.app_label
            app_text = "Χρήστες"
        elif model._meta.app_label == "private_teachers":
            app_label = model._meta.app_label
            app_text = "Ιδιωτικά Σχολεία"
        else:
            app_text = model._meta.app_label
            app_label = model._meta.app_label

        has_module_perms = user.has_module_perms(app_label)
        if has_module_perms:
            perms = model_admin.get_model_perms(request)

            # Check whether user has any perm for this module.
            # If so, add the module to the model_list.
            if True in list(perms.values()):
                info = (app_label, model._meta.model_name)
                search_model.append(model)
                if info in ADMIN_TOOLS:
                    admin_tools.append({
                        'name': capfirst(model._meta.verbose_name_plural),
                        'url': ADMIN_TOOLS[info],
                    })
                    continue
                featured = FEATURED_MODELS.get(info)
                model_dict = {
                    'name': capfirst(model._meta.verbose_name_plural),
                    # Το app_list.html φτιάχνει από αυτό την κλάση της
                    # γραμμής («model-permanent»). Έλειπε από το δικό μας
                    # context, οπότε κάθε γραμμή έβγαινε ως σκέτο
                    # class="model-" και χανόταν και η σήμανση current-model.
                    'object_name': model._meta.object_name,
                    'perms': perms,
                    'order': featured[0] if featured else UNFEATURED_ORDER,
                    'icon': featured[1] if featured else MODEL_ICONS.get(info),
                    'featured': bool(featured),
                }

                
                if perms.get('change', False):
                    try:
                        model_dict['admin_url'] = reverse('admin:%s_%s_changelist' % info, current_app=self.name)
                    except NoReverseMatch:
                        pass
                if perms.get('add', False) and model._meta.managed == True:
                    try:
                        model_dict['add_url'] = reverse('admin:%s_%s_add' % info, current_app=self.name)
                    except NoReverseMatch:
                        pass
                if app_label in app_dict:
                    app_dict[app_label]['models'].append(model_dict)
                else:
                    app_dict[app_label] = {
                        'name': app_text,
                        'has_module_perms': has_module_perms,
                        'models': [model_dict],
                    }

    # Sort the apps alphabetically.
    app_list = list(app_dict.values())
    app_list.sort(key=lambda x: x['name'])

    # Sort the models alphabetically within each app, with the featured
    # staff categories pulled to the top in their own order.
    for app in app_list:
        app['models'].sort(key=lambda x: (x.get('order', UNFEATURED_ORDER),
                                          x['name']))

    tot_perm = Permanent.objects.filter(currently_serves=1).count()

    y1 = datetime.date.today().year if datetime.date.today().month > 8 and datetime.date.today().month <= 12 else datetime.date.today().year - 1
    y2 = datetime.date.today().year if datetime.date.today().month >= 1 and datetime.date.today().month < 9 else datetime.date.today().year + 1

    tot_non = NonPermanent.objects.substitutes_in_date_range(date_from='%d-09-01' % y1, date_to='%d-08-31' % y2) 

    tot_priv = PrivateTeacher.objects.filter(active__exact=1).count()

    tot_admin = Administrative.objects.filter(currently_serves=1).count()
    dbls, l = find_duplicates()
    # Από το Django 2.0 και μετά τα βασικά πρότυπα του admin περιμένουν
    # όσα βάζει το each_context() (log_entries, available_apps, δικαιώματα
    # κ.λπ.), οπότε το δικό μας context χτίζεται πάνω σε αυτό.
    context = dict(self.each_context(request))
    context.update({
        'title': _('Site administration'),
        'app_list': app_list,
        'total_permanent': '%d' % tot_perm,
        'total_nonpermanent': '%d' % tot_non.count(),
        'total_private': '%d' % tot_priv,
        'total_administrative': '%d' % tot_admin,
        'yf': y1,
        'yt': y2,
        'is_super': is_super,
        'photo_total': tot_pho,
        'today_mod_total': tot_day_mod,
        # Σκέτη η έκδοση: το υποσέλιδο γράφει ήδη τη λέξη «Django» πριν από
        # αυτήν, οπότε το πρόθεμα εδώ έβγαζε «Django Django 5.2.17».
        'django_version': '.'.join(str(i) for i in djangoversion[:3]),
        'total_dbl': l,
        'admin_tools': sorted(admin_tools, key=lambda t: t['name']),
    })
    context.update(extra_context or {})
    # Το κουτί αναζήτησης υποβάλλει με POST· οι σύνδεσμοι σελιδοποίησης
    # ξαναζητούν την ίδια αναζήτηση με GET.
    q = (request.POST.get('q') if request.method == 'POST'
         else request.GET.get('q'))
    if q is not None:
        q = q.strip()
        groups = search_groups(q, search_model, today, tot_non, dbls) if q else []

        rows = []
        counts = []
        for label, found in groups:
            found = list(found)
            if found:
                counts.append({'label': label, 'count': len(found)})
            rows.extend([(label, o) for o in found])

        total_results = len(rows)

        # Περιορισμός σε μία κατηγορία, από τους συνδέσμους της σύνοψης.
        category = request.GET.get('cat', '')
        if category:
            rows = [r for r in rows if r[0] == category]

        rows.sort(key=lambda r: (getattr(r[1], 'lastname', '') or '',
                                 getattr(r[1], 'firstname', '') or ''))

        paginator = Paginator(rows, SEARCH_PAGE_SIZE)
        try:
            page = paginator.page(request.GET.get('page'))
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        # Τα στοιχεία κάθε γραμμής υπολογίζονται μόνο για την τρέχουσα
        # σελίδα: το organization_serving() κοστίζει ερωτήματα ανά εγγραφή.
        context = dict(self.each_context(request))
        context.update({
            'title': _('Search'),
            'q': q,
            't': total_results,
            'shown': len(rows),
            'category': category,
            'counts': counts,
            'page': page,
            'paginator': paginator,
            'page_numbers': elided_page_range(paginator, page.number),
            'base_query': search_query_string(q, category),
            'results': [search_result_details(label, o) for label, o in page],
        })

        context.update(extra_context or {})
        return TemplateResponse(request, 'admin/search.html', context)
    else:
        return TemplateResponse(request, self.index_template or
                            'admin/index.html', context)


@csrf_protect
@staff_member_required
def photo_update(request, emp_id):
    e = Employee.objects.get(id=emp_id)
    if request.POST:
        if 'photo' in request._files:
            e.photo = base64.b64encode(request._files['photo'].read())
            e.photo_type = request._files['photo'].name.split(".")[-1]
            e.save()
            return HttpResponse()
        else:
            e.photo = ''
            e.photo_type = ''
            e.save()
            messages.info(request, 'Η φωτογραφία διαγράφηκε.')
    if 'saved' in request.GET:
        messages.info(request, 'Η φωτογραφία ενημερώθηκε.')
    context = {
        "emp": e,
        "dide_place": SETTINGS['dide_place'],
        "errors": [],
    }
    return render(request, 'admin/photo.html', context)


@csrf_protect
@staff_member_required
def photo(request, emp_id):
    emp = Employee.objects.get(id=emp_id)
    # Το b64decode επιστρέφει bytes: δεν χωρούν σε StringIO και δεν
    # χρειάζεται ενδιάμεσος buffer.
    return HttpResponse(base64.b64decode(emp.photo),
                        content_type='image/%s' % emp.photo_type)


@csrf_protect
@staff_member_required
def nonpermanent_list(request):
    np = NonPermanent.objects.all()
    context = {
        "set": np,
        "dide_place": SETTINGS['dide_place'],
        "errors": [],
    }
    r = render(request, 'admin/nonpermanent_list.html', context)
    return HttpResponse(r)


# Import/Export: only offer models that make sense to bulk-create from
# a spreadsheet, plus their common ancestor and siblings for reporting.
IMPORT_MODELS = [('Permanent', Permanent), ('NonPermanent', NonPermanent)]
EXPORT_MODELS = [('Employee', Employee), ('Permanent', Permanent),
                 ('NonPermanent', NonPermanent), ('Administrative', Administrative)]


def _model_choices(models):
    return [(key, model._meta.verbose_name) for key, model in models]


def _import_model(name):
    return dict(IMPORT_MODELS).get(name, Permanent)


def _normalize_vat_number(value):
    """Normalize a raw xls cell value into a 9-digit Α.Φ.Μ. (VAT number)
    string.

    xlrd reads any numeric-looking cell as a Python float, so by the time
    a vat_number cell has round-tripped through the upload/save/final
    form stages it usually looks like u'123456789.0'; a genuinely textual
    cell may also carry stray whitespace or punctuation. Take the digits
    only -- via int(float(...)) when that parses, otherwise by filtering
    non-digit characters out -- and zero-pad on the left to the standard
    9 characters, since a real Α.Φ.Μ. that starts with a zero loses it
    once Excel treats the cell as a number.

    Returns None if no digits could be recovered at all.
    """
    if value is None:
        return None
    try:
        digits = str(int(float(value)))
    except (TypeError, ValueError):
        digits = ''.join(ch for ch in str(value) if ch.isdigit())
    if not digits:
        return None
    return digits.zfill(9)[:9]


def _fill_required_defaults(obj):
    """Supply values for NOT NULL columns the spreadsheet did not map.

    Django initialises a new instance with each field's default, so a
    field only stays None here if it genuinely has no usable value. Two
    cases matter: fields declared NOT NULL but with an explicit
    default=None (NonPermanent.pedagogical_sufficiency, Employee.photo)
    would otherwise make every insert fail with an IntegrityError, so
    substitute an empty value of the right type. Foreign keys cannot be
    invented, so their verbose names are returned for the caller to
    report as an error.
    """
    missing = []
    for f in obj._meta.fields:
        if f.primary_key or getattr(f, 'auto_now', False) \
                or getattr(f, 'auto_now_add', False):
            continue
        if f.null or getattr(obj, f.attname, None) is not None:
            continue
        default = f.get_default() if f.has_default() else None
        if default is not None:
            setattr(obj, f.attname, default)
        elif getattr(f, 'rel', None) is not None:
            missing.append(str(f.verbose_name))
        elif f.get_internal_type() == "BooleanField":
            setattr(obj, f.attname, False)
        elif f.get_internal_type() in ("CharField", "TextField"):
            setattr(obj, f.attname, '')
    return missing


def _coerce_value(mf, field_name, raw_value):
    """Μετατρέπει ένα κελί του φύλλου σε τιμή πεδίου του μοντέλου.

    Επιστρέφει (ok, value, warning): ok=False όταν η τιμή δεν μπόρεσε να
    μετατραπεί, οπότε το warning λέει γιατί. Την ίδια συνάρτηση
    χρησιμοποιούν και η εισαγωγή και η ενημέρωση, ώστε να μη διαφωνούν
    ποτέ για το τι σημαίνει μια τιμή του αρχείου.
    """
    if field_name not in mf:
        return False, None, "%s: άγνωστο πεδίο" % field_name

    kind = mf[field_name]

    if field_name == 'vat_number':
        vat = _normalize_vat_number(raw_value)
        if vat:
            return True, vat, None
        return False, None, "%s: μη έγκυρη τιμή '%s'" % (field_name, raw_value)

    if kind == "ForeignKey":
        if field_name in ("profession", "second_profession"):
            try:
                return True, Profession.objects.get(pk=str(raw_value)), None
            except Exception:
                return False, None, \
                    "%s: δεν βρέθηκε η τιμή '%s'" % (field_name, raw_value)
        if field_name == "transfer_area":
            try:
                return True, TransferArea.objects.filter(
                    name__istartswith=str(raw_value)[:1])[0], None
            except Exception:
                return False, None, \
                    "%s: δεν βρέθηκε η τιμή '%s'" % (field_name, raw_value)
        try:
            return True, int(raw_value), None
        except Exception:
            return False, None, \
                "%s: μη έγκυρη τιμή '%s'" % (field_name, raw_value)

    if kind in ("DateField", "DateTimeField"):
        # Το _read_xls δίνει ήδη ISO για κελιά με μορφή ημερομηνίας· εδώ
        # καλύπτονται τα κελιά που ήταν απλό κείμενο.
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y'):
            try:
                return True, datetime.datetime.strptime(
                    raw_value.strip(), fmt).date(), None
            except ValueError:
                continue
        return False, None, \
            "%s: μη έγκυρη ημερομηνία '%s'" % (field_name, raw_value)

    if kind in ("IntegerField", "OneToOneField"):
        try:
            # Το xlrd δίνει τους αριθμούς ως float, οπότε το «900001»
            # φτάνει εδώ ως «900001.0»· κρατώντας μόνο τα ψηφία έβγαινε
            # 9000010. Κόβεται πρώτα το δεκαδικό μέρος.
            text = str(raw_value).strip().split('.')[0]
            # Το φιλτράρισμα των ψηφίων πετάει και το πρόσημο: το «-42»
            # γινόταν σιωπηλά 42. Κρατιέται ξεχωριστά.
            negative = text.startswith('-')
            digits = ''.join(v for v in text if v.isdigit())
            value = int(digits)
            return True, -value if negative else value, None
        except Exception:
            return False, None, \
                "%s: μη έγκυρη τιμή '%s'" % (field_name, raw_value)

    if kind in ("BooleanField", "NullBooleanField"):
        try:
            return True, bool(int(raw_value[:1])), None
        except Exception:
            return False, None, \
                "%s: μη έγκυρη τιμή '%s'" % (field_name, raw_value)

    return True, raw_value, None


def _build_import_record(model, mf, pairs):
    """Build one unsaved instance of `model` from a row of the spreadsheet.

    `pairs` is a sequence of (field_name, raw_value) for the columns the
    operator mapped. Returns (instance, warnings); warnings names any
    column whose value could not be applied, so the row can still be
    saved on the strength of its remaining fields and the operator can
    see what was dropped.
    """
    p = model()
    warnings = []
    for field_name, raw_value in pairs:
        if not field_name or not raw_value:
            continue
        ok, value, warning = _coerce_value(mf, field_name, raw_value)
        if warning:
            warnings.append(warning)
        if ok:
            setattr(p, field_name, value)
    return p, warnings


IMPORT_WIZARD_KEY = 'importexport_wizard'


def _wizard_rows(request):
    """Τα δεδομένα του αρχείου που μεταφορτώθηκε, από τη συνεδρία.

    Τα κελιά κρατιούνται στη συνεδρία αντί να ταξιδεύουν μπρος-πίσω ως
    κρυφά πεδία της φόρμας. Ένα αρχείο 30 στηλών επί 40 γραμμές παρήγαγε
    πάνω από 1.200 πεδία ανά υποβολή, δηλαδή περισσότερα από το όριο
    settings.DATA_UPLOAD_MAX_NUMBER_FIELDS (1.000) που εισήγαγε το Django
    1.10: ο οδηγός τερμάτιζε με σκέτο «400 Bad Request» σε κάθε αρχείο
    ρεαλιστικού μεγέθους. Τώρα υποβάλλονται μόνο η αντιστοίχιση των
    στηλών και οι επιλογές των γραμμών.
    """
    return request.session.get(IMPORT_WIZARD_KEY) or {}


def _xls_cell(worksheet, datemode, r, c):
    """Ένα κελί ως συμβολοσειρά, με τη μορφή που περιμένει το μοντέλο.

    Το xlrd δίνει κάθε αριθμητικό κελί ως float: το «900001» έφτανε ως
    «900001.0» και η ημερομηνία ως «29465.0». Έτσι οι ακέραιοι έβγαιναν
    δεκαπλάσιοι (κρατώντας μόνο τα ψηφία) και οι ημερομηνίες ήταν
    αδιάβαστες. Εδώ ο ακέραιος γράφεται χωρίς δεκαδικά και η ημερομηνία
    σε ISO.
    """
    kind = worksheet.cell_type(r, c)
    value = worksheet.cell_value(r, c)

    if kind == xlrd.XL_CELL_DATE:
        try:
            y, mo, d, h, mi, sec = xlrd.xldate_as_tuple(value, datemode)
            if (y, mo, d) != (0, 0, 0):
                return '%04d-%02d-%02d' % (y, mo, d)
            return '%02d:%02d:%02d' % (h, mi, sec)
        except Exception:
            return str(value)

    if kind == xlrd.XL_CELL_NUMBER:
        return str(int(value)) if float(value).is_integer() else str(value)

    if kind == xlrd.XL_CELL_BOOLEAN:
        return '1' if value else '0'

    if kind in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK):
        return ''

    return str(value)


def _read_xls(uploaded):
    """Το πρώτο φύλλο του αρχείου ως λίστα από λίστες συμβολοσειρών."""
    workbook = xlrd.open_workbook(file_contents=uploaded.read())
    worksheet = workbook.sheet_by_index(0)
    datemode = workbook.datemode
    return [[_xls_cell(worksheet, datemode, r, c)
             for c in range(worksheet.ncols)]
            for r in range(1, worksheet.nrows)]


@csrf_protect
@staff_member_required
def import_export_view(request):
    wizard = _wizard_rows(request)
    import_model_name = request.POST.get(
        'import_model', wizard.get('model', 'Permanent'))
    model = _import_model(import_model_name)

    context = {
        "title": 'Εισαγωγή - Εξαγωγή Δεδομένων',
        "opts": [],
        "form": [],
        "app_label": 'Εισαγωγή - Εξαγωγή Δεδομένων',
        "errors": [],
        "import_model": import_model_name,
        "import_model_label": model._meta.verbose_name,
        "import_model_choices": _model_choices(IMPORT_MODELS),
    }

    if request.method != 'POST':
        request.session.pop(IMPORT_WIZARD_KEY, None)
        return render(request, 'admin/importexport.html', context)

    # --- βήμα 1: μεταφόρτωση του αρχείου ---------------------------------
    if "upload" in request.GET:
        uploaded = request.FILES.get('xls_upload')
        if not uploaded:
            context["errors"] = ['Επιλέξτε αρχείο προς μεταφόρτωση.']
            return render(request, 'admin/importexport.html', context)
        try:
            rows = _read_xls(uploaded)
        except Exception as ex:
            context["errors"] = [
                'Το αρχείο δεν διαβάστηκε ως βιβλίο Excel (.xls): %s' % ex]
            return render(request, 'admin/importexport.html', context)
        if not rows:
            context["errors"] = ['Το πρώτο φύλλο του αρχείου δεν έχει δεδομένα.']
            return render(request, 'admin/importexport.html', context)

        request.session[IMPORT_WIZARD_KEY] = {
            'model': import_model_name,
            'file': uploaded.name,
            'rows': rows,
        }
        context.update({
            "import_file": uploaded.name,
            "fields": [x.name for x in model._meta.fields],
            "cols": list(range(len(rows[0]))),
            "data": rows,
        })
        return render(request, 'admin/importexport.html', context)

    rows = wizard.get('rows')
    if not rows:
        context["errors"] = [
            'Η συνεδρία έληξε ή δεν έχει μεταφορτωθεί αρχείο. '
            'Ξεκινήστε ξανά από τη μεταφόρτωση.']
        return render(request, 'admin/importexport.html', context)

    # --- βήμα 2: αντιστοίχιση στηλών και επιλογή γραμμών -----------------
    if "save" in request.GET:
        ncols = len(rows[0])
        # Οι στήλες που ο χειριστής αντιστοίχισε σε πεδίο του μοντέλου,
        # με τη σειρά που εμφανίζονται στο αρχείο.
        mapping = [(c, request.POST.get('field_%d' % c, '').strip())
                   for c in range(ncols)]
        mapping = [(c, name) for c, name in mapping if name]

        selected = [i for i in range(len(rows))
                    if 'check_%d' % i in request.POST]

        chosen = []
        dbl = 0
        for i in selected:
            values = [rows[i][c].strip() for c, _ in mapping]
            vat = _normalize_vat_number(rows[i][0]) if rows[i] else None
            found = ''
            if vat:
                match = Employee.objects.filter(vat_number=vat).first()
                if match:
                    found = match.vat_number
                    dbl += 1
            chosen.append({'row': i, 'values': values, 'found': found})

        request.session[IMPORT_WIZARD_KEY] = dict(
            wizard, mapping=mapping, selected=selected)

        context.update({
            "dataselected": chosen,
            "dublicates": dbl,
            "imported_file": wizard.get('file', ''),
            "field_titles": [name for _, name in mapping],
        })
        return render(request, 'admin/importexport.html', context)

    # --- βήμα 3: οριστικοποίηση ------------------------------------------
    if "final" in request.GET:
        mapping = [tuple(m) for m in wizard.get('mapping', [])]
        selected = wizard.get('selected', [])
        mf = {x.name: x.get_internal_type() for x in model._meta.fields}
        saved, notins, foundins = [], [], []

        for k, i in enumerate(selected):
            if request.POST.get('select_%d' % k, '0') != '0':
                continue

            pairs = [(name, rows[i][c].strip()) for c, name in mapping]
            p, warnings = _build_import_record(model, mf, pairs)
            # reported back to the template per row
            p.import_error = ''
            p.import_warnings = warnings

            missing = _fill_required_defaults(p)
            if missing:
                p.import_error = 'Λείπουν υποχρεωτικά πεδία: %s' % \
                    ', '.join(missing)
                notins.append(p)
                continue

            # An employee already holding this Α.Φ.Μ. means the row is a
            # duplicate: skip it and say which record it clashed with,
            # rather than creating a second entry for the same person.
            # Checked against the database at save time, so a record added
            # since the file was uploaded is still caught.
            vat = getattr(p, 'vat_number', None)
            if vat:
                existing = Employee.objects.filter(vat_number=vat).first()
                if existing:
                    p.import_error = \
                        'Υπάρχει ήδη εγγραφή με Α.Φ.Μ. %s: %s' % (vat, existing)
                    foundins.append(p)
                    continue

            try:
                p.save()
                saved.append(p)
            except Exception as ex:
                p.import_error = str(ex)
                notins.append(p)

        request.session.pop(IMPORT_WIZARD_KEY, None)
        context.update({
            "dataimported": saved,
            "notinserted": notins,
            "foundinserted": foundins,
        })

    return render(request, 'admin/importexport.html', context)


UPDATE_WIZARD_KEY = 'importupdate_wizard'

# Το κλειδί με το οποίο εντοπίζεται η υπάρχουσα εγγραφή. Δεν επιλέγεται
# από τον χειριστή: η ενημέρωση χωρίς σταθερό κλειδί είναι επικίνδυνη.
UPDATE_KEY_FIELD = 'vat_number'


def _mapping_columns(ncols, chosen):
    """Οι στήλες του αρχείου για τον επιλογέα αντιστοίχισης.

    Κάθε στήλη κουβαλά την τρέχουσα επιλογή της, ώστε όταν η φόρμα
    επιστρέφει με σφάλμα (π.χ. δεν αντιστοιχίστηκε το πεδίο-κλειδί) ο
    χειριστής να μη χάνει τη δουλειά που έκανε.
    """
    return [{'index': c, 'selected': chosen.get(c, '')}
            for c in range(ncols)]


def _display_value(value):
    """Η τιμή ενός πεδίου ως κείμενο, για τον πίνακα αλλαγών."""
    if value is None or value == '':
        return '—'
    if value is True:
        return 'Ναι'
    if value is False:
        return 'Όχι'
    return str(value)


def _diff_record(obj, mf, pairs):
    """Ποια πεδία του `obj` θα άλλαζαν αν εφαρμοζόταν η γραμμή.

    Επιστρέφει (changes, warnings). Κάθε change έχει το όνομα και την
    ετικέτα του πεδίου, την τρέχουσα και τη νέα τιμή ως κείμενο, ώστε ο
    χειριστής να δει ακριβώς τι πρόκειται να γίνει πριν γίνει.
    """
    changes = []
    warnings = []
    for field_name, raw_value in pairs:
        if not field_name or field_name == UPDATE_KEY_FIELD:
            continue
        if raw_value == '':
            # Κενό κελί σημαίνει «δεν το πειράζεις», όχι «σβήσ' το»:
            # αλλιώς ένα ελλιπές αρχείο θα άδειαζε στήλες χωρίς να το
            # ζητήσει κανείς.
            continue
        ok, value, warning = _coerce_value(mf, field_name, raw_value)
        if warning:
            warnings.append(warning)
        if not ok:
            continue
        try:
            old = getattr(obj, field_name)
        except Exception:
            old = None
        if old == value:
            continue
        changes.append({
            'field': field_name,
            'label': str(obj._meta.get_field(field_name).verbose_name),
            'old': _display_value(old),
            'new': _display_value(value),
            'value': value,
        })
    return changes, warnings


def _update_rows(request, model, rows, mapping, key_column):
    """Συγκρίνει κάθε γραμμή του αρχείου με την εγγραφή της βάσης.

    Επιστρέφει (matched, notfound, unchanged): τα matched κρατούν τη
    γραμμή, την εγγραφή και τις αλλαγές της.
    """
    mf = {x.name: x.get_internal_type() for x in model._meta.fields}
    matched, notfound, unchanged = [], [], []

    for i, row in enumerate(rows):
        vat = _normalize_vat_number(row[key_column]) if row else None
        if not vat:
            notfound.append({'row': i, 'vat': row[key_column] if row else '',
                             'reason': 'Μη έγκυρο Α.Φ.Μ.'})
            continue

        obj = model.objects.filter(vat_number=vat).first()
        if obj is None:
            reason = 'Δεν βρέθηκε εγγραφή'
            if Employee.objects.filter(vat_number=vat).exists():
                reason = 'Υπάρχει υπάλληλος με αυτό το Α.Φ.Μ., αλλά όχι ως %s' \
                    % model._meta.verbose_name
            notfound.append({'row': i, 'vat': vat, 'reason': reason})
            continue

        pairs = [(name, row[c].strip()) for c, name in mapping]
        changes, warnings = _diff_record(obj, mf, pairs)
        entry = {'row': i, 'vat': vat, 'label': str(obj),
                 'changes': changes, 'warnings': warnings, 'pk': obj.pk}
        if changes:
            matched.append(entry)
        else:
            unchanged.append(entry)

    return matched, notfound, unchanged


@csrf_protect
@staff_member_required
def import_update_view(request):
    """Ενημέρωση υπαρχουσών εγγραφών από αρχείο Excel, με κλειδί το Α.Φ.Μ.

    Τρία βήματα, όπως και η εισαγωγή: μεταφόρτωση -> αντιστοίχιση
    στηλών -> προεπισκόπηση των αλλαγών και εφαρμογή. Οι αλλαγές
    υπολογίζονται ξανά τη στιγμή της εφαρμογής, πάνω στην τρέχουσα
    κατάσταση της βάσης, ώστε να μη γραφτεί ποτέ κάτι που ο χειριστής
    δεν είδε.
    """
    wizard = request.session.get(UPDATE_WIZARD_KEY) or {}
    import_model_name = request.POST.get(
        'import_model', wizard.get('model', 'Permanent'))
    model = _import_model(import_model_name)

    context = {
        "title": 'Ενημέρωση Δεδομένων',
        "opts": [],
        "form": [],
        "app_label": 'Ενημέρωση Δεδομένων',
        "errors": [],
        "import_model": import_model_name,
        "import_model_label": model._meta.verbose_name,
        "import_model_choices": _model_choices(IMPORT_MODELS),
        "key_field": UPDATE_KEY_FIELD,
    }

    if request.method != 'POST':
        request.session.pop(UPDATE_WIZARD_KEY, None)
        return render(request, 'admin/importupdate.html', context)

    # --- βήμα 1: μεταφόρτωση ---------------------------------------------
    if "upload" in request.GET:
        uploaded = request.FILES.get('xls_upload')
        if not uploaded:
            context["errors"] = ['Επιλέξτε αρχείο προς μεταφόρτωση.']
            return render(request, 'admin/importupdate.html', context)
        try:
            rows = _read_xls(uploaded)
        except Exception as ex:
            context["errors"] = [
                'Το αρχείο δεν διαβάστηκε ως βιβλίο Excel (.xls): %s' % ex]
            return render(request, 'admin/importupdate.html', context)
        if not rows:
            context["errors"] = ['Το πρώτο φύλλο του αρχείου δεν έχει δεδομένα.']
            return render(request, 'admin/importupdate.html', context)

        request.session[UPDATE_WIZARD_KEY] = {
            'model': import_model_name,
            'file': uploaded.name,
            'rows': rows,
        }
        context.update({
            "import_file": uploaded.name,
            "fields": [x.name for x in model._meta.fields],
            "cols": _mapping_columns(len(rows[0]), {}),
            "data": rows,
        })
        return render(request, 'admin/importupdate.html', context)

    rows = wizard.get('rows')
    if not rows:
        context["errors"] = [
            'Η συνεδρία έληξε ή δεν έχει μεταφορτωθεί αρχείο. '
            'Ξεκινήστε ξανά από τη μεταφόρτωση.']
        return render(request, 'admin/importupdate.html', context)

    # --- βήμα 2: αντιστοίχιση στηλών και προεπισκόπηση --------------------
    if "preview" in request.GET:
        ncols = len(rows[0])
        mapping = [(c, request.POST.get('field_%d' % c, '').strip())
                   for c in range(ncols)]
        mapping = [(c, name) for c, name in mapping if name]

        key_columns = [c for c, name in mapping if name == UPDATE_KEY_FIELD]
        if not key_columns:
            context.update({
                "errors": ['Αντιστοιχίστε μία στήλη στο πεδίο-κλειδί «%s»: '
                           'χωρίς αυτό δεν μπορεί να βρεθεί η εγγραφή που θα '
                           'ενημερωθεί.' % UPDATE_KEY_FIELD],
                "import_file": wizard.get('file', ''),
                "fields": [x.name for x in model._meta.fields],
                "cols": _mapping_columns(ncols, dict(mapping)),
                "data": rows,
            })
            return render(request, 'admin/importupdate.html', context)

        key_column = key_columns[0]
        matched, notfound, unchanged = _update_rows(
            request, model, rows, mapping, key_column)

        request.session[UPDATE_WIZARD_KEY] = dict(
            wizard, mapping=mapping, key_column=key_column)

        context.update({
            "matched": matched,
            "notfound": notfound,
            "unchanged": unchanged,
            # Σημαία για το πρότυπο: χωρίς αυτήν, ένα αρχείο που δεν φέρνει
            # καμία αλλαγή (όλες οι εγγραφές ήδη ενημερωμένες) εμφάνιζε
            # κενή σελίδα αντί για «δεν χρειάζεται καμία αλλαγή».
            "preview_done": True,
            "imported_file": wizard.get('file', ''),
            "total_changes": sum(len(m['changes']) for m in matched),
        })
        return render(request, 'admin/importupdate.html', context)

    # --- βήμα 3: εφαρμογή -------------------------------------------------
    if "final" in request.GET:
        mapping = [tuple(m) for m in wizard.get('mapping', [])]
        key_column = wizard.get('key_column', 0)
        matched, notfound, unchanged = _update_rows(
            request, model, rows, mapping, key_column)

        updated, failed = [], []
        for k, entry in enumerate(matched):
            if request.POST.get('select_%d' % k, '0') != '0':
                continue
            obj = model.objects.filter(vat_number=entry['vat']).first()
            if obj is None:
                entry['error'] = 'Η εγγραφή δεν υπάρχει πλέον'
                failed.append(entry)
                continue
            for change in entry['changes']:
                setattr(obj, change['field'], change['value'])
            try:
                obj.save()
                updated.append(entry)
            except Exception as ex:
                entry['error'] = str(ex)
                failed.append(entry)

        request.session.pop(UPDATE_WIZARD_KEY, None)
        context.update({
            "updated": updated,
            "failed": failed,
            "notfound": notfound,
        })

    return render(request, 'admin/importupdate.html', context)


def _export_field_value(obj, field):
    """Render one field's value as text for the CSV writer.

    Στην Python 3 το csv module γράφει κείμενο· η κωδικοποίηση γίνεται
    μία φορά, όταν συναρμολογηθεί ολόκληρο το αρχείο.
    """
    try:
        value = getattr(obj, field.name)
    except Exception:
        return ''
    if field.choices:
        display = getattr(obj, 'get_%s_display' % field.name, None)
        if display:
            try:
                value = display()
            except Exception:
                pass
    if value is None or value == '':
        return ''
    if isinstance(value, bool):
        return str(int(value))
    return str(value)


# Πεδία που δεν έχουν νόημα σε αρχείο CSV: η φωτογραφία είναι base64
# μερικών δεκάδων KB ανά εγγραφή και οι σημειώσεις είναι ελεύθερο
# κείμενο με αλλαγές γραμμής. Ο τύπος φωτογραφίας δεν χρησιμεύει χωρίς
# την ίδια την φωτογραφία -- ίδιος αποκλεισμός με το CSVReport του admin.
EXPORT_EXCLUDED_TYPES = ('TextField', 'BinaryField', 'FileField', 'ImageField')
EXPORT_EXCLUDED_NAMES = ('photo_type',)


def exportable_fields(model):
    """The model fields that may appear in an export, in model order."""
    return [f for f in model._meta.fields
            if f.get_internal_type() not in EXPORT_EXCLUDED_TYPES
            and f.name not in EXPORT_EXCLUDED_NAMES]


def _export_csv_response(model, field_names, encoding=DEFAULT_ENCODING):
    # keep the model's own field order rather than whatever order the
    # checkboxes happened to post in, and filter against the exportable
    # set so a hand-made POST cannot ask for an excluded field
    fields = [f for f in exportable_fields(model) if f.name in field_names]
    encoding = clean_encoding(encoding)

    # Το αρχείο συναρμολογείται ως κείμενο και κωδικοποιείται μία φορά στο
    # τέλος, με αντικατάσταση όσων χαρακτήρων δεν χωράνε στο σετ προορισμού.
    buf = StringIO()
    writer = csv.writer(buf, delimiter=';', quotechar='"',
                        quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow([str(f.verbose_name) for f in fields])
    for obj in model.objects.all():
        writer.writerow([_export_field_value(obj, f) for f in fields])

    # Το BOM (όπου χρειάζεται) προηγείται κάθε άλλου χαρακτήρα.
    body = encode_text(bom_for(encoding) + buf.getvalue(), encoding)

    response = HttpResponse(
        body, content_type='text/csv; charset=%s' % charset_name(encoding))
    response['Content-Disposition'] = 'attachment; filename=export_%s_%s.csv' % (
        model.__name__, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
    add_never_cache_headers(response)
    return response


@csrf_protect
@staff_member_required
def export_view(request):
    export_model_name = request.POST.get('export_model')
    model = dict(EXPORT_MODELS).get(export_model_name)
    encoding = clean_encoding(request.POST.get('encoding'))

    context = {
        "title": 'Εξαγωγή Δεδομένων',
        "opts": [],
        "app_label": 'Εξαγωγή Δεδομένων',
        "errors": [],
        "export_model_choices": _model_choices(EXPORT_MODELS),
        "encoding_choices": ENCODING_CHOICES,
        "encoding": encoding,
    }

    if request.POST and model:
        field_choices = [(f.name, str(f.verbose_name))
                         for f in exportable_fields(model)]

        if "download" in request.GET:
            allowed = set(f.name for f in exportable_fields(model))
            selected_fields = [name for name in request.POST.getlist('export_fields')
                               if name in allowed]
            if selected_fields:
                return _export_csv_response(model, selected_fields, encoding)
            context.update({
                "errors": ['Επιλέξτε τουλάχιστον ένα πεδίο προς εξαγωγή.'],
                "export_model": export_model_name,
                "export_field_choices": field_choices,
            })
        elif "fields" in request.GET:
            context.update({
                "export_model": export_model_name,
                "export_field_choices": field_choices,
            })

    r = render(request, 'admin/export.html', context)
    return r




# Οι τέσσερις κατηγορίες υπαλλήλων. Όλες κληρονομούν από το Employee, οπότε
# μία εγγραφή Employee μπορεί να εμφανίζεται σε περισσότερες από μία.
def employee_role_models():
    return [('Μόνιμος', Permanent),
            ('Αναπληρωτής/Ωρομίσθιος', NonPermanent),
            ('Διοικητικός', Administrative),
            ('Ιδιωτικός Εκπαιδευτικός', PrivateTeacher)]


def admin_change_url(app_label, model_name, pk):
    try:
        return reverse('admin:%s_%s_change' % (app_label, model_name), args=[pk])
    except NoReverseMatch:
        return None


@csrf_protect
@staff_member_required
def duplicate_employees_view(request):
    """Εντοπισμός διπλοεγγραφών εκπαιδευτικών.

    Δύο ξεχωριστά προβλήματα εμφανίζονται μαζί:

    * μία εγγραφή Employee που συνδέεται με περισσότερες από μία
      κατηγορίες (π.χ. είναι ταυτόχρονα Μόνιμος και Αναπληρωτής), και
    * περισσότερες εγγραφές Employee, με διαφορετικό id, που αφορούν
      το ίδιο πρόσωπο (ίδιο επώνυμο, όνομα, πατρώνυμο και ειδικότητα).
    """
    if not request.user.is_superuser:
        raise PermissionDenied

    # Ένα ερώτημα ανά κατηγορία για τα ids, αντί για ένα ανά υπάλληλο.
    roles = []
    for label, model in employee_role_models():
        opts = model._meta
        roles.append((label, opts.app_label, opts.model_name,
                      set(model.objects.values_list('parent_id', flat=True))))

    groups = {}
    for e in Employee.objects.all().values(
            'id', 'firstname', 'lastname', 'fathername', 'profession_id',
            'vat_number', 'identity_number', 'date_created', 'date_modified'):
        record = dict(e)
        record['roles'] = [
            {'label': label,
             'url': admin_change_url(app_label, model_name, e['id'])}
            for label, app_label, model_name, ids in roles if e['id'] in ids]
        record['role_count'] = len(record['roles'])
        groups.setdefault(
            identity_key(e['lastname'], e['firstname'],
                         e['fathername'], e['profession_id']), []).append(record)

    duplicates = []
    total_records = 0
    total_multi_role = 0
    for records in list(groups.values()):
        multi_role = [r for r in records if r['role_count'] > 1]
        # Ενδιαφέρουν είτε οι πολλαπλές εγγραφές του ίδιου προσώπου είτε
        # η μία εγγραφή που ανήκει σε πολλές κατηγορίες.
        if len(records) < 2 and not multi_role:
            continue
        records.sort(key=lambda r: r['id'])
        first = records[0]
        duplicates.append({
            'lastname': first['lastname'],
            'firstname': first['firstname'],
            'fathername': first['fathername'],
            'profession': first['profession_id'],
            'records': records,
            'record_count': len(records),
            'multi_role_count': len(multi_role),
        })
        total_records += len(records)
        total_multi_role += len(multi_role)

    duplicates.sort(key=lambda g: (g['lastname'] or '', g['firstname'] or ''))

    context = {
        "title": 'Έλεγχος διπλοεγγραφών',
        "app_label": 'Έλεγχος διπλοεγγραφών',
        "opts": [],
        "errors": [],
        "duplicates": duplicates,
        "total_groups": len(duplicates),
        "total_records": total_records,
        "total_multi_role": total_multi_role,
        "role_labels": [label for label, model in employee_role_models()],
    }
    return render(request, 'admin/duplicates.html', context)


def json_for_script(data):
    """Serialize data for embedding inside a <script> block.

    json.dumps escapes non-ASCII already; the angle brackets and
    ampersand are escaped too so that no value can close the script
    element early.
    """
    return json.dumps(data).replace('<', '\\u003c') \
                           .replace('>', '\\u003e') \
                           .replace('&', '\\u0026')


@csrf_protect
@staff_member_required
def school_geo_view(request):
    sch = School.objects.all() \
        .exclude(google_maps_x__isnull=True).exclude(google_maps_x__exact='') \
        .exclude(google_maps_y__isnull=True).exclude(google_maps_y__exact='') \
        .select_related('type', 'transfer_area', 'island', 'manager')
    sch_units = []
    y1 = datetime.date.today().year if datetime.date.today().month > 8 and datetime.date.today().month <= 12 else datetime.date.today().year - 1
    y2 = datetime.date.today().year if datetime.date.today().month >= 1 and datetime.date.today().month < 9 else datetime.date.today().year + 1

    total_p = 0
    total_np = 0
    for item in sch:
        c_npr = NonPermanent.objects.temporary_post_in_organization(item.id).count()
        c_prm = Permanent.objects.serving_in_organization(item.id).filter(currently_serves=True).count()
        total_p += c_prm
        total_np += c_npr

        def text(value):
            return str(value) if value else ''

        unit = {
            'id': item.id,
            'title': item.name,
            'x': item.google_maps_x,
            'y': item.google_maps_y,
            # Η ακτίνα των κύκλων παραμένει ανάλογη του πλήθους.
            'pop_p': c_prm * 25,
            'pop_np': c_npr * 25,
            'permanent': c_prm,
            'nonpermanent': c_npr,
            'total': c_prm + c_npr,
            'code': text(item.code),
            'type': text(item.type),
            'transfer_area': text(item.transfer_area),
            'island': text(item.island),
            'address': text(item.address),
            'post_code': text(item.post_code),
            'telephone': text(item.telephone_number),
            'fax': text(item.fax_number),
            'email': text(item.email),
            'manager': text(item.manager),
            'points': text(item.points),
            'inaccessible': bool(item.inaccessible),
            'url': admin_change_url('dide', 'school', item.id),
        }
        sch_units.append(unit)

    sch_units.sort(key=lambda u: u['title'])

    map_settings = SETTINGS['open_map_settings'].split(';')
    opts = []
    context = {
        "yf": y1,
        "yt": y2,
        "schools": sch_units,
        "schools_json": json_for_script(sch_units),
        "total_schools": len(sch_units),
        "total_permanent": total_p,
        "total_nonpermanent": total_np,
        "om_x": map_settings[0],
        "om_y": map_settings[1],
        "om_zoom": map_settings[2],
        "title": 'Γεωγραφική Απεικόνιση Σχολείων',
        "opts": opts,
        "form": [],
        "app_label": 'Γεωγραφική Απεικόνιση Σχολείων',
        "errors": [],
    }

    r = render(request, 'admin/schools_geo_list.html', context)
    return HttpResponse(r)


def handler404(request, exception=None):
    response = render(request, 'admin/404.html', {})
    response.status_code = 404
    return response


def handler500(request):
    response = render(request, 'admin/500.html', {})
    response.status_code = 500
    return response
