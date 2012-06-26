# -*- coding: utf-8 -*-
from django.contrib import admin
from overrides.admin import DideAdmin
from filters import (PermanentPostFilter, OrganizationServingFilter,
                     StudyFilter, DateHiredFilter, LeaveDateToFilter,
                     LeaveDateFromFilter, CurrentlyServesFilter,
                     NonPermanentCurrentlyServesFilter,
                     TransferedFilter, NextPromotionInRangeFilter)
from applications.filters import FinalisedFilter
from models import (TransferArea, Leave, Responsibility, Profession,
                    Promotion, NonPermanentType,
                    NonPermanent, Permanent, Employee, DegreeCategory,
                    SchoolType, School, OtherOrganization, PlacementType,
                    Placement, EmployeeLeave, EmployeeResponsibility,
                    EmployeeDegree, Child, Loan, SocialSecurity,
                    LoanCategory, Service, Settings, Application,
                    ApplicationSet, ApplicationChoices, ApplicationType)
from actions import CSVReport, FieldAction

from reports.permanent import permanent_docx_reports
from reports.leave import leave_docx_reports


class ApplicationChoiceInline(admin.TabularInline):
    model = ApplicationChoices
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


class ApplicationAdmin(DideAdmin):
    list_display = ['employee', 'set', 'finalised']
    list_filter = ['set__name', FinalisedFilter, 'employee__transfer_area',
                   'employee__profession__unified_profession']
    search_fields = ['employee__lastname']
    inlines = [ApplicationChoiceInline]

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
                           'date_start', 'date_end', 'address',
                           'identity_number', 'telephone_number1',
                           'telephone_number2', 'email',
                           'birth_date', 'hours_current',
                           'organization_serving', 'date_created']}),
        economic_fieldset]
    readonly_fields = ['last_placement', 'organization_serving',
                       'date_created']
    list_max_show_all = 10000
    list_per_page = 50
    actions = [FieldAction(u'Αναστολή υπηρέτησης', 'currently_serves',
                           lambda: False)]


class OtherOrganizationAdmin(DideAdmin):
    search_fields = ('name', )
    list_display = ('name', 'belongs')


class SchoolAdmin(OtherOrganizationAdmin):
    search_fields = ('name', 'code')
    list_display = ['name', 'transfer_area', 'type',
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
                                               DateHiredFilter, StudyFilter,
                                               CurrentlyServesFilter,
                                               NextPromotionInRangeFilter,
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
                    'organization_serving', 'study_years', 'serving_type',
                    'date_hired', 'order_hired', 'hours', 'is_permanent',
                    'has_permanent_post', 'currently_serves',
                    'recognised_experience', 'formatted_recognised_experience',
                    'payment_start_date_auto', 'payment_start_date_manual',
                    'rank', 'date_start', 'date_end', 'address',
                    'identity_number', 'inaccessible_school',
                    'telephone_number1', 'telephone_number2', 'email',
                    'birth_date', 'hours_current', 'date_created']}),
            economic_fieldset]
    search_fields = EmployeeAdmin.search_fields + ('registration_number',)
    readonly_fields = EmployeeAdmin.readonly_fields + \
        ['permanent_post', 'formatted_recognised_experience',
         'payment_start_date_auto', 'rank', 'profession_description',
         'date_created']

    actions = sorted([CSVReport(add=['permanent_post', 'organization_serving',
                                     'profession__description'])] + \
    permanent_docx_reports, key=lambda k: k.short_description)


class EmployeeLeaveAdmin(DideAdmin):

    class Media:
        css = {'all': ('/static/admin/css/widgets.css',)}
        js = ('/static/admin/js/calendar.js',
              '/static/admin/js/admin/DateTimeShortcuts.js', 'js/dide.js')

    search_fields = ('employee__lastname',)
    list_display = ('employee', 'profession', 'leave',
                    'date_to', 'date_from', 'date_issued', 'duration')
    list_filter = ('leave', 'employee__profession__unified_profession',
                   LeaveDateToFilter, LeaveDateFromFilter)
    actions = [CSVReport()] + sorted(leave_docx_reports,
                                     key=lambda k: k.short_description)


class NonPermanentAdmin(EmployeeAdmin):
    inlines = EmployeeAdmin.inlines + [PlacementInline,
               ServiceInline, LeaveInline, ResponsibilityInline]
    list_filter = EmployeeAdmin.list_filter + \
        (NonPermanentCurrentlyServesFilter, )


class SchoolTypeAdmin(DideAdmin):
    list_display = ('name', 'shift', 'category', 'rank')


admin.site.register(Permanent, PermanentAdmin)
admin.site.register(Profession, ProfessionAdmin)
admin.site.register(SchoolType, SchoolTypeAdmin)
admin.site.register(OtherOrganization, OtherOrganizationAdmin)
admin.site.register(School, SchoolAdmin)
admin.site.register(NonPermanent, NonPermanentAdmin)
admin.site.register(PlacementType, PlacementTypeAdmin)
admin.site.register(EmployeeLeave, EmployeeLeaveAdmin)
admin.site.register(Application, ApplicationAdmin)

admin.site.register((TransferArea, Leave, Responsibility, NonPermanentType,
                     SocialSecurity, LoanCategory, DegreeCategory, Settings,
                     ApplicationSet, ApplicationType, ApplicationChoices))
