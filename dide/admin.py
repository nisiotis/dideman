# -*- coding: utf-8 -*-
from django.contrib import admin
from django.forms.models import inlineformset_factory
from forms import SubstitutePlacementForm
from overrides.admin import DideAdmin
from filters import (PermanentPostFilter, OrganizationServingFilter,
                     StudyFilter, DateHiredFilter, LeaveDateToFilter,
                     LeaveDateFromFilter, CurrentlyServesFilter,
                     TransferedFilter, NextPromotionInRangeFilter,
                     EmployeeWithLeaveFilter, EmployeeWithOutLeaveFilter,
                     ServesInDideSchoolFilter, SubstituteAreaFilter,
                     SubstituteOrderFilter, SubstituteDateRangeFilter,
                     NonPermanentOrganizationServingFilter)
from applications.filters import FinalisedFilter
from models import (TransferArea, Leave, Responsibility, Profession,
                    Promotion, NonPermanentType,
                    NonPermanent, Permanent, Employee, DegreeCategory,
                    SchoolType, School, OtherOrganization, PlacementType,
                    Placement, EmployeeLeave, EmployeeResponsibility,
                    EmployeeDegree, Child, Loan, SocialSecurity,
                    LoanCategory, Service, Settings, ApplicationSet,
                    MoveInside, TemporaryPosition,
                    TemporaryPositionAllAreas, SubstitutePlacement,
                    SubstituteMinistryOrder, OrderedSubstitution,
                    ApplicationChoice, ApplicationType, )
from models import (RankCode, PaymentFileName, PaymentCategoryTitle,
                    PaymentReportType, PaymentCode)

from actions import CSVReport, FieldAction

from reports.permanent import permanent_docx_reports
from reports.leave import leave_docx_reports
from reports.nonpermanent import nonpermanent_docx_reports
from django.core import management


class PaymentFileNameAdmin(admin.ModelAdmin):
    readonly_fields = ['status', 'imported_records']
    list_display = ('description', 'status', 'imported_records')

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['xml_file', ] + self.readonly_fields
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        if (obj.imported_records == 0) or (obj.imported_records is None):
            obj.imported_records = 0
        obj.save()
        if not change:
            try:
                management.call_command('importxml', str(obj.id), verbosity=0)
            except:
                raise


class RankCodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'rank')


class PaymentCodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'description')


class PaymentReportTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'type')


class PaymentCategoryTitleAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')


class ApplicationChoiceInline(admin.TabularInline):
    model = ApplicationChoice
    extra = 0


class PromotionInline(admin.TabularInline):
    model = Promotion
    extra = 0


class PlacementInline(admin.TabularInline):
    model = Placement
    extra = 0


class PlacementTypeAdmin(DideAdmin):
    pass


class ServiceInline(admin.TabularInline):
    model = Service
    extra = 0


class SubstitutePlacementInline(admin.TabularInline):
    model = SubstitutePlacement
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        return inlineformset_factory(NonPermanent, SubstitutePlacement,
                                     form=SubstitutePlacementForm,
                                     fields=['organization', 'ministry_order',
                                             'date_from'],
                                     extra=SubstitutePlacementInline.extra)


class OrderedSubstitutionInline(admin.TabularInline):
    model = OrderedSubstitution
    extra = 0


class LeaveInline(admin.TabularInline):
    model = EmployeeLeave
    extra = 0


class DegreeInline(admin.TabularInline):
    model = EmployeeDegree
    extra = 0


class ResponsibilityInline(admin.TabularInline):
    model = EmployeeResponsibility
    extra = 0


class ChildInline(admin.TabularInline):
    model = Child
    extra = 0


class LoanInline(admin.TabularInline):
    model = Loan
    extra = 0


class PermanentInline(admin.TabularInline):
    model = Permanent
    extra = 0


class EmployeeInline(admin.TabularInline):
    model = Employee
    extra = 0


class ApplicationSetAdmin(DideAdmin):
    model = ApplicationSet

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('klass',) + self.readonly_fields
        return self.readonly_fields


class ApplicationAdmin(DideAdmin):
    list_display = ['employee', 'set', 'finalised',
                    'profession']
    list_filter = ['set__name', FinalisedFilter, 'employee__transfer_area',
                   'employee__profession__unified_profession']
    search_fields = ['employee__lastname']
    inlines = [ApplicationChoiceInline]
    actions = [CSVReport(add=['employee__profession__description',
                              'employee__profession__id',
                              'employee__permanent__permanent_post',
                              'employee__permanent__registration_number',
                              'employee__permanent__date_hired',
                              'join_choices'],
                         exclude=['parent'])]


class TemporaryPositionAdmin(ApplicationAdmin):
    pass


class MoveInsideAdmin(ApplicationAdmin):
    pass


class TemporaryPositionAllAreasAdmin(ApplicationAdmin):
    pass


economic_fieldset = (u'Οικονομικά στοιχεία', {
        'fields': ['vat_number', 'tax_office', 'bank', 'bank_account_number',
                   'iban', 'social_security_registration_number', 'before_93',
                   'has_family_subsidy', 'other_social_security',
                   'organization_paying']})


class EmployeeAdmin(DideAdmin):

    class Media:
        css = {'all': ('css/no-addanother-button.css',
                         '/static/admin/css/widgets.css')}
        js = ('/static/admin/js/admin/DateTimeShortcuts.js',
              '/static/admin/js/calendar.js', 'js/dide.js')

    list_display = ['lastname', 'firstname', 'fathername', 'profession',
                    'notes', 'transfer_area', 'organization_serving']
    list_filter = ('profession__unified_profession', 'transfer_area')
    search_fields = ('lastname', 'identity_number')
    inlines = [DegreeInline, ChildInline, LoanInline]
    fieldsets = [
        (u'Βασικά στοιχεία', {
                'fields': ['currently_serves', 'transfer_area',
                           'firstname', 'lastname', 'fathername',
                           'mothername', 'profession',
                           'date_end', 'address',
                           'profession_description',
                           'identity_number', 'telephone_number1',
                           'telephone_number2', 'email',
                           'birth_date', 'hours_current',
                           'organization_serving', 'date_created']}),
        economic_fieldset]
    readonly_fields = ['last_placement', 'organization_serving',
                       'date_created', 'profession_description']
    list_max_show_all = 10000
    list_per_page = 50
    actions = [FieldAction(u'Αναστολή υπηρέτησης', 'currently_serves',
                           lambda: False)]


class SubstituteMinistryOrderAdmin(DideAdmin):
    inlines = [OrderedSubstitutionInline]
    extra = 0


class OtherOrganizationAdmin(DideAdmin):
    search_fields = ('name', )
    list_display = ('name', 'belongs')


class SchoolAdmin(OtherOrganizationAdmin):
    search_fields = ('name', 'code')
    list_display = ['name', 'code', 'transfer_area', 'type',
                    'telephone_number', 'email']
    list_filter = ['transfer_area', 'type', 'type__shift',
                   'type__category', 'inaccessible']
    actions = [CSVReport()]


class ProfessionAdmin(DideAdmin):
    list_display = ('description', 'id', 'unified_profession')
    list_filter = ('unified_profession',)
    search_fields = ('description', 'id')


class PermanentAdmin(EmployeeAdmin):
    list_display = ['lastname', 'firstname', 'fathername',
                    'registration_number', 'profession', 'date_hired',
                    'permanent_post', 'organization_serving']
    inlines = EmployeeAdmin.inlines + [PromotionInline, PlacementInline,
                                       ServiceInline, LeaveInline,
                                       ResponsibilityInline]

    list_filter = EmployeeAdmin.list_filter + (TransferedFilter,
                                               'serving_type',
                                               DateHiredFilter,
                                               'has_permanent_post',
                                               StudyFilter,
                                               CurrentlyServesFilter,
                                               ServesInDideSchoolFilter,
                                               NextPromotionInRangeFilter,
                                               EmployeeWithLeaveFilter,
                                               EmployeeWithOutLeaveFilter,
                                               OrganizationServingFilter,
                                               PermanentPostFilter)
    list_per_page = 50
    fieldsets = [
        ('Στοιχεία μόνιμου', {
            'fields': [
                    'transfer_area',
                    'lastname', 'firstname', 'fathername', 'notes',
                    'registration_number', 'profession',
                    'profession_description', 'permanent_post',
                    'temporary_position', 'organization_serving',
                    'study_years', 'serving_type', 'date_hired',
                    'order_hired', 'hours', 'is_permanent',
                    'has_permanent_post', 'currently_serves',
                    'recognised_experience', 'formatted_recognised_experience',
                    'payment_start_date_auto', 'payment_start_date_manual',
                    'rank', 'date_end', 'address',
                    'identity_number', 'inaccessible_school',
                    'telephone_number1', 'telephone_number2', 'email',
                    'birth_date', 'hours_current', 'date_created']}),
            economic_fieldset]
    search_fields = EmployeeAdmin.search_fields + ('registration_number',)
    readonly_fields = EmployeeAdmin.readonly_fields + \
        ['permanent_post', 'temporary_position',
         'formatted_recognised_experience', 'payment_start_date_auto',
         'rank', 'profession_description',
         'date_created']

    actions = sorted([CSVReport(add=['permanent_post', 'organization_serving',
                                     'temporary_position',
                                     'profession__description',
                                     'payment_start_date_auto',
                                     'payment_start_date_manual',
                                     'formatted_recognised_experience',
                                     'rank__value', 'rank__date'])] + \
    permanent_docx_reports, key=lambda k: k.short_description)


class EmployeeLeaveAdmin(DideAdmin):

    class Media:
        css = {'all': ('/static/admin/css/widgets.css',)}
        js = ('/static/admin/js/calendar.js',
              '/static/admin/js/admin/DateTimeShortcuts.js', 'js/dide.js')

    search_fields = ('employee__lastname',)
    list_display = ('employee', 'profession', 'category', 'date_from',
                    'date_to', 'duration')
    list_filter = ('leave', 'employee__profession__unified_profession',
                   LeaveDateToFilter, LeaveDateFromFilter)
    actions = [CSVReport(add=['employee__profession__id',
                              'organization_serving', 'permanent_post'])] + \
        sorted(leave_docx_reports, key=lambda k: k.short_description)

    def print_leave(self, request, employeeleave_id):
        from django.http import HttpResponse
        leave_qs = EmployeeLeave.objects.filter(pk=employeeleave_id)
        if (len(leave_qs) != 1):
            return HttpResponse(u'Η άδεια δεν βρέθηκε')
        leave = leave_qs[0]

        for r in leave_docx_reports:
            if r.short_description == leave.leave.name:
                return r(self, request, leave_qs)
        return HttpResponse(u'Δεν βρέθηκε αναφορά για την άδεια')

    def get_urls(self):
        from django.conf.urls import patterns, url
        return super(EmployeeLeaveAdmin, self).get_urls() + \
            patterns('', url(r'^print/(\d+)$',
                          self.admin_site.admin_view(self.print_leave),
                          name='dide_employeeleave_print'))


class NonPermanentAdmin(EmployeeAdmin):
    list_display = ['lastname', 'firstname', 'fathername',
                    'profession', 'current_placement']
    list_per_page = 50
    fieldsets = [
        ('Στοιχεία μη-μόνιμου', {
            'fields': [
                    'lastname', 'firstname', 'fathername', 'mothername',
                    'current_transfer_area',
                    'notes', 'type', 'profession', 'profession_description',
                    'current_placement', 'study_years',
                    'identity_number', 'telephone_number1',
                    'telephone_number2', 'email', 'birth_date',
                    'date_created', 'pedagogical_sufficiency',
                    'social_security_number']}),
            economic_fieldset]
    readonly_fields = ['type', 'profession_description',
                       'current_placement', 'date_created',
                       'current_transfer_area']
    inlines = EmployeeAdmin.inlines + [SubstitutePlacementInline,
                                       ServiceInline, LeaveInline,
                                       ResponsibilityInline]
    list_filter = [SubstituteDateRangeFilter, SubstituteAreaFilter,
                   SubstituteOrderFilter, 'profession__unified_profession', NonPermanentOrganizationServingFilter]
    actions = sorted([CSVReport(add=['current_placement',
                                     'profession__description'])] + \
    nonpermanent_docx_reports, key=lambda k: k.short_description)


class SchoolTypeAdmin(DideAdmin):
    list_display = ('name', 'shift', 'category', 'rank')


map(lambda t: admin.site.register(*t), (
        (Permanent, PermanentAdmin),
        (Profession, ProfessionAdmin),
        (SchoolType, SchoolTypeAdmin),
        (SubstituteMinistryOrder, SubstituteMinistryOrderAdmin),
        (OtherOrganization, OtherOrganizationAdmin),
        (School, SchoolAdmin),
        (NonPermanent, NonPermanentAdmin),
        (PlacementType, PlacementTypeAdmin),
        (EmployeeLeave, EmployeeLeaveAdmin),
        (MoveInside, MoveInsideAdmin),
        (TemporaryPosition, TemporaryPositionAdmin),
        (TemporaryPositionAllAreas, TemporaryPositionAllAreasAdmin),
        (ApplicationSet, ApplicationSetAdmin),
        (PaymentCategoryTitle, PaymentCategoryTitleAdmin),
        (PaymentReportType, PaymentReportTypeAdmin),
        (PaymentFileName, PaymentFileNameAdmin),
        (RankCode, RankCodeAdmin),
        (PaymentCode, PaymentCodeAdmin)
        ))

admin.site.register((TransferArea, Leave, Responsibility, NonPermanentType,
                     SocialSecurity, LoanCategory, DegreeCategory, Settings,
                     ApplicationType))
