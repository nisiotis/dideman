# -*- coding: utf-8 -*-
from dideman.dide.actions import CSVReport
from django.contrib import admin
from dideman.dide.overrides.admin import DideAdmin
from dideman.private_teachers.models import *
from dideman.dide.admin import DegreeInline
from dideman.dide.actions import EmployeeBecome
from dideman.dide.models import Permanent, NonPermanent, Administrative, Promotion

to_permanent = EmployeeBecome('Μετατροπή σε Μόνιμο', Permanent)
to_non_permanent = EmployeeBecome('Μετατροπή σε Αναπληρωτή', NonPermanent)
to_private_teacher = EmployeeBecome('Μετατροπή σε Ιδιωτικό', PrivateTeacher)
to_administrative = EmployeeBecome('Μετατροπή σε Διοικητικό', Administrative)

#to_permanent = None
#to_non_permanent = None
#to_private_teacher = None
#to_administrative = None

class LeaveWithoutPayInline(admin.TabularInline):
    model = LeaveWithoutPay
    extra = 0

class WorkingPeriodInline(admin.TabularInline):
    model = WorkingPeriod
    extra = 0

class PromotionInline(admin.TabularInline):
    model = Promotion
    extra = 0

class PrivateTeacherAdmin(DideAdmin):
    class Media:
        js = ('js/dide.js', )


    actions = [#to_permanent, to_non_permanent, to_administrative,
        CSVReport(add=["total_experience", "total_service", "rank",
                              "next_rank_date", 'total_service_311215'])]
    list_display = ['lastname', 'firstname', 'profession', 'school', 'total_service_311215', 'active']
    list_filter = ['profession__unified_profession', 'school', 'active']
    search_fields = ('lastname', 'identity_number')

    fieldsets = [
        ('Γενικά Στοιχεία', {
            'fields': [
                    'lastname', 'firstname', 'fathername', 'sex', 'profession',
                    'profession_description', 'series_number',
                    'total_experience', 'total_service', 'total_service_today', 'total_service_311215', 
                    'rank', 'next_rank_date',
                    'school', 'current_placement_date', 'current_hours',
                    'identity_number', 'telephone_number1',
                    'telephone_number2', 'email', 'birth_date', 'not_service_days',
                    'active', 'date_created']}),
        (u'Οικονομικά στοιχεία', {
                'fields': ['vat_number', 'tax_office', 'bank',
                           'bank_account_number', 'iban',
                           'social_security_registration_number']})]

    readonly_fields = ['organization_serving', 'total_experience',
                       'total_service', 'total_service_today', 'total_service_311215',
                       'date_created',
                       'profession_description', 'rank', 'next_rank_date']
    inlines = [DegreeInline, WorkingPeriodInline, PromotionInline, LeaveWithoutPayInline]

admin.site.register(PrivateTeacher, PrivateTeacherAdmin)
admin.site.register(PrivateSchool)
