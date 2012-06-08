# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.contrib.admin.filters import FieldListFilter
from django.db import models
from django.contrib.admin.util import get_fields_from_path
from dideman.dide.filters import FreeDateFieldListFilter
from chosen import forms as chosenforms
from django.shortcuts import render_to_response


def get_specs(request, model, model_admin):
    filter_specs = []
    if model_admin.list_filter:
        for list_filter in model_admin.list_filter:
            if callable(list_filter):
                spec = list_filter(request, [], model, model_admin)
            else:
                field_path = None
                if isinstance(list_filter, (tuple, list)):
                    field, field_list_filter_class = list_filter
                else:
                    field, field_list_filter_class = (list_filter,
                    FieldListFilter.create)
                if not isinstance(field, models.Field):
                    field_path = field
                    field = get_fields_from_path(model, field_path)[-1]
                spec = field_list_filter_class(field,
                                               request, [], model, model_admin,
                                               field_path=field_path)
            if spec and spec.has_output():
                filter_specs.append(spec)
    return filter_specs


def render_template(request, model, model_admin):
    selects = []
    date_filters = []
    specs = get_specs(request, model, model_admin)
    for spec in specs:
        if isinstance(spec, FreeDateFieldListFilter):
            date_filters.append(spec)
        elif spec.lookup_choices:
            if isinstance(spec.lookup_choices, (list, tuple)):
                choices = spec.lookup_choices
            else:
                choices = [(x, x) for x in spec.lookup_choices]
            select_multiple = chosenforms.ChosenSelectMultiple(
                choices=choices, overlay=u'Επιλέξτε',
                attrs={'style': 'width:600px',
                       'name': spec.lookup_param, 'title': spec.title})
            selects.append(select_multiple)
    return render_to_response('admin/full_filters.html',
                              {'selects': selects,
                               'date_filters': date_filters,
                               'path': '/'.join(request.path.split('/')[:-2])})


def permanent(request):
    from dideman.dide.admin import PermanentAdmin
    from dideman.dide.models import Permanent
    return render_template(request, Permanent, PermanentAdmin)


def placementtype(request):
    from dideman.dide.admin import PlacementTypeAdmin
    from dideman.dide.models import PlacementType
    return render_template(request, PlacementType, PlacementTypeAdmin)


def profession(request):
    from dideman.dide.admin import ProfessionAdmin
    from dideman.dide.models import Profession
    return render_template(request, Profession, ProfessionAdmin)


def school(request):
    from dideman.dide.admin import SchoolAdmin
    from dideman.dide.models import School
    return render_template(request, School, SchoolAdmin)


def schooltype(request):
    from dideman.dide.admin import SchoolTypeAdmin
    from dideman.dide.models import SchoolType
    return render_template(request, SchoolType, SchoolTypeAdmin)


def nonpermanent(request):
    from dideman.dide.admin import NonPermanentAdmin
    from dideman.dide.models import NonPermanent
    return render_template(request, NonPermanent, NonPermanentAdmin)


def employeeleave(request):
    from dideman.dide.admin import EmployeeLeaveAdmin
    from dideman.dide.models import EmployeeLeave
    return render_template(request, EmployeeLeave, EmployeeLeaveAdmin)


def otherorganization(request):
    from dideman.dide.admin import OtherOrganizationAdmin
    from dideman.dide.models import OtherOrganization
    return render_template(request, OtherOrganization, OtherOrganizationAdmin)
