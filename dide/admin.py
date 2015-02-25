# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from dideman.private_teachers.models import PrivateTeacher
from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse
from django.forms.models import inlineformset_factory
from django.template.response import TemplateResponse
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.forms import ModelForm
from django.forms import ModelChoiceField
from forms import SubstitutePlacementForm, PaymentFileNameMassForm, SchoolCommissionForm
from overrides.admin import DideAdmin
from filters import *
from applications.filters import FinalisedFilter
from models import (TransferArea, Island, Leave, Responsibility, Profession,
                    Promotion, NonPermanentType, Administrative,
                    NonPermanent, Permanent, Employee, DegreeCategory,
                    SchoolType, School, OtherOrganization, PlacementType,
                    Placement, EmployeeLeave, EmployeeResponsibility,
                    NonPermanentLeave, LeavePeriod,
                    EmployeeDegree, Child, Loan, SocialSecurity,
                    LoanCategory, Service, Settings, ApplicationSet,
                    MoveInside, TemporaryPosition,
                    TemporaryPositionAllAreas, SubstitutePlacement,
                    SubstituteMinistryOrder, OrderedSubstitution,
                    ApplicationChoice, ApplicationType, SchoolCommission,
                    DegreeOrganization)
from models import (RankCode, PaymentFileName, PaymentCategoryTitle,
                    PaymentReportType, PaymentCode, PaymentFilePDF)
from actions import (CSVEconomicsReport, CSVReport, FieldAction, XMLReadAction,
                     CreatePDF, PDFReadAction, DeleteAction, timestamp, 
                     EmployeeBecome, HideMassReports, ShowMassReports)
from reports.permanent import permanent_docx_reports
from reports.leave import leave_docx_reports
from reports.nonpermanent import nonpermanent_docx_reports
from django.utils.translation import ugettext_lazy
from dideman import settings
from django.utils.encoding import force_unicode

import zipfile, os


class PaymentFilePDFAdmin(DideAdmin):
    readonly_fields = ['status', 'extracted_files']
    list_display = ('description', 'status', 'extracted_files')
    search_fields = ('description',)
    actions = [PDFReadAction(u'Δημιουργία PDF')]


    def read_pdf(pdf_file, desc):
        pass

    def save_model(self, request, obj, form, change):
        pf = force_unicode(obj.pdf_file.name, 'cp737', 'ignore')
        if pf[-4:] == ".pdf":
            obj.save()

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['pdf_file' ] + self.readonly_fields                
        return self.readonly_fields



class PaymentFileNameAdmin(DideAdmin):
    readonly_fields = ['status', 'imported_records']
    list_display = ('description', 'status', 'imported_records', 'taxed')
    search_fields = ('description',)

    actions = [XMLReadAction(u'Ανάγνωση XML')]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            if obj.status:
                return ['xml_file', 'taxed', ] + self.readonly_fields
            else:
                return ['xml_file', ] + self.readonly_fields                
        return self.readonly_fields

    def admin_add_zip(self, request):
        opts = self.model._meta
        form = PaymentFileNameMassForm
        title = u"Προσθήκη αρχείου ZIP"

        if request.POST:
            form = PaymentFileNameMassForm(request.POST, request.FILES)
            if form.is_valid():
                if zipfile.is_zipfile(request.FILES['xml_file']):
                    zf = zipfile.ZipFile(request.FILES['xml_file'], 'r')
                    xml_li = [f for f in zf.namelist() if f.lower().endswith('.xml')]
                    for file in xml_li:
                        taxedfound = 0
                        t = timestamp()
                        f = open(os.path.join(settings.MEDIA_ROOT,'xmlfiles','fromzipfile%s.xml' % t),"wb")
                        f.write(zf.read(file))
                        f.close()
                        if request.POST.get('taxed'):
                            taxedfound = 1
                        pf = PaymentFileName(xml_file='xmlfiles/fromzipfile%s.xml' % t,
                                             description='%s %s' % (request.POST['description'], force_unicode(file, 'cp737', 'ignore')[:-4]),
                                             status=0, taxed=taxedfound)
                        pf.save()

                    msg = u'Το αρχείο %s περιείχε %s xml αρχεία.' % (request.FILES['xml_file'], len(xml_li))

                    self.message_user(request, msg)
                    post_url = reverse('admin:%s_%s_changelist' %
                                       (opts.app_label, opts.module_name),
                                       current_app=self.admin_site.name)
                    return HttpResponseRedirect(post_url)
                else:
                    msg = u"Το αρχείο δεν είναι μορφής ZIP."
                    messages.error(request, msg)

        media = self.media
        context = {
            "title": title,
            "opts": opts,
            "form": form,
            'media': media,
            "app_label": opts.app_label,
            'errors': helpers.AdminErrorList(form, []),
            'action_name': u'Προσθήκη αρχείου ZIP',
            }

        # Display the confirmation page
        return TemplateResponse(request,
                                'admin/add_zip_file.html',
                                context,
                                )


    def get_urls(self):
        urls = super(PaymentFileNameAdmin, self).get_urls()
        my_urls = patterns('',
            url(
                r'add_zip',
                self.admin_site.admin_view(self.admin_add_zip),
                name='admin_add_zip',
            ),
        )
        return my_urls + urls


class RankCodeAdmin(DideAdmin):
    list_display = ('id', 'rank')


class PaymentCodeAdmin(DideAdmin):
    list_display = ('id', 'description', 'group_name', 'calc_type')
    # add search field
    search_fields = ('id', 'description', b'group_name')


class PaymentReportTypeAdmin(DideAdmin):
    list_display = ('id', 'type')


class PaymentCategoryTitleAdmin(DideAdmin):
    list_display = ('id', 'title')
    search_fields = ('title',)


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
                                             'date_from', 'date_to'],
                                     extra=SubstitutePlacementInline.extra)


class OrderedSubstitutionInline(admin.TabularInline):
    model = OrderedSubstitution
    extra = 0


class LeaveInline(admin.TabularInline):
    model = EmployeeLeave
    extra = 0



class LeavePeriodInline(admin.TabularInline):
    model = LeavePeriod
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
                   'organization_paying', 'show_mass_pay']})

to_permanent = EmployeeBecome('Μετατροπή σε Μόνιμο', Permanent)
to_non_permanent = EmployeeBecome('Μετατροπή σε Αναπληρωτή', NonPermanent)
to_private_teacher = EmployeeBecome('Μετατροπή σε Ιδιωτικό', PrivateTeacher)
to_administrative = EmployeeBecome('Μετατροπή σε Διοικητικό', Administrative)

class EmployeeAdmin(DideAdmin):

    class Media:
        css = {'all': ('css/no-addanother-button.css',
                         '/static/admin/css/widgets.css')}
        js = ('/static/admin/js/admin/DateTimeShortcuts.js',
              '/static/admin/js/calendar.js', 'js/dide.js')

    list_display = ['lastname', 'firstname', 'fathername', 'profession',
                    'notes', 'transfer_area', 'organization_serving']
    list_filter = ('profession__unified_profession', 'transfer_area')
    search_fields = ('lastname', 'identity_number', 'vat_number')
    inlines = [DegreeInline, ChildInline, LoanInline]
    fieldsets = [
        (u'Βασικά στοιχεία', {
                'fields': ['currently_serves', 'transfer_area',
                           'firstname', 'lastname', 'fathername',
                           'mothername',  'profession',
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
    actions = [FieldAction(u'Αναστολή υπηρέτησης', 'currently_serves', lambda: False),
               ShowMassReports(u'Εμφάνιση Μισθοδοτιών Καταστάσεων'),               
               HideMassReports(u'Απόκρυψη Μισθοδοτιών Καταστάσεων'),
               CSVEconomicsReport(add=[])]


class SubstituteMinistryOrderAdmin(DideAdmin):
    list_display = ['order', 'date', 'web_code']
    search_fields = ['order', 'date', 'web_code']
    inlines = [OrderedSubstitutionInline]
    extra = 0


class OtherOrganizationAdmin(DideAdmin):
    search_fields = ('name', )
    list_display = ('name', 'belongs')
    
class LeaveAdmin(DideAdmin):
    search_fields = ('name', )
    list_display = ('name', 'type', 'for_non_permanents')


class SchoolCommissionAdmin(DideAdmin):
    form = SchoolCommissionForm
    search_fields= ('municipality', )
    list_display = ('municipality', 'vat_number', 'tax_office')
    actions = [CSVReport()]

class SchoolAdmin(OtherOrganizationAdmin):
    search_fields = ('name', 'code')
    list_display = ['name', 'code', 'transfer_area', 'island', 'type',
                    'telephone_number', 'email']
    list_filter = ['transfer_area', 'island', 'type', 'type__shift',
                   'type__category', 'inaccessible']

    readonly_fields = ('commission_data', )
    actions = [CSVReport(add=['commission_data'])]


class ProfessionAdmin(DideAdmin):
    list_display = ('description', 'id', 'unified_profession')
    list_filter = ('unified_profession',)
    search_fields = ('description', 'id')


class PermanentAdmin(EmployeeAdmin):
    list_display = ['lastname', 'firstname', 'fathername',
                    'registration_number', 'profession', 'date_hired',
                    'permanent_post', 'organization_serving']
    inlines = EmployeeAdmin.inlines + [PromotionInline, PlacementInline,
                                       ServiceInline, LeaveInline, ResponsibilityInline]

    list_filter = EmployeeAdmin.list_filter + (OrganizationServingFilter,
                                               IslandServingFilter,
                                               PermanentPostFilter,
                                               PermanentPostInIslandFilter,
                                               TemporaryPostFilter,
                                               ServingTypeFilter,
                                               ServesInDideSchoolFilter,
                                               OrganizationPayingFilter,
                                               ServesInDideOrgFilter,
                                               OnServiceFilter,
                                               'has_permanent_post',
                                               StudyFilter,
                                               TransferedFilter,
                                               CurrentlyServesFilter,
                                               BirthdateFilter,
                                               DateHiredFilter,
                                               PaymentStartDateFilter,
                                               NextPromotionInRangeFilter,
                                               EmployeeWithLeaveFilter,
                                               EmployeeWithOutLeaveFilter)
    list_per_page = 50
    fieldsets = [
        ('Γενικά Στοιχεία', {
            'fields': [
                'transfer_area',
                    'lastname', 'firstname', 'fathername', 'notes',
                    'sex', 'registration_number', 'profession',
                    'profession_description', 'permanent_post',
                    'temporary_position', 'organization_serving',
                    'study_years', 'serving_type', 'date_hired',
                    'order_hired', 'is_permanent',
                    'has_permanent_post', 'rank', 'address', 'identity_number',
                    'inaccessible_school', 'telephone_number1',
                    'telephone_number2', 'email',
                    'birth_date', 'date_created', 'educated']}), #Removed 'hours_current',
        ('Στοιχεία Προϋπηρεσίας', {
                'fields': ['currently_serves',
                           'recognised_experience',
                           'formatted_recognised_experience',
                           'non_educational_experience',
                           'calculable_not_service', 'not_service_existing',
                           'total_service',
                           'payment_start_date_auto',
                           'payment_start_date_manual',
                           'educational_service',
                           'hours',
                           'date_end']}),
            economic_fieldset]
    search_fields = EmployeeAdmin.search_fields + ('registration_number',)
    readonly_fields = EmployeeAdmin.readonly_fields + \
        ['permanent_post', 'temporary_position', 'hours', 'total_service',
         'formatted_recognised_experience', 'payment_start_date_auto',
         'rank', 'profession_description', 'calculable_not_service',
         'date_created', 'educational_service']

    actions = sorted([to_private_teacher, to_administrative,
      CSVReport(add=['permanent_post', 'organization_serving',
                                     'permanent_post_island',
                                     'temporary_position',
                                     'hours',
                                     'profession__description',
                                     'payment_start_date_auto',
                                     'formatted_recognised_experience',
                                     'non_educational_experience',
                                     'educational_service',
                                     'educated',
                                     'rank__value', 'rank__date', 'rank__next_promotion_date'])] + \
    permanent_docx_reports, key=lambda k: k.short_description)


class AdministrativeAdmin(PermanentAdmin):
    inlines = EmployeeAdmin.inlines + [PromotionInline, PlacementInline,
                                       LeaveInline, ResponsibilityInline]
    list_filter = EmployeeAdmin.list_filter + (OrganizationServingFilter,
                                               IslandServingFilter,
                                               PermanentPostFilter,
                                               PermanentPostInIslandFilter,
                                               ServingTypeFilter,
                                               ServesInDideOrgFilter,
                                               CurrentlyServesFilter,
                                               'has_permanent_post',
                                               StudyFilter,
                                               DateHiredFilter,
                                               PaymentStartDateFilter,
                                               NextPromotionInRangeFilter,
                                               EmployeeWithLeaveFilter,
                                               EmployeeWithOutLeaveFilter)
    fieldsets = [
            ('Γενικά Στοιχεία', {
                'fields': [
                        'transfer_area',
                        'lastname', 'firstname', 'fathername', 'notes',
                        'sex', 'registration_number', 'profession',
                        'profession_description', 'permanent_post',
                        'organization_serving',
                        'study_years', 'serving_type', 'date_hired',
                        'order_hired', 'is_permanent',
                        'has_permanent_post', 'rank', 'address', 'identity_number',
                         'telephone_number1',
                        'telephone_number2', 'email',
                        'birth_date', 'hours_current', 'date_created']}),
            ('Στοιχεία Προϋπηρεσίας', {
                    'fields': ['currently_serves',
                               'recognised_experience',
                               'formatted_recognised_experience',
                               'calculable_not_service', 'not_service_existing',
                               'total_service',
                               'payment_start_date_auto',
                               'payment_start_date_manual',
                               'date_end']}),
                economic_fieldset]

    search_fields = EmployeeAdmin.search_fields + ('registration_number',)
    readonly_fields = EmployeeAdmin.readonly_fields + \
            ['permanent_post', 'total_service',
             'formatted_recognised_experience', 'payment_start_date_auto',
             'rank', 'profession_description', 'calculable_not_service',
             'date_created']

    actions = sorted([to_permanent, to_private_teacher,
      CSVReport(add=['permanent_post', 
                                    'organization_serving',
                                    'permanent_post_island',
                                    'profession__description',
                                    'payment_start_date_auto',
                                    'formatted_recognised_experience',
                                    'rank__value', 'rank__date', 'rank__next_promotion_date'])] + \
        permanent_docx_reports, key=lambda k: k.short_description)   


class EmployeeLeaveForm(ModelForm):

    class Meta:
        model = EmployeeLeave

    def __init__(self, *args, **kwargs):
        super(EmployeeLeaveForm, self).__init__(*args, **kwargs)
        self.fields['employee'] = EmployeeChoiceField(label=u'Υπάλληλος')
        self.fields['leave'] = LeaveChoiceField(label=u'Κατηγορία άδειας', for_non_permanents=False)


class EmployeeChoiceField(ModelChoiceField):
    def __init__(self, *args, **kwargs):
        self.choices = Permanent.objects.choices() + Administrative.objects.choices() + NonPermanent.objects.choices()
        return super(EmployeeChoiceField, self).__init__(Employee.objects, *args, **kwargs)
    
class LeaveChoiceField(ModelChoiceField):
    def __init__(self, *args, **kwargs):
        self.choices = Leave.objects.choices(for_non_permanents=kwargs['for_non_permanents'])
        del kwargs['for_non_permanents']
        super(LeaveChoiceField, self).__init__(Leave.objects, *args, **kwargs)    
    

class NonPermanentLeaveForm(ModelForm):
    
    class Meta:
        model = NonPermanentLeave
        
    def __init__(self, *args, **kwargs):
        super(NonPermanentLeaveForm, self).__init__(*args, **kwargs)
        self.fields['leave'] = LeaveChoiceField(label=u'Κατηγορία άδειας', for_non_permanents=True)

class NonPermanentLeaveAdmin(DideAdmin):
    inlines = [LeavePeriodInline]
    search_fields = ('non_permanent__lastname',
                     'non_permanent__vat_number')
    list_display = ('non_permanent', 'leave', 'date_from', 'date_to', 'duration')
    list_filter = (NonPermanentLeaveFilter, 'non_permanent__profession__unified_profession',
                   LeaveDateToFilter, LeaveDateFromFilter)
    actions = [CSVReport(add=['non_permanent__profession__id', 'non_permanent__organization_serving'])]
    form = NonPermanentLeaveForm
    
    def print_leave(self, request, employeeleave_id):
        from django.http import HttpResponse
        from reports.non_permanent_leave import non_permanent_leave_docx_reports
        leave_qs = NonPermanentLeave.objects.filter(pk=employeeleave_id)
        if len(leave_qs) != 1:
            return HttpResponse(u'Η άδεια δεν βρέθηκε')
        leave = leave_qs[0]
        for r in non_permanent_leave_docx_reports:
            if r.short_description == leave.leave.name:
                return r(self, request, leave_qs)
        return HttpResponse(u'Δεν βρέθηκε αναφορά για την άδεια')
    
    def get_urls(self):
        from django.conf.urls import patterns, url      
        return patterns('', url(r'^print/([0-9]+)/$',
                          self.admin_site.admin_view(self.print_leave))) + super(NonPermanentLeaveAdmin, self).get_urls();
            


class EmployeeLeaveAdmin(DideAdmin):

    class Media:
        css = {'all': ('/static/admin/css/widgets.css',)}
        js = ('/static/admin/js/calendar.js',
              '/static/admin/js/admin/DateTimeShortcuts.js', 'js/dide.js')
    form = EmployeeLeaveForm
    search_fields = ('employee__lastname',
                     'employee__permanent__registration_number')
    list_display = ('employee', 'profession', 'category', 'date_from',
                    'date_to', 'duration')
    list_filter = (PermanentLeaveFilter, 'employee__profession__unified_profession',
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
    search_fields = ('lastname', 'identity_number', 'vat_number')
    list_per_page = 50

    fieldsets = [
        ('Στοιχεία μη-μόνιμου', {
            'fields': [
                    'lastname', 'firstname', 'fathername', 'mothername',
                    'sex', 'current_transfer_area',
                    'notes', 'type', 'profession', 'profession_description',
                    'current_placement', 'organization_serving',
                    'study_years',
                    'identity_number', 'telephone_number1',
                    'telephone_number2', 'email', 'birth_date',
                    'date_created', 'pedagogical_sufficiency',
                    'social_security_number']}),
            economic_fieldset]
    readonly_fields = ['type', 'profession_description',
                       'current_placement', 'organization_serving',
                       'date_created',
                       'current_transfer_area']
    inlines = EmployeeAdmin.inlines + [SubstitutePlacementInline,
                                       ServiceInline, LeaveInline,
                                       ResponsibilityInline]
    list_filter = [SubstituteDateRangeFilter, SubstituteAreaFilter,
                   SubstituteOrderFilter, 'profession__unified_profession',
                   NonPermanentOrganizationServingFilter,
                   NonPermanentWithTotalExtraPosition]
    actions = sorted([to_permanent, to_administrative, to_private_teacher,
                    CSVReport(add=['current_placement', 'organization_serving', 'profession__description']),
                  ] + nonpermanent_docx_reports, key=lambda k: k.short_description)


class SchoolTypeAdmin(DideAdmin):
    list_display = ('name', 'shift', 'category', 'rank')


map(lambda t: admin.site.register(*t), (
    (Leave, LeaveAdmin),
    (Permanent, PermanentAdmin),
    (Administrative, AdministrativeAdmin),
    (Profession, ProfessionAdmin),
    (SchoolType, SchoolTypeAdmin),
    (SubstituteMinistryOrder, SubstituteMinistryOrderAdmin),
    (OtherOrganization, OtherOrganizationAdmin),
    (School, SchoolAdmin),
    (NonPermanent, NonPermanentAdmin),
    (PlacementType, PlacementTypeAdmin),
    (EmployeeLeave, EmployeeLeaveAdmin),
    (NonPermanentLeave, NonPermanentLeaveAdmin),
    (MoveInside, MoveInsideAdmin),
    (TemporaryPosition, TemporaryPositionAdmin),
    (TemporaryPositionAllAreas, TemporaryPositionAllAreasAdmin),
    (ApplicationSet, ApplicationSetAdmin),
    (SchoolCommission, SchoolCommissionAdmin),
    (PaymentCategoryTitle, PaymentCategoryTitleAdmin),
    (PaymentReportType, PaymentReportTypeAdmin),
    (PaymentFilePDF, PaymentFilePDFAdmin),
    (PaymentFileName, PaymentFileNameAdmin),
    (RankCode, RankCodeAdmin),
    (PaymentCode, PaymentCodeAdmin)
))


admin.site.register((TransferArea, Island, Responsibility, NonPermanentType,
                     SocialSecurity, LoanCategory, DegreeCategory, Settings,
                     ApplicationType, DegreeOrganization))
admin.site.disable_action('delete_selected')
admin.site.add_action(DeleteAction(ugettext_lazy("Delete selected %(verbose_name_plural)s")))
