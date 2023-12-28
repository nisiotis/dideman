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
        else:
            if hasattr(spec, 'lookup_choices'):
                if isinstance(spec.lookup_choices, (list, tuple)):
                    choices = spec.lookup_choices
                else:
                    choices = [(x, x) for x in spec.lookup_choices]
            elif hasattr(spec, 'choices'):
                choices = spec.choices()
            else:
                choices = None
            if choices:
                select_multiple = chosenforms.ChosenSelectMultiple(
                    choices=choices, overlay=u'Επιλέξτε',
                    attrs={'style': 'width:600px',
                           'name': spec.lookup_param, 'title': spec.title})
                selects.append(select_multiple)
    return render_to_response('admin/full_filters.html',
                              {'selects': selects,
                               'date_filters': date_filters,
                               'path': '/'.join(request.path.split('/')[:-2])})


def application(request):
    from dideman.dide.admin import ApplicationAdmin
    from dideman.dide.models import Application
    return render_template(request, Application, ApplicationAdmin)


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

def administrative(request):
    from dideman.dide.admin import AdministrativeAdmin
    from dideman.dide.models import Administrative
    return render_template(request, Administrative, AdministrativeAdmin)


def nonpermanentleave(request):
  from dideman.dide.admin import NonPermanentLeaveAdmin
  from dideman.dide.models import NonPermanentLeave
  return render_template(request, NonPermanentLeave, NonPermanentLeaveAdmin)


def employeeleave(request):
    from dideman.dide.admin import EmployeeLeaveAdmin
    from dideman.dide.models import EmployeeLeave
    return render_template(request, EmployeeLeave, EmployeeLeaveAdmin)

def permanentleave(request):
    from dideman.dide.admin import PermanentLeaveAdmin
    from dideman.dide.models import PermanentLeave
    return render_template(request, PermanentLeave, PermanentLeaveAdmin)

def administrativeleave(request):
    from dideman.dide.admin import AdministrativeLeaveAdmin
    from dideman.dide.models import AdministrativeLeave
    return render_template(request, AdministrativeLeave, AdministrativeLeaveAdmin)

def otherorganization(request):
    from dideman.dide.admin import OtherOrganizationAdmin
    from dideman.dide.models import OtherOrganization
    return render_template(request, OtherOrganization, OtherOrganizationAdmin)

def temporaryposition(request):
    from dideman.dide.admin import TemporaryPositionAdmin
    from dideman.dide.models import TemporaryPosition
    return render_template(request, TemporaryPosition,
                           TemporaryPositionAdmin)


def moveinside(request):
    from dideman.dide.admin import MoveInsideApplication
    from dideman.dide.models import MoveInside
    return render_template(request, MoveInside,
                           MoveInsideAdmin)


def temporarypositionallareas(request):
    from dideman.dide.admin import TemporaryPositionAllAreas
    from dideman.dide.models import TemporaryPositionAllAreas
    return render_template(request, TemporaryPositionAllAreas,
                           TemporaryPositionAllAreas)


def applicationset(request):
    from dideman.dide.admin import ApplicationSetAdmin
    from dideman.dide.models import ApplicationSet
    return render_template(request, ApplicationSet, ApplicationSetAdmin)


def substituteministryorder(request):
    from dideman.dide.admin import SubstituteMinistryOrderAdmin
    from dideman.dide.models import SubstituteMinistryOrder
    return render_template(request, SubstituteMinistryOrder,
                           SubstituteMinistryOrderAdmin)


def paymentfilename(request):
    from dideman.dide.admin import PaymentFileNameAdmin
    from dideman.dide.models import PaymentFileName
    return render_template(request, PaymentFileName,
                           PaymentFileNameAdmin)


def paymentfilepdf(request):
    from dideman.dide.admin import PaymentFilePDFAdmin
    from dideman.dide.models import PaymentFilePDF
    return render_template(request, PaymentFilePDF,
                           PaymentFilePDFAdmin)

def nonpermanentinsurancefile(request):
    from dideman.dide.admin import NonPermanentInsuranceFileAdmin
    from dideman.dide.models import NonPermanentInsuranceFile
    return render_template(request, NonPermanentInsuranceFile,
                           NonPermanentInsuranceFileAdmin)


def rankcode(request):
    from dideman.dide.admin import RankCodeAdmin
    from dideman.dide.models import RankCode
    return render_template(request, RankCode, RankCodeAdmin)


def socialsecurity(request):
    from dideman.dide.admin import SocialSecurityAdmin
    from dideman.dide.models import SocialSecurity
    return render_template(request, SocialSecurity, SocialSecurityAdmin)


def paymentcode(request):
    from dideman.dide.admin import PaymentCodeAdmin
    from dideman.dide.models import PaymentCode
    return render_template(request, PaymentCode, PaymentCodeAdmin)


def paymentreporttype(request):
    from dideman.dide.admin import PaymentReportTypeAdmin
    from dideman.dide.models import PaymentReportType
    return render_template(request, PaymentReportType,
                           PaymentReportTypeAdmin)


def paymentcategorytitle(request):
    from dideman.dide.admin import PaymentCategoryTitleAdmin
    from dideman.dide.models import PaymentCategoryTitle
    return render_template(request, PaymentCategoryTitle,
                           PaymentCategoryTitleAdmin)

def schoolcommission(request):
    from dideman.dide.admin import SchoolCommissionAdmin
    from dideman.dide.models import SchoolCommission
    return render_template(request, SchoolCommission,
                           SchoolCommissionAdmin)

def leave(request):
    from dideman.dide.admin import LeaveAdmin
    from dideman.dide.models import Leave
    return render_template(request, Leave,
                           LeaveAdmin)

