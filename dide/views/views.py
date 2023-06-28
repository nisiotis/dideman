# -*- coding: utf-8 -*-
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from dideman.dide.models import Employee, NonPermanent, Permanent, School, Placement, Administrative
from dideman.private_teachers.models import PrivateTeacher
from dideman.dide.util.settings import SETTINGS
from django import VERSION as djangoversion
from django.utils.translation import ugettext as _
from django.utils import six
from django.utils.text import capfirst
from django.views.decorators.cache import never_cache
from django.db.models import Q
from django.conf.urls import *
from django.core.urlresolvers import reverse, NoReverseMatch
from cStringIO import StringIO
import datetime, base64


def find_duplicates():
    l = []
    r = 0
    pl = Permanent.objects.all()
    nl = NonPermanent.objects.exclude(vat_number=None)

    for pitem in pl:
        for nitem in nl:
            if (pitem.firstname == nitem.firstname) and (pitem.lastname == nitem.lastname) and (pitem.fathername == nitem.fathername) and (pitem.profession == nitem.profession):
                l.append(pitem)
                r += 1
                l.append(nitem)

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
    response = render_to_response('404.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 404
    return response


def handler500(request):
    response = render_to_response('500.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 500
    return response
