# -*- coding: utf-8 -*-
from overrides.admin import ModifierSimpleListFilter
from overrides.admin import DideAdmin
from django.contrib.admin.filters import SimpleListFilter
from models import (Organization, School, Permanent, DegreeCategory,
                    NonPermanent, EmployeeLeave, TransferArea,
                    SubstituteMinistryOrder)
import django.contrib.admin.views.main as views
import datetime
import re
from dideman.lib.date import current_year_date_to
from django.utils.translation import ugettext_lazy as _


class PermanentPostFilter(ModifierSimpleListFilter):
    title = u'Οργανική Θέση'
    parameter_name = 'organization__id'
    modifier_name = '_m_' + parameter_name
    lookup_param = parameter_name
    views.__dict__['IGNORED_PARAMS'] += [modifier_name]
    DideAdmin.add_filter_parameter(parameter_name)
    list_view = False

    def __init__(self, request, params, model, model_admin, *args, **kwargs):
        self.modifier_value = request.GET.get(self.modifier_name, u'AND')
        super(PermanentPostFilter, self).__init__(request, params, model,
                                                  model_admin)

    def lookups(self, request, model_admin):
        schools = School.objects.all()
        return ((s.id, s.name) for s in schools)

    def filter_param(self, queryset, query_dict):
        val = query_dict.get(self.parameter_name, None)
        if val:
            return queryset & \
                Permanent.objects.permanent_post_in_organization(int(val))
        else:
            return queryset

    def has_output(self):
        return True

    def used_params(self):
        return [self.parameter_name]


class TransferedFilter(ModifierSimpleListFilter):
    title = u'Έχει μετατεθεί'
    parameter_name = 'is_transfered'
    modifier_name = '_m_' + parameter_name
    lookup_param = parameter_name
    views.__dict__['IGNORED_PARAMS'] += [modifier_name]
    DideAdmin.add_filter_parameter(parameter_name)
    list_view = False

    def __init__(self, request, params, model, model_admin, *args, **kwargs):
        self.modifier_value = request.GET.get(self.modifier_name, u'AND')
        super(TransferedFilter, self).__init__(request, params, model,
                                                model_admin)

    def lookups(self, request, model_admin):
        return(('1', _('Yes')), ('2', _('No')))

    def filter_param(self, queryset, query_dict):
        val = query_dict.get(self.parameter_name, None)
        if val:
            if val == '1':
                return queryset & Permanent.objects.transfered()
            elif val == '2':
                return queryset & Permanent.objects.not_transfered()
        else:
            return queryset

    def has_output(self):
        return True

    def used_params(self):
        return [self.parameter_name]


class CurrentlyServesFilter(ModifierSimpleListFilter):
    title = u'Υπηρετεί στην Δ.Δ.Ε.Δ.'
    parameter_name = 'currently_serves'
    modifier_name = '_m_' + parameter_name
    lookup_param = parameter_name
    field = 'currently_serves'
    views.__dict__['IGNORED_PARAMS'] += [modifier_name]
    DideAdmin.add_filter_parameter(parameter_name)
    list_view = True

    def __init__(self, request, params, model, model_admin, *args, **kwargs):
        self.modifier_value = request.GET.get(self.modifier_name, u'AND')
        super(CurrentlyServesFilter, self).__init__(request, params, model,
                                                    model_admin)

    def lookups(self, request, model_admin):
        return  (('1', _('Yes')),
                ('0', _('No')),
                ('3', u'Όλοι'))

    def filter_param(self, queryset, query_dict, klass=Permanent):
        # value defaults to 1 so that not serving permanents are filtered out
        val = query_dict.get(self.parameter_name, 1)
        if val != '3':
            return queryset & klass.objects.filter(currently_serves=int(val))
        else:
            return queryset

    def has_output(self):
        return True

    def used_params(self):
        return [self.parameter_name]


class NonPermanentCurrentlyServesFilter(CurrentlyServesFilter):
    def filter_param(self, queryset, query_dict):
        return super(NonPermanentCurrentlyServesFilter, self).\
            filter_param(queryset, query_dict, NonPermanent)


class StudyFilter(ModifierSimpleListFilter):
    title = u'Σπουδές'
    parameter_name = 'study'
    modifier_name = '_m_' + parameter_name
    lookup_param = parameter_name
    views.__dict__['IGNORED_PARAMS'] += [modifier_name]
    DideAdmin.add_filter_parameter(parameter_name)
    list_view = False

    def __init__(self, request, params, model, model_admin, *args, **kwargs):
        self.modifier_value = request.GET.get(self.modifier_name, u'AND')
        super(StudyFilter, self).__init__(request, params, model, model_admin)

    def lookups(self, request, model_admin):
        degrees = DegreeCategory.objects.all().only('id', 'name')
        return ((d.id, d.name) for d in degrees)

    def filter_param(self, queryset, query_dict):
        val = query_dict.get(self.parameter_name, None)
        if val:
            return queryset & Permanent.objects.have_degree(val)
        else:
            return queryset

    def has_output(self):
        return True

    def used_params(self):
        return [self.parameter_name]


class OrganizationServingFilter(ModifierSimpleListFilter):
    title = u'Σχολείο υπηρεσίας'
    parameter_name = 'serving_organization__id'
    modifier_name = '_m_' + parameter_name
    lookup_param = parameter_name
    views.__dict__['IGNORED_PARAMS'] += [modifier_name]
    DideAdmin.add_filter_parameter(parameter_name)
    list_view = False

    def __init__(self, request, params, model, model_admin, *args, **kwargs):
        self.modifier_value = request.GET.get(self.modifier_name, u'AND')
        super(OrganizationServingFilter, self).__init__(request, params, model,
                                                        model_admin, *args,
                                                        **kwargs)

    def lookups(self, request, model_admin):
        organizations = Organization.objects.all()
        return ((o.id, o.name) for o in organizations)

    def filter_param(self, queryset, query_dict):
        val = query_dict.get(self.parameter_name, None)
        if val:
            return queryset & \
                Permanent.objects.serving_in_organization(int(val))
        else:
            return queryset

    def has_output(self):
        return True

    def used_params(self):
        return [self.parameter_name]


class FreeDateFieldListFilter(SimpleListFilter):
    template_name = 'free_date_filter'
    parameter_name = 'free_date_period'
    sep = '|'
    default_date_from = datetime.date(1950, 1, 1)
    default_date_to = datetime.date(2050, 12, 31)
    DideAdmin.add_filter_parameter(parameter_name)
    list_view = False

    def default_date_values(self):
        return [self.default_date_from, self.default_date_to]

    def __init__(self, request, *args, **kwargs):
        super(FreeDateFieldListFilter, self).__init__(request, *args, **kwargs)
        url_value = request.GET.get(self.parameter_name, '')
        if re.match('^\d{1,2}-\d{1,2}-\d{4}\|\d{1,2}-\d{1,2}-\d{4}',
                    url_value):
            try:
                self.date_from, self.date_to = \
                    map(lambda x:
                            datetime.datetime.strptime(x, '%d-%m-%Y').date(),
                    url_value.split('|'))
            except:
                self.date_from, self.date_to = self.default_date_values()
        else:
            self.date_from, self.date_to = self.default_date_values()
        self.url_from_value, self.url_to_value = \
            self.date_from.strftime('%d-%m-%Y'), \
            self.date_to.strftime('%d-%m-%Y')

    def used_params(self):
        return [self.parameter_name]

    def lookups(self, request, model_admin):
        return []

    def has_output(self):
        return True


class DateHiredFilter(FreeDateFieldListFilter):
    title = u'Ημερομηνία Διορισμού'
    parameter_name = 'date_hired_period'
    modifier_name = '_m_' + parameter_name
    lookup_param = parameter_name
    views.__dict__['IGNORED_PARAMS'].append(modifier_name)
    DideAdmin.add_filter_parameter(parameter_name)
    list_view = False

    def __init__(self, request, params, model, model_admin, *args, **kwargs):
        self.modifier_value = request.GET.get(self.modifier_name, u'AND')
        super(DateHiredFilter, self).__init__(request, params, model,
                                              model_admin, *args, **kwargs)

    def queryset(self, request, queryset):
        if [self.date_from, self.date_to] == self.default_date_values():
            return queryset
        else:
            return queryset.filter(date_hired__gte=self.date_from,
                                   date_hired__lte=self.date_to)


class LeaveDateToFilter(FreeDateFieldListFilter):
    title = u'Ημερομηνία Λήξης'
    parameter_name = 'leave_date_to'
    modifier_name = '_m_' + parameter_name
    lookup_param = parameter_name
    views.__dict__['IGNORED_PARAMS'].append(modifier_name)
    DideAdmin.add_filter_parameter(parameter_name)
    list_view = False

    def __init__(self, request, params, model, model_admin, *args, **kwargs):
        self.modifier_value = request.GET.get(self.modifier_name, u'AND')
        super(LeaveDateToFilter, self).__init__(request, params, model,
                                                model_admin, *args, **kwargs)

    def queryset(self, request, queryset):
        if [self.date_from, self.date_to] == self.default_date_values():
            return queryset
        else:
            return queryset.filter(date_to__gte=self.date_from,
                                   date_to__lte=self.date_to)


class EmployeeWithOutLeaveFilter(FreeDateFieldListFilter):
    title = u'Χωρίς Άδεια'
    parameter_name = 'ewo_leave_date_to'
    modifier_name = '_m_' + parameter_name
    lookup_param = parameter_name
    views.__dict__['IGNORED_PARAMS'].append(modifier_name)
    DideAdmin.add_filter_parameter(parameter_name)
    list_view = False

    def __init__(self, request, params, model, model_admin, *args, **kwargs):
        self.modifier_value = request.GET.get(self.modifier_name, u'AND')
        super(EmployeeWithOutLeaveFilter, self).__init__(request, params,
                                                         model, model_admin,
                                                         *args, **kwargs)

    def queryset(self, request, queryset):
        if [self.date_from, self.date_to] == self.default_date_values():
            return queryset
        else:
            return queryset.exclude(
                id__in=[obj.employee_id
                        for obj in EmployeeLeave.objects.date_range_intersect(
                        self.date_from, self.date_to)])


class EmployeeWithLeaveFilter(FreeDateFieldListFilter):
    title = u'Με Άδεια'
    parameter_name = 'ew_leave_date_to'
    modifier_name = '_m_' + parameter_name
    lookup_param = parameter_name
    views.__dict__['IGNORED_PARAMS'].append(modifier_name)
    DideAdmin.add_filter_parameter(parameter_name)
    list_view = False

    def __init__(self, request, params, model, model_admin, *args, **kwargs):
        self.modifier_value = request.GET.get(self.modifier_name, u'AND')
        super(EmployeeWithLeaveFilter, self).__init__(request, params,
                                                         model, model_admin,
                                                         *args, **kwargs)

    def queryset(self, request, queryset):
        if [self.date_from, self.date_to] == self.default_date_values():
            return queryset
        else:
            return queryset.filter(id__in=[obj.employee_id
                        for obj in EmployeeLeave.objects.date_range_intersect(
                        self.date_from, self.date_to)])


class ServesInDideSchoolFilter(ModifierSimpleListFilter):
    title = u'Υπηρετεί σε σχολείο της Δ.Δ.Ε.'
    parameter_name = 'serves_in_dde_sch'
    modifier_name = '_m_' + parameter_name
    lookup_param = parameter_name
    views.__dict__['IGNORED_PARAMS'] += [modifier_name]
    DideAdmin.add_filter_parameter(parameter_name)
    list_view = False

    def __init__(self, request, params, model, model_admin, *args, **kwargs):
        self.modifier_value = request.GET.get(self.modifier_name, u'AND')
        super(ServesInDideSchoolFilter, self).__init__(request, params, model,
                                                model_admin)

    def lookups(self, request, model_admin):
        return(('1', _('Yes')), ('2', _('No')))

    def filter_param(self, queryset, query_dict):
        val = query_dict.get(self.parameter_name, None)
        if val:
            if val == '1':
                return queryset & Permanent.objects.serves_in_dide_school()
            elif val == '2':
                return queryset & Permanent.objects.not_serves_in_dide_school()
        else:
            return queryset

    def has_output(self):
        return True

    def used_params(self):
        return [self.parameter_name]


class ServesInDideOrgFilter(ModifierSimpleListFilter):
    title = u'Υπηρετεί σε σχολείο/φορέα της Δ.Δ.Ε.'
    parameter_name = 'serves_in_dde_org'
    modifier_name = '_m_' + parameter_name
    lookup_param = parameter_name
    views.__dict__['IGNORED_PARAMS'] += [modifier_name]
    DideAdmin.add_filter_parameter(parameter_name)
    list_view = False

    def __init__(self, request, params, model, model_admin, *args, **kwargs):
        self.modifier_value = request.GET.get(self.modifier_name, u'AND')
        super(ServesInDideOrgFilter, self).__init__(request, params, model,
                                                model_admin)

    def lookups(self, request, model_admin):
        return(('1', _('Yes')), ('2', _('No')))

    def filter_param(self, queryset, query_dict):
        val = query_dict.get(self.parameter_name, None)
        if val:
            if val == '1':
                return queryset & Permanent.objects.serves_in_dide_org()
            elif val == '2':
                return queryset & Permanent.objects.not_serves_in_dide_org()
        else:
            return queryset

    def has_output(self):
        return True

    def used_params(self):
        return [self.parameter_name]


class LeaveDateFromFilter(FreeDateFieldListFilter):
    title = u'Ημερομηνία Έναρξης'
    parameter_name = 'leave_date_from'
    modifier_name = '_m_' + parameter_name
    lookup_param = parameter_name
    views.__dict__['IGNORED_PARAMS'].append(modifier_name)
    DideAdmin.add_filter_parameter(parameter_name)
    list_view = False

    def __init__(self, request, params, model, model_admin, *args, **kwargs):
        self.modifier_value = request.GET.get(self.modifier_name, u'AND')
        super(LeaveDateFromFilter, self).__init__(request, params, model,
                                                  model_admin, *args, **kwargs)

    def queryset(self, request, queryset):
        if [self.date_from, self.date_to] == self.default_date_values():
            return queryset
        else:
            return queryset.filter(date_from__gte=self.date_from,
                                   date_from__lte=self.date_to)


class NextPromotionInRangeFilter(FreeDateFieldListFilter):
    title = u'Ημερομηνία χορήγησης επόμενου Μ.Κ.'
    parameter_name = 'next_promotion_date'
    modifier_name = '_m_' + parameter_name
    lookup_param = parameter_name
    views.__dict__['IGNORED_PARAMS'].append(modifier_name)
    DideAdmin.add_filter_parameter(parameter_name)
    list_view = False

    def __init__(self, request, params, model, model_admin, *args, **kwargs):
        self.modifier_value = request.GET.get(self.modifier_name, u'AND')
        super(NextPromotionInRangeFilter, self).__init__(request, params,
                                                         model, model_admin,
                                                         *args, **kwargs)

    def queryset(self, request, queryset):
        if [self.date_from, self.date_to] == self.default_date_values():
            return queryset
        else:
            return Permanent.objects.next_promotion_in_range(self.date_from,
                                                             self.date_to)


class PaymentStartDateFilter(FreeDateFieldListFilter):
    title = u'Ημερομηνία Μισθολογικής Αφετηρίας'
    parameter_name = 'payment_start'
    modifier_name = '_m_' + parameter_name
    lookup_param = parameter_name
    views.__dict__['IGNORED_PARAMS'].append(modifier_name)
    DideAdmin.add_filter_parameter(parameter_name)
    list_view = False

    def __init__(self, request, params, model, model_admin, *args, **kwargs):
        self.modifier_value = request.GET.get(self.modifier_name, u'AND')
        super(PaymentStartDateFilter, self).__init__(request, params,
                                                         model, model_admin,
                                                         *args, **kwargs)

    def queryset(self, request, queryset):
        if [self.date_from, self.date_to] == self.default_date_values():
            return queryset
        else:
            ids = [p.id for p in queryset
                   if self.date_from <= \
                       p.payment_start_date_auto().python() <=\
                       self.date_to]
            print ids
            return queryset.filter(id__in=ids)


class SubstituteAreaFilter(ModifierSimpleListFilter):
    title = u'Περιοχή τοποθέτησης'
    parameter_name = u'position_area'
    modifier_name = '_m_' + parameter_name
    lookup_param = parameter_name
    views.__dict__['IGNORED_PARAMS'].append(modifier_name)
    DideAdmin.add_filter_parameter(parameter_name)
    list_view = True

    def __init__(self, request, params, model, model_admin, *args, **kwargs):
        self.modifier_value = request.GET.get(self.modifier_name, u'AND')
        super(SubstituteAreaFilter, self).__init__(request, params, model,
                                                   model_admin)

    def lookups(self, request, model_admin):
        return [(a.id, a.name) for a in TransferArea.objects.all()]

    def filter_param(self, queryset, query_dict):
        val = query_dict.get(self.parameter_name, None)
        if val:
            val = int(val)
            return queryset & NonPermanent.objects.\
                substitutes_in_transfer_area(val)
        else:
            return queryset

    def has_output(self):
        return True

    def used_params(self):
        return [self.parameter_name]


class SubstituteOrderFilter(ModifierSimpleListFilter):
    title = u'Υπουργική απόφαση'
    parameter_name = u'date_order'
    modifier_name = '_m_' + parameter_name
    lookup_param = parameter_name
    views.__dict__['IGNORED_PARAMS'].append(modifier_name)
    DideAdmin.add_filter_parameter(parameter_name)
    list_view = True

    def __init__(self, request, params, model, model_admin, *args, **kwargs):
        self.modifier_value = request.GET.get(self.modifier_name, u'AND')
        super(SubstituteOrderFilter, self).__init__(request, params, model,
                                                   model_admin)

    def lookups(self, request, model_admin):
        return [(a.id, '%s - %s' % (a.order, a.date)) \
                    for a in SubstituteMinistryOrder.objects.all()]

    def filter_param(self, queryset, query_dict):
        val = query_dict.get(self.parameter_name, None)
        if val:
            return queryset & NonPermanent.objects.substitutes_in_order(val)
        else:
            return queryset

    def has_output(self):
        return True

    def used_params(self):
        return [self.parameter_name]


class SubstituteDateRangeFilter(FreeDateFieldListFilter):
    title = u'Χρονικό διάστημα εργασίας'
    parameter_name = 'sub_order_date'
    modifier_name = '_m_' + parameter_name
    lookup_param = parameter_name
    views.__dict__['IGNORED_PARAMS'].append(modifier_name)
    DideAdmin.add_filter_parameter(parameter_name)
    list_view = True

    def __init__(self, request, params, model, model_admin, *args, **kwargs):
        self.modifier_value = request.GET.get(self.modifier_name, u'AND')
        super(SubstituteDateRangeFilter, self).__init__(request, params,
                                                         model, model_admin,
                                                         *args, **kwargs)

    def queryset(self, request, queryset):
        if [self.date_from, self.date_to] == self.default_date_values():
            return queryset
        else:
            return queryset & NonPermanent.objects.substitutes_in_date_range(
                self.date_from, self.date_to)


class NonPermanentOrganizationServingFilter(OrganizationServingFilter):
    title = u'Προσωρινή Τοποθέτηση'

    def lookups(self, request, model_admin):
        schools = School.objects.all()
        return ((s.id, s.name) for s in schools)

    def filter_param(self, queryset, query_dict):
        val = query_dict.get(self.parameter_name, None)
        if val:
            return queryset & \
                NonPermanent.objects.temporary_post_in_organization(int(val))
        else:
            return queryset


class NonPermanentWithTotalExtraPosition(ModifierSimpleListFilter):
    title = u'Με ολική διάθεση'
    parameter_name = 'with_total'
    modifier_name = '_m_' + parameter_name
    lookup_param = parameter_name
    views.__dict__['IGNORED_PARAMS'].append(modifier_name)
    DideAdmin.add_filter_parameter(parameter_name)

    def __init__(self, request, params, model, model_admin, *args, **kwargs):
        self.modifier_value = request.GET.get(self.modifier_name, u'AND')
        super(NonPermanentWithTotalExtraPosition, self).\
            __init__(request, params, model, model_admin, *args, **kwargs)

    def lookups(self, request, model_admin):
        return(('1', _('Yes')), ('2', _('No')))

    def filter_param(self, queryset, query_dict):
        val = query_dict.get(self.parameter_name, None)
        if val:
            if val == '1':
                return queryset & NonPermanent.objects.with_total_extra_position()
            elif val == '2':
                return queryset & NonPermanent.objects.with_total_extra_position(exclude=True)
        else:
            return queryset

    def has_output(self):
        return True

    def used_params(self):
        return [self.parameter_name]
