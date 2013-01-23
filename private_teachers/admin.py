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

    list_display = ['lastname', 'firstname', 'profession', 'school']
    list_filter = ['profession__unified_profession', 'school']
    inlines = [WorkingPeriodInline]
    readonly_fields = ['total_experience']

admin.site.register(PrivateTeacher, PrivateTeacherAdmin)
admin.site.register(PrivateSchool)
