# -*- coding: utf-8 -*-
from overrides.admin import ModifierSimpleListFilter
from overrides.admin import DideAdmin
from django.contrib.admin.filters import SimpleListFilter, FieldListFilter
from models import (Organization, School, Permanent, DegreeCategory,
                    NonPermanent, EmployeeLeave, TransferArea, Island,
                    AdministrativeLeave, PermanentLeave,
                    SubstituteMinistryOrder, Leave, NonPermanentLeave)
import django.contrib.admin.views.main as views
import datetime
import re
from django.utils.translation import ugettext_lazy as _


class PermanentPostFilter(ModifierSimpleListFilter):
    title = u'Σχολείο Οργανικής'
    parameter_name = 'organization__id'
    list_view = False

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
        
        
class PermanentLeaveFilter(ModifierSimpleListFilter):
    title = u'Κατηγορία άδειας'
    parameter_name = 'leave__id'
    list_view = True
    
    def lookups(self, request, model_admin):
        leaves = Leave.objects.filter(for_non_permanents=False)
        return ((l.id, l.name) for l in leaves)

    def filter_param(self, queryset, query_dict):
        val = query_dict.get(self.parameter_name, None)
        if val:
            return queryset & \
                PermanentLeave.objects.filter(leave__id=int(val))
        else:
            return queryset

class AdministrativeLeaveFilter(ModifierSimpleListFilter):
    title = u'Κατηγορία άδειας'
    parameter_name = 'leave__id'
    list_view = True

    def lookups(self, request, model_admin):
	leaves = Leave.objects.filter(for_non_permanents=False)
        return ((l.id, l.name) for l in leaves)

    def filter_param(self, queryset, query_dict):
	val = query_dict.get(self.parameter_name, None)
	if val:
            return queryset & \
                AdministrativeLeave.objects.filter(leave__id=int(val))
        else:
            return queryset


class NonPermanentLeaveFilter(ModifierSimpleListFilter):
    title = u'Κατηγορία άδειας'
    parameter_name = 'leave__id'
    list_view = True
    
    def lookups(self, request, model_admin):
        leaves = Leave.objects.filter(for_non_permanents=False)
        return ((l.id, l.name) for l in leaves)

    def filter_param(self, queryset, query_dict):
        val = query_dict.get(self.parameter_name, None)
        if val:
            return queryset & \
                NonPermanentLeave.objects.filter(leave__id=int(val))
        else:
            return queryset
        
class PermanentPostInIslandFilter(ModifierSimpleListFilter):
    title = u'Νησί Οργανικής'
    parameter_name = 'island__id'
    list_view = False

    def lookups(self, request, model_admin):
        islands = Island.objects.all()
        return ((i.id, i.name) for i in islands)

    def filter_param(self, queryset, query_dict):
        val = query_dict.get(self.parameter_name, None)
        if val:
            return queryset & \
                Permanent.objects.permanent_post_in_island(int(val))
        else:
            return queryset


class TemporaryPostFilter(ModifierSimpleListFilter):
    title = u'Σχολείο Προσωρινής'
    parameter_name = 'temp_organization__id'
    list_view = False

    def lookups(self, request, model_admin):
        schools = School.objects.all()
        return ((s.id, s.name) for s in schools)

    def filter_param(self, queryset, query_dict):
        val = query_dict.get(self.parameter_name, None)
        if val:
            return queryset & \
                Permanent.objects.temporary_post_in_organization(int(val))
        else:
            return queryset


class TransferedFilter(ModifierSimpleListFilter):
    title = u'Έχει μετατεθεί'
    parameter_name = 'is_transfered'

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


class ServingTypeFilter(ModifierSimpleListFilter):
    title = u"Ανήκει οργανικά στην Δ.Δ.Ε."
    parameter_name = "serving_type"

    def lookups(self, request, model_admin):
        return(('1', _('Yes')), ('2', _('No')))

    def filter_param(self, queryset, query_dict):
        val = query_dict.get(self.parameter_name, None)
        if val:
            if val == '1':
                return queryset & Permanent.objects.filter(serving_type=val)
            elif val == '2':
                return queryset & Permanent.objects.exclude(serving_type=1)
        else:
            return queryset


class RecognisedExperienceN44522017Filter(ModifierSimpleListFilter):
    title = u'Έχει προϋπηρεσία Ν.4452/2017 (Βαθμολογική);'
    parameter_name = 'has_experience_n4452_2017'

    def lookups(self, request, model_admin):
        return(('1', _('Yes')), ('0', _('No')))

    def filter_param(self, queryset, query_dict):
        val = query_dict.get(self.parameter_name, None)
        if val == '1':            
            return queryset & Permanent.objects.extra_rank_service()
        elif val == '0':
            qs = Permanent.objects.extra_rank_service()
            return queryset & Permanent.objects.exclude(pk__in=qs)
        else:
            return queryset



class CurrentlyServesFilter(ModifierSimpleListFilter):
    title = u'Είναι ενεργός'
    parameter_name = 'currently_serves'

    def lookups(self, request, model_admin):
        return  (('1', _('Yes')),
                ('0', _('No')),
                ('3', u'Όλοι'))

    def filter_param(self, queryset, query_dict):
        # value defaults to 1 so that not serving permanents are filtered out
        val = query_dict.get(self.parameter_name, 1)
        if val != '3':
            return queryset & queryset.model.objects.filter(currently_serves=int(val))
        else:
            return queryset


class NonPermanentCurrentlyServesFilter(CurrentlyServesFilter):
    def filter_param(self, queryset, query_dict):
        return super(NonPermanentCurrentlyServesFilter, self).\
            filter_param(queryset, query_dict, NonPermanent)


class StudyFilter(ModifierSimpleListFilter):
    title = u'Σπουδές'
    parameter_name = 'study'
    list_view = False

    def lookups(self, request, model_admin):
        degrees = DegreeCategory.objects.all().only('id', 'name')
        return ((d.id, d.name) for d in degrees)

    def filter_param(self, queryset, query_dict):
        val = query_dict.get(self.parameter_name, None)
        if val:
            return queryset & Permanent.objects.have_degree(val)
        else:
            return queryset

class OrganizationPayingFilter(ModifierSimpleListFilter):
    title = u'Οργανισμός Μισθοδοσίας'
    parameter_name = 'organization_paying'
    list_view = False

    def lookups(self, request, model_admin):
        return [(o.id, o.name) for o in Organization.objects.only('id', 'name').filter(id__in=Permanent.objects.values('organization_paying_id'))]


class OrganizationServingFilter(ModifierSimpleListFilter):
    title = u'Σχολείο υπηρεσίας'
    parameter_name = 'serving_organization__id'
    list_view = False

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

class IslandServingFilter(ModifierSimpleListFilter):
    title = u'Νησί υπηρεσίας'
    parameter_name = 'serving_island__id'
    list_view = False

    def lookups(self, request, model_admin):
        islands = Island.objects.all()
        return ((i.id, i.name) for i in islands)

    def filter_param(self, queryset, query_dict):
        val = query_dict.get(self.parameter_name, None)
        if val:
            return queryset & \
                Permanent.objects.serving_in_island(int(val))
        else:
            return queryset

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
        self.modifier_name = '_m_' + self.parameter_name
        self.lookup_param = self.parameter_name
        views.__dict__['IGNORED_PARAMS'].append(self.modifier_name)
        DideAdmin.add_filter_parameter(self.parameter_name)

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

    def queryset(self, request, queryset):
        if [self.date_from, self.date_to] == self.default_date_values():
            return queryset
        else:
            return queryset.filter(date_hired__gte=self.date_from,
                                   date_hired__lte=self.date_to)


class LeaveDateToFilter(FreeDateFieldListFilter):
    title = u'Ημερομηνία Λήξης'
    parameter_name = 'leave_date_to'

    def queryset(self, request, queryset):
        if [self.date_from, self.date_to] == self.default_date_values():
            return queryset
        else:
            return queryset.filter(date_to__gte=self.date_from,
                                   date_to__lte=self.date_to)


class EmployeeWithOutLeaveFilter(FreeDateFieldListFilter):
    title = u'Χωρίς Άδεια'
    parameter_name = 'ewo_leave_date_to'

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

    def queryset(self, request, queryset):
        if [self.date_from, self.date_to] == self.default_date_values():
            return queryset
        else:
            return queryset.filter(id__in=[obj.employee_id
                        for obj in EmployeeLeave.objects.date_range_intersect(
                        self.date_from, self.date_to)])


class OnServiceFilter(ModifierSimpleListFilter):
    title = u'Υπηρετεί με θητεία.'
    parameter_name = 'on_service'

    def lookups(self, request, model_admin):
        return(('1', _('Yes')), ('2', _('No')))

    def filter_param(self, queryset, query_dict):
        val = query_dict.get(self.parameter_name, None)
        if val:
            if val == '1':
                return queryset & Permanent.objects.on_service()
            elif val == '2':
                return queryset & Permanent.objects.on_service(exclude=True)
        else:
            return queryset

class ServesInDideSchoolFilter(ModifierSimpleListFilter):
    title = u'Υπηρετεί σε σχολείο της Δ.Δ.Ε.'
    parameter_name = 'serves_in_dde_sch'

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


class ServesInDideOrgFilter(ModifierSimpleListFilter):
    title = u'Υπηρετεί σε σχολείο/φορέα της Δ.Δ.Ε.'
    parameter_name = 'serves_in_dde_org'
    list_view = True

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


class LeaveDateFromFilter(FreeDateFieldListFilter):
    title = u'Ημερομηνία Έναρξης'
    parameter_name = 'leave_date_from'

    def queryset(self, request, queryset):
        if [self.date_from, self.date_to] == self.default_date_values():
            return queryset
        else:
            return queryset.filter(date_from__gte=self.date_from,
                                   date_from__lte=self.date_to)


class BirthdateFilter(FreeDateFieldListFilter):
    title = u'Ημερομηνία Γέννησης'
    parameter_name = 'bithdate'

    def queryset(self, request, queryset):
        if [self.date_from, self.date_to] == self.default_date_values():
            return queryset
        else:
            return queryset.filter(birth_date__gte=self.date_from,
                                   birth_date__lte=self.date_to)


class NextPromotionInRangeFilter(FreeDateFieldListFilter):
    title = u'Ημερομηνία χορήγησης επόμενου Μ.Κ.'
    parameter_name = 'next_promotion_date'

    def queryset(self, request, queryset):
        if [self.date_from, self.date_to] == self.default_date_values():
            return queryset
        else:
            return Permanent.objects.next_promotion_in_range(self.date_from,
                                                             self.date_to)


class NextHoursReductionFilter(FreeDateFieldListFilter):
    title = u'Ημερομηνία επόμενης μείωσης ωραρίου'
    parameter_name = 'next_hours_reduction_date'

    def queryset(self, request, queryset):
        if [self.date_from, self.date_to] == self.default_date_values():
            return queryset
        else:
            return queryset.filter(id__in=Permanent.objects.next_hours_reduction_in_range(self.date_from,
                                                                                          self.date_to))


class PaymentStartDateFilter(FreeDateFieldListFilter):
    title = u'Ημερομηνία Μισθολογικής Αφετηρίας'
    parameter_name = 'payment_start'

    def queryset(self, request, queryset):
        if [self.date_from, self.date_to] == self.default_date_values():
            return queryset
        else:
            ids = [p.id for p in queryset
                   if self.date_from <= \
                       p.payment_start_date_auto().python() <=\
                       self.date_to]
            return queryset.filter(id__in=ids)


class SubstituteAreaFilter(ModifierSimpleListFilter):
    title = u'Περιοχή τοποθέτησης'
    parameter_name = u'position_area'
    list_view = True

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


class SubstituteOrderFilter(ModifierSimpleListFilter):
    title = u'Υπουργική απόφαση'
    parameter_name = u'date_order'
    list_view = True

    def lookups(self, request, model_admin):
        """ only last two years"""
        year = datetime.date.today().year
        return [(a.id, '%s - %s' % (a.order, a.date)) \
                    for a in SubstituteMinistryOrder.objects.filter(date__gte="%s-01-01" % (year - 1))]

    def filter_param(self, queryset, query_dict):
        val = query_dict.get(self.parameter_name, None)
        if val:
            return queryset & NonPermanent.objects.substitutes_in_order(val)
        else:
            return queryset


class SubstituteDateRangeFilter(FreeDateFieldListFilter):
    title = u'Χρονικό διάστημα εργασίας'
    parameter_name = 'sub_order_date'
    list_view = True

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
    list_view = True

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
