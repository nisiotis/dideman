# -*- coding: utf-8 -*-
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect
from django.contrib.admin.views.decorators import staff_member_required
from dideman.dide.models import NonPermanent, Permanent, School, Placement
from dideman.dide.util.settings import SETTINGS


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

