# -*- coding: utf-8 -*-
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect
from django.contrib.admin.views.decorators import staff_member_required
from dideman.dide.models import NonPermanent, Permanent, School, Placement, Administrative
from dideman.private_teachers.models import PrivateTeacher
from dideman.dide.util.settings import SETTINGS
from django import VERSION as djangoversion
from django.utils.translation import ugettext as _
from django.utils import six
from django.utils.text import capfirst
from django.views.decorators.cache import never_cache
from django.db.models import Q
from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse
from django.utils.encoding import force_unicode

import datetime

@never_cache
def index(self, request, extra_context=None):
    """
    Displays the main admin index page, which lists all of the installed
    apps that have been registered in this site.
    """
    app_dict = {}
    search_model = []
    user = request.user
    for model, model_admin in self._registry.items():
        app_label = model._meta.app_label
        has_module_perms = user.has_module_perms(app_label)

        if has_module_perms:
            perms = model_admin.get_model_perms(request)

            # Check whether user has any perm for this module.
            # If so, add the module to the model_list.
            if True in perms.values():
                info = (app_label, model._meta.module_name)
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
                if perms.get('add', False):
                    try:
                        model_dict['add_url'] = reverse('admin:%s_%s_add' % info, current_app=self.name)
                    except NoReverseMatch:
                        pass
                if app_label in app_dict:
                    app_dict[app_label]['models'].append(model_dict)
                else:
                    app_dict[app_label] = {
                        'name': app_label.title(),
                        'app_url': reverse('admin:app_list', kwargs={'app_label': app_label}, current_app=self.name),
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
    y1 = datetime.date.today().year + 1 if datetime.date.today().month <= 9 else datetime.date.today().year
    y2 = datetime.date.today().year + 1 if datetime.date.today().month > 9 else datetime.date.today().year      
    tot_non = NonPermanent.objects.substitutes_in_date_range(date_from='%d-09-01' % y1, date_to='%d-08-31' % y2).count() 

    tot_priv = PrivateTeacher.objects.filter(active__exact=1).count()

    tot_admin = Administrative.objects.filter(currently_serves=1).count()

    context = {
        'title': _('Site administration'),
        'app_list': app_list,
        'total_permanent': '%d' % tot_perm,
        'total_nonpermanent': '%d' % tot_non,
        'total_private': '%d' % tot_priv,
        'total_administrative': '%d' % tot_admin,
        'y_1': y1,
        'y_2': y2, 
        'django_version': 'Django ' + '.'.join(str(i) for i in djangoversion[:3]),
    }
    context.update(extra_context or {})
    if request.POST:
        results = {}
        total_results = 0
        if request.POST['q'] != '':
            for model in search_model:
                if model.__name__ == "Permanent":
                    results[model._meta.verbose_name] = model.objects.filter(Q(lastname__startswith=request.POST['q'].upper())
                    | Q(vat_number__startswith=request.POST['q'])
                    | Q(registration_number__startswith=request.POST['q']))
                    total_results += len(results[model._meta.verbose_name])
                if model.__name__ in ("NonPermanent", "Administrative", "PrivateTeacher"):
                    results[model._meta.verbose_name] = model.objects.filter(Q(lastname__startswith=request.POST['q'].upper())
                    | Q(vat_number__startswith=request.POST['q']))
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
def nonpermanent_list(request): 
    np = NonPermanent.objects.all()
    #import pdb; pdb.set_trace()
        
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
    for item in sch:
        #import pdb; pdb.set_trace()
        c_npr = NonPermanent.objects.temporary_post_in_organization(item.id).count()
        c_prm = Permanent.objects.serving_in_organization(item.id).filter(currently_serves=True).count()
        unit = {
            'id': item.id,
            'title': item.name,
            'x': item.google_maps_x,
            'y': item.google_maps_y,
            'pop': c_prm,
            'pop_np': c_npr,
        }
        sch_units.append(unit)

    g_settings = SETTINGS['google_map_settings'].split(',')
    opts = []
    context = {
        "schools": sch_units,
        "google_x": g_settings[0],
        "google_y": g_settings[1],
        "google_zoom": g_settings[2],
        "google_key": SETTINGS['google_map_key'],
        "title": u'Γεωγραφική Απεικόνιση Σχολείων',
        "opts": opts,
        "form": [],
        "app_label": u'Γεωγραφική Απεικόνιση Σχολείων',
        "errors": [],
    }

    r = render_to_response('admin/schools_geo_list.html', context, RequestContext(request))
    return HttpResponse(r)

from django.shortcuts import render_to_response
from django.template import RequestContext


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
