# -*- coding: utf-8 -*-
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from dideman.dide.models import Profession, TransferArea, Employee, NonPermanent, Permanent, School, Placement, Administrative
from dideman.private_teachers.models import PrivateTeacher
from dideman.dide.util.settings import SETTINGS
from django import VERSION as djangoversion
from django.utils.translation import ugettext as _
from django.utils import six
from django.utils.text import capfirst
from django.views.decorators.cache import never_cache
from django.utils.cache import add_never_cache_headers
from django.db.models import Q
from django.conf.urls import *
from django.core.urlresolvers import reverse, NoReverseMatch
from django.core.exceptions import PermissionDenied
from dideman.lib.common import without_accented
from cStringIO import StringIO
import csv
import datetime, base64
import os, itertools
import xlrd


def identity_key(lastname, firstname, fathername, profession_id):
    """The combination that in practice identifies one person.

    Names are compared case-insensitively, without surrounding
    whitespace and without tonos, so that 'ΆΝΝΑ' and 'ΑΝΝΑ ' count as
    the same person.
    """
    def norm(v):
        return without_accented(unicode(v if v is not None else u'').strip().upper())
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

@never_cache
def index(self, request, extra_context=None):
    """
    Displays the main admin index page, which lists all of the installed
    apps that have been registered in this site. Added a search field, used monkey-patch 
    to overide the default index
    """
    app_dict = {}
    search_model = []
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
    for model, model_admin in self._registry.items():
        if model._meta.app_label == "dide":
            app_label = model._meta.app_label
            app_text = u"Διεύθυνση"
        elif model._meta.app_label == "auth":
            app_label = model._meta.app_label
            app_text = u"Χρήστες"
        elif model._meta.app_label == "private_teachers":
            app_label = model._meta.app_label
            app_text = u"Ιδιωτικά Σχολεία"
        else:
            app_text = model._meta.app_label
            app_label = model._meta.app_label

        has_module_perms = user.has_module_perms(app_label)
        if has_module_perms:
            perms = model_admin.get_model_perms(request)

            # Check whether user has any perm for this module.
            # If so, add the module to the model_list.
            if True in perms.values():
                info = (app_label, model._meta.model_name)
                search_model.append(model)
                model_dict = {
                    'name': capfirst(model._meta.verbose_name_plural),
                    'perms': perms,
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
    app_list = list(six.itervalues(app_dict))
    app_list.sort(key=lambda x: x['name'])

    # Sort the models alphabetically within each app.
    for app in app_list:
        app['models'].sort(key=lambda x: x['name'])

    tot_perm = Permanent.objects.filter(currently_serves=1).count()

    y1 = datetime.date.today().year if datetime.date.today().month > 8 and datetime.date.today().month <= 12 else datetime.date.today().year - 1
    y2 = datetime.date.today().year if datetime.date.today().month >= 1 and datetime.date.today().month < 9 else datetime.date.today().year + 1

    tot_non = NonPermanent.objects.substitutes_in_date_range(date_from='%d-09-01' % y1, date_to='%d-08-31' % y2) 

    tot_priv = PrivateTeacher.objects.filter(active__exact=1).count()

    tot_admin = Administrative.objects.filter(currently_serves=1).count()
    dbls, l = find_duplicates()
    context = {
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
        'django_version': 'Django ' + '.'.join(str(i) for i in djangoversion[:3]),
        'total_dbl': l,

    }
    context.update(extra_context or {})
    if request.POST:
        results = {}
        total_results = 0
        if request.POST['q'] != '':
            if request.POST['q'] == '/photo':
                for model in search_model:
                    if model.__name__ in ("Permanent", "NonPermanent", "Administrative"):
                        results[model._meta.verbose_name] = model.objects.exclude(photo__exact='').exclude(photo__isnull=True)
                        total_results += len(results[model._meta.verbose_name])
            if request.POST['q'] == '/nonpermanent':
                results['Ενεργοί αναπληρωτές'] = tot_non
                total_results = tot_non.count()
            elif request.POST['q'] == '/dublicates':
                results['Διπλές Εγγραφές'] = dbls
                total_results = l
            elif request.POST['q'] == '/lastedit':
                for model in search_model:
                    if model.__name__ in ("Permanent", "NonPermanent", "Administrative", "PrivateTeacher"):
                        results[model._meta.verbose_name] = model.objects.filter(date_modified__year=today.year,
                                                date_modified__month=today.month,
                                                date_modified__day=today.day)
                        total_results += len(results[model._meta.verbose_name])
            else:
                for model in search_model:
                    
                    if model.__name__ == "Permanent":
                        results[model._meta.verbose_name] = model.objects.filter(Q(lastname__istartswith=request.POST['q'].upper())
                        | Q(vat_number__istartswith=request.POST['q'])
                        | Q(registration_number__istartswith=request.POST['q']))
                        total_results += len(results[model._meta.verbose_name])
                    if model.__name__ in ("NonPermanent", "Administrative", "PrivateTeacher"):
                        results[model._meta.verbose_name] = model.objects.filter(Q(lastname__istartswith=request.POST['q'].upper())
                        | Q(vat_number__istartswith=request.POST['q']))
                        total_results += len(results[model._meta.verbose_name])

        context = {
            'title': _('Search'),
            'q': request.POST['q'],
            't': total_results,
            'set': results,
        }
        
        context.update(extra_context or {})
        return TemplateResponse(request, 'admin/search.html', context,
                            current_app=self.name)
    else:
        return TemplateResponse(request, self.index_template or
                            'admin/index.html', context,
                            current_app=self.name)


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
        "messages": messages,
        "emp": e,
        "dide_place": SETTINGS['dide_place'],
        "errors": [],
    }
    return render_to_response('admin/photo.html',
                                  RequestContext(request, context))


@csrf_protect
@staff_member_required
def photo(request, emp_id):
    emp = Employee.objects.get(id=emp_id)
    file = StringIO()
    file.write(base64.b64decode(emp.photo))
    file.seek(0)
    response = HttpResponse(file.getvalue(), content_type='image/%s' % emp.photo_type)
    file.close()
    return response


@csrf_protect
@staff_member_required
def nonpermanent_list(request):
    np = NonPermanent.objects.all()
    context = {
        "set": np,
        "dide_place": SETTINGS['dide_place'],
        "errors": [],
    }
    r = render_to_response('admin/nonpermanent_list.html', context, RequestContext(request))
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
        digits = ''.join(ch for ch in unicode(value) if ch.isdigit())
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
            missing.append(unicode(f.verbose_name))
        elif f.get_internal_type() == "BooleanField":
            setattr(obj, f.attname, False)
        elif f.get_internal_type() in ("CharField", "TextField"):
            setattr(obj, f.attname, '')
    return missing


def _build_import_record(model, mf, request, row):
    """Build one unsaved instance of `model` from the posted row.

    Returns (instance, warnings); warnings names any column whose value
    could not be applied, so the row can still be saved on the strength
    of its remaining fields and the operator can see what was dropped.
    """
    p = model()
    warnings = []
    for j in range(1, int(request.POST['fieldlength'])+1):
        field_name = request.POST['field_item_'+str(j)]
        raw_value = request.POST['row_'+str(row)+'_item_'+str(j)]
        if not raw_value:
            continue
        if field_name not in mf:
            warnings.append(u"%s: άγνωστο πεδίο" % field_name)
            continue

        if field_name == 'vat_number':
            vat = _normalize_vat_number(raw_value)
            if vat:
                setattr(p, field_name, vat)
            else:
                warnings.append(u"%s: μη έγκυρη τιμή '%s'" % (field_name, raw_value))

        elif mf[field_name] == "ForeignKey":
            if field_name in ("profession", "second_profession"):
                try:
                    setattr(p, field_name,
                            Profession.objects.get(pk=unicode(raw_value)))
                except Exception:
                    warnings.append(
                        u"%s: δεν βρέθηκε η τιμή '%s'" % (field_name, raw_value))
            elif field_name == "transfer_area":
                try:
                    setattr(p, field_name,
                            TransferArea.objects.filter(
                                name__istartswith=unicode(raw_value)[:1])[0])
                except Exception:
                    warnings.append(
                        u"%s: δεν βρέθηκε η τιμή '%s'" % (field_name, raw_value))
            else:
                try:
                    setattr(p, field_name, int(raw_value))
                except Exception:
                    warnings.append(
                        u"%s: μη έγκυρη τιμή '%s'" % (field_name, raw_value))

        elif mf[field_name] in ("IntegerField", "OneToOneField"):
            try:
                setattr(p, field_name,
                        int(''.join(v for v in raw_value if v.isdigit())))
            except Exception:
                warnings.append(
                    u"%s: μη έγκυρη τιμή '%s'" % (field_name, raw_value))

        elif mf[field_name] in ("BooleanField", "NullBooleanField"):
            try:
                setattr(p, field_name, int(raw_value[:1]))
            except Exception:
                warnings.append(
                    u"%s: μη έγκυρη τιμή '%s'" % (field_name, raw_value))

        else:
            setattr(p, field_name, raw_value)

    return p, warnings


@csrf_protect
@staff_member_required
def import_export_view(request):
    import_model_name = request.POST.get('import_model', 'Permanent')
    model = _import_model(import_model_name)

    context = {
        "title": u'Εισαγωγή - Εξαγωγή Δεδομένων',
        "opts": [],
        "form": [],
        "app_label": u'Εισαγωγή - Εξαγωγή Δεδομένων',
        "errors": [],
        "import_model": import_model_name,
        "import_model_label": model._meta.verbose_name,
        "import_model_choices": _model_choices(IMPORT_MODELS),
    }

    if request.POST:
        if "final" in request.GET:
            saved = []
            notins = []
            foundins = []
            if 'datalength' in request.POST:
                mf = {x.name: x.get_internal_type() for x in model._meta.fields}
                for i in range(0, int(request.POST['datalength'])):
                    if int(request.POST['select_'+str(i)]) != 0:
                        continue

                    p, warnings = _build_import_record(model, mf, request, i)
                    # reported back to the template per row
                    p.import_error = ''
                    p.import_warnings = warnings

                    missing = _fill_required_defaults(p)
                    if missing:
                        p.import_error = u'Λείπουν υποχρεωτικά πεδία: %s' % \
                            u', '.join(missing)
                        notins.append(p)
                        continue

                    # An employee already holding this Α.Φ.Μ. means the row is
                    # a duplicate: skip it and say which record it clashed
                    # with, rather than creating a second entry for the same
                    # person. Checked against the database at save time, so a
                    # record added since the file was uploaded is still caught.
                    vat = getattr(p, 'vat_number', None)
                    if vat:
                        existing = Employee.objects.filter(vat_number=vat).first()
                        if existing:
                            p.import_error = \
                                u'Υπάρχει ήδη εγγραφή με Α.Φ.Μ. %s: %s' % (vat, existing)
                            foundins.append(p)
                            continue

                    try:
                        p.save()
                        saved.append(p)
                    except Exception as ex:
                        p.import_error = unicode(ex)
                        notins.append(p)

            context.update({
                "dataimported": saved,
                "notinserted": notins,
                "foundinserted": foundins,
            })

        if "save" in request.GET:
            sel_rows = 0
            ds = []
            fset = []
            dbl = 0
            if 'datalength' in request.POST:
                for i in range(0,int(request.POST['columns'])):
                    if len(request.POST['field_'+str(i)]) > 0:

                        fset.append(request.POST['field_'+str(i)])

                for i in range(0,int(request.POST['datalength'])):
                    if "check_"+str(i) in request.POST:
                        sel_rows += 1
                        d = {}
                        for j in range(1,int(request.POST['columns'])+1):
                            if len(request.POST['field_'+str(j-1)]) > 0:
                                d[j] = request.POST['row_'+str(i)+'_item_'+str(j)].strip()

                        vat = _normalize_vat_number(request.POST['check_'+str(i)])
                        e = Employee.objects.filter(vat_number=vat) if vat else Employee.objects.none()

                        if e:
                            d['found'] = e[0].vat_number
                            dbl += 1
                        else:
                            d['found'] = ''
                        ds.append(d)


                context.update({
                    "dataselected": ds,
                    "dublicates": dbl,
                    "imported_file": request.POST['imported_file'],
                    "cols": range(1, int(request.POST['columns'])+1),
                    "iterator": itertools.count(),
                    "field_titles": fset,
                })
        if "upload" in request.GET:
            importfile = ""
            if 'xls_upload' in request._files:
                mf = [x.name for x in model._meta.fields]
                importfile = request._files['xls_upload']
                workbook = xlrd.open_workbook(file_contents=importfile.read())
                worksheet = workbook.sheet_by_index(0)
                curr_row = 1
                xlsdata = []
                ncols = worksheet.ncols
                while curr_row < worksheet.nrows:
                    d = {}
                    for i in range(ncols):
                        d[i] = unicode(worksheet.cell_value(curr_row,i))
                    xlsdata.append(d)
                    curr_row += 1
                context.update({
                    "import_file": importfile.name,
                    "fields": mf,
                    "cols": range(ncols),
                    "iterator": itertools.count(),
                    "data": xlsdata,
                })

    r = render_to_response('admin/importexport.html', context, RequestContext(request))
    return r


def _export_field_value(obj, field):
    """Render one field's value for CSV export, in the same iso-8859-7
    (Greek/Windows) encoding the admin's CSV report actions already use,
    so exported files open cleanly in Excel."""
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
    if isinstance(value, unicode):
        return value.encode('iso8859-7', 'ignore')
    if hasattr(value, '__unicode__'):
        return unicode(value).encode('iso8859-7', 'ignore')
    return str(value)


def _export_csv_response(model, field_names):
    # keep the model's own field order rather than whatever order the
    # checkboxes happened to post in
    fields = [f for f in model._meta.fields if f.name in field_names]

    response = HttpResponse()
    response['Content-Type'] = 'text/csv; charset=iso-8859-7'
    response['Content-Disposition'] = 'attachment; filename=export_%s_%s.csv' % (
        model.__name__, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
    add_never_cache_headers(response)

    writer = csv.writer(response, delimiter=';', quotechar='"',
                        quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow([unicode(f.verbose_name).encode('iso8859-7', 'ignore') for f in fields])
    for obj in model.objects.all():
        writer.writerow([_export_field_value(obj, f) for f in fields])
    return response


@csrf_protect
@staff_member_required
def export_view(request):
    export_model_name = request.POST.get('export_model')
    model = dict(EXPORT_MODELS).get(export_model_name)

    context = {
        "title": u'Εξαγωγή Δεδομένων',
        "opts": [],
        "app_label": u'Εξαγωγή Δεδομένων',
        "errors": [],
        "export_model_choices": _model_choices(EXPORT_MODELS),
    }

    if request.POST and model:
        field_choices = [(f.name, unicode(f.verbose_name)) for f in model._meta.fields]

        if "download" in request.GET:
            selected_fields = request.POST.getlist('export_fields')
            if selected_fields:
                return _export_csv_response(model, selected_fields)
            context.update({
                "errors": [u'Επιλέξτε τουλάχιστον ένα πεδίο προς εξαγωγή.'],
                "export_model": export_model_name,
                "export_field_choices": field_choices,
            })
        elif "fields" in request.GET:
            context.update({
                "export_model": export_model_name,
                "export_field_choices": field_choices,
            })

    r = render_to_response('admin/export.html', context, RequestContext(request))
    return r




# Οι τέσσερις κατηγορίες υπαλλήλων. Όλες κληρονομούν από το Employee, οπότε
# μία εγγραφή Employee μπορεί να εμφανίζεται σε περισσότερες από μία.
def employee_role_models():
    return [(u'Μόνιμος', Permanent),
            (u'Αναπληρωτής/Ωρομίσθιος', NonPermanent),
            (u'Διοικητικός', Administrative),
            (u'Ιδιωτικός Εκπαιδευτικός', PrivateTeacher)]


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
    for records in groups.values():
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

    duplicates.sort(key=lambda g: (g['lastname'] or u'', g['firstname'] or u''))

    context = {
        "title": u'Έλεγχος διπλοεγγραφών',
        "app_label": u'Έλεγχος διπλοεγγραφών',
        "opts": [],
        "errors": [],
        "duplicates": duplicates,
        "total_groups": len(duplicates),
        "total_records": total_records,
        "total_multi_role": total_multi_role,
        "role_labels": [label for label, model in employee_role_models()],
    }
    return render_to_response('admin/duplicates.html', context,
                              RequestContext(request))


@csrf_protect
@staff_member_required
def school_geo_view(request):
    sch = School.objects.all().exclude(google_maps_x__isnull=True).exclude(google_maps_x__exact='').exclude(google_maps_y__isnull=True).exclude(google_maps_y__exact='')
    sch_units = []
    y1 = datetime.date.today().year if datetime.date.today().month > 8 and datetime.date.today().month <= 12 else datetime.date.today().year - 1
    y2 = datetime.date.today().year if datetime.date.today().month >= 1 and datetime.date.today().month < 9 else datetime.date.today().year + 1

#    y1 = datetime.date.today().year + 1 if datetime.date.today().month <= 9 else datetime.date.today().year
#    y2 = datetime.date.today().year + 1 if datetime.date.today().month > 9 else datetime.date.today().year      

    for item in sch:
        c_npr = NonPermanent.objects.temporary_post_in_organization(item.id).count()
        c_prm = Permanent.objects.serving_in_organization(item.id).filter(currently_serves=True).count()
        unit = {
            'id': item.id,
            'title': item.name,
            'x': item.google_maps_x,
            'y': item.google_maps_y,
            'pop_p': c_prm * 25,
            'pop_np': c_npr * 25,
        }
        sch_units.append(unit)

    map_settings = SETTINGS['open_map_settings'].split(';')
    opts = []
    context = {
        "yf": y1,
        "yt": y2,
        "schools": sch_units,
        "om_x": map_settings[0],
        "om_y": map_settings[1],
        "om_zoom": map_settings[2],
        "title": u'Γεωγραφική Απεικόνιση Σχολείων',
        "opts": opts,
        "form": [],
        "app_label": u'Γεωγραφική Απεικόνιση Σχολείων',
        "errors": [],
    }

    r = render_to_response('admin/schools_geo_list.html', context, RequestContext(request))
    return HttpResponse(r)


def handler404(request):
    response = render_to_response('admin/404.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 404
    return response


def handler500(request):
    response = render_to_response('admin/500.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 500
    return response
