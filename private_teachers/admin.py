# -*- coding: utf-8 -*-
from django.contrib import admin
from dideman.dide.overrides.admin import DideAdmin
from dideman.private_teachers.models import *


class WorkingPeriodInline(admin.TabularInline):
    model = WorkingPeriod
    extra = 0


class PrivateTeacherAdmin(DideAdmin):
    class Media:
        js = ('js/dide.js', )

    list_display = ['lastname', 'firstname', 'profession', 'school', 'active']
    list_filter = ['profession__unified_profession', 'school', 'active']
    fieldsets = [
        ('Γενικά Στοιχεία', {
            'fields': [
                    'lastname', 'firstname', 'fathername', 'sex', 'profession',
                    'profession_description', 'total_experience',
                    'total_service', 'school', 'current_placement_date',
                    'current_hours',
                    'identity_number', 'telephone_number1',
                    'telephone_number2', 'email', 'birth_date', 'no_pay_days',
                    'active', 'date_created']}),
        (u'Οικονομικά στοιχεία', {
                'fields': ['vat_number', 'tax_office', 'bank',
                           'bank_account_number', 'iban',
                           'social_security_registration_number']})]

    readonly_fields = ['organization_serving', 'total_experience',
                       'total_service', 'date_created',
                       'profession_description']
    inlines = [WorkingPeriodInline]

admin.site.register(PrivateTeacher, PrivateTeacherAdmin)
admin.site.register(PrivateSchool)
