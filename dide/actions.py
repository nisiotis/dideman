# -*- coding: utf-8 -*-
from cStringIO import StringIO
from dideman.dide.util.pay_reports import (generate_pdf_structure, 
                                           reports_calc_amount, rprts_from_file)
from dideman import settings
from dideman.dide.util import xml
from dideman.dide.util.common import without_accented, current_year_date_from, \
    current_year_date_to, parse_deletable_list
from dideman.dide.util.settings import SETTINGS
from dideman.settings import TEMPLATE_DIRS
from django.contrib.admin import helpers
from django.contrib.admin.util import get_deleted_objects, model_ngettext
from django.core.exceptions import PermissionDenied
from django.db import router
from django.http import HttpResponse
from django.shortcuts import render
from django.template import Context, loader, Template
from django.template.response import TemplateResponse
from django.utils.cache import add_never_cache_headers
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext as _
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Image, Table
from reportlab.platypus.doctemplate import NextPageTemplate, SimpleDocTemplate
from reportlab.platypus.flowables import PageBreak
from itertools import chain

import csv
import datetime
import inspect
import os
import zipfile
from dideman.dide.models import Employee, PaymentCode


def timestamp():
    return filter(lambda x: x >= '0' and x <= '9',
                  str(datetime.datetime.now()))


class TemplateAction(object):
    template_base_path = 'reports'

    def __init__(self, short_description, template_path, file_type):
        self.short_description = short_description
        self.file_type = file_type
        self.template_path = template_path
        self.__name__ = short_description

    def add_response_headers(self):
        self.response['Content-Type'] = 'text/%s' % self.file_type
        self.response['Content-Disposition'] = 'attachment; ' + \
            'filename=report%s.%s' % (timestamp(), self.file_type)
        add_never_cache_headers(self.response)

    def __call__(self, modeladmin, request, data={}, *args, **kwargs):
        self.response = render(request, os.path.join(self.template_base_path,
                                                     self.template_path), data)
        self.add_response_headers()
        return self.response

    def merge_fields(self, modeladmin, add, remove):
        if not self.fields:
            self.fields = [field.name
                           for field in modeladmin.model._meta.fields]
            if self.add:
                self.fields += self.add
            if self.exclude:
                self.fields = [field for field in self.fields
                               if field not in self.exclude]

    def field_string_value(self, obj, field,
                           encode_in_iso=False):
        return self.convert_to_string(self.field_value(obj, field),
                                      encode_in_iso)

    def field_value(self, obj, field):
        if callable(field):
            return field(obj)
        if hasattr(obj, field):
            attr = getattr(obj, field)
            if callable(attr):
                attr = attr()
        else:
            if '__' in field:
                t = obj
                for sf in field.split('__'):
                    t = getattr(t, sf)
                    if callable(t):
                        t = t()
                attr = t
            else:
                attr = ''
        return attr

    def convert_to_string(self, value, encode_in_iso=False):
        if isinstance(value, bool):
            return str(int(value))
        elif not value:
            return ''
        elif encode_in_iso:
            if isinstance(value, unicode):
                return value.encode('iso8859-7', 'ignore')
            elif hasattr(value, '__unicode__'):
                return unicode(value).encode('iso8859-7', 'ignore')
            else:
                return str(value)
        elif isinstance(value, unicode):
            return value
        else:
            return "%s" % str(value)


class DocxReport(TemplateAction):
    template_base_path = os.path.join(TemplateAction.template_base_path,
                                      'docx')

    def __init__(self, short_description, body_template_path, fields,
                 custom_context=None, model_fields=None, include_header=True,
                 include_footer=True):
        model_fields = model_fields or {}
        custom_context = custom_context or {}
        self.short_description = short_description
        self.body_template_path = body_template_path
        self.file_type = 'docx'
        self.__name__ = short_description
        self.fields = fields
        self.model_fields = model_fields
        self.dictionary = {'data': [], 
                           'settings': SETTINGS,
                           'dide_place':
                               without_accented(SETTINGS['dide_place']
                                                .upper()),
                           'date': datetime.date.today,
                           'current_year_date_from': current_year_date_from(),
                           'current_year_date_to': current_year_date_to(),
                           'body_template_path':
                               os.path.join(self.template_base_path,
                                            self.body_template_path),
                           'subject': 'Default Docx Subject',
                           'include_header': include_header,
                           'include_footer': include_footer}
        self.dictionary.update(custom_context)

    def __call__(self, modeladmin, request, queryset, *args, **kwargs):
        self.response = HttpResponse()
        self.response.content = ''
        # does not get cleared on each request bug??
        self.dictionary['data'] = []
        for obj in queryset:
            d1 = dict(zip(self.fields, [self.field_value(obj, field)
                                        for field in self.fields]))
            d2 = dict(zip([f for f in self.model_fields],
                          [self.map_field_or_list(self.model_fields[f], d1)
                           for f in self.model_fields]))
            d1.update(d2)
            self.dictionary['data'].append(d1)

        t = loader.get_template(os.path.join(self.template_base_path,
                                             'basic', 'document.xml'))

        document = t.render(Context(self.dictionary))
        self.add_response_headers()
        self.response.write(self.add_to_docx(document))
        self.response.close()
        self.response.flush()
        return self.response

    def map_field(self, field, dictionary):
        if callable(field):
            field = field(dictionary)
        if '{{' in field:
            return Template(field).render(Context(dictionary))
        else:
            return field

    def map_field_or_list(self, field, dictionary):
        if isinstance(field, list):
            return [self.map_field(f, dictionary) for f in field]
        else:
            return self.map_field(field, dictionary)

    def add_response_headers(self):
        self.response['Content-Type'] = 'application/' + \
            'vnd.openxmlformats-officedocument.wordprocessingml.document'
        self.response['Content-Disposition'] = 'attachment; ' + \
            'filename=report%s.%s' % (timestamp(), self.file_type)
        add_never_cache_headers(self.response)

    def add_to_docx(self, document):
        buffer = StringIO()
        template_dir = os.path.join(TEMPLATE_DIRS[0], self.template_base_path,
                                    'basic', 'docx-contents')
        docx = zipfile.ZipFile(buffer,
                               mode='w', compression=zipfile.ZIP_DEFLATED)
        os.chdir(template_dir)
        docx.writestr('word/document.xml', document.encode('utf-8'))
        for dirpath, dirnames, filenames in os.walk('.'):
            for filename in filenames:
                template_file = os.path.join(dirpath, filename)
                docx.write(template_file, template_file[2:])
        docx.close()
        buffer.flush()
        ret_zip = buffer.getvalue()
        buffer.close()
        return ret_zip


class CSVReport(TemplateAction):

    def __init__(self, short_description=u'Εξαγωγή σε csv',
                 fields=None, add=None, exclude=None):
        self.fields = fields
        self.add = add
        self.exclude = exclude
        self.response = HttpResponse()
        super(CSVReport, self).__init__(short_description, None, 'csv')

    def __call__(self, modeladmin, request, queryset, *args, **kwargs):
        self.merge_fields(modeladmin, self.add, self.exclude)
        self.response.content = ''
        writer = csv.writer(self.response, delimiter=';', quotechar='"',
                            quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(self.fields)
        for obj in queryset:
            writer.writerow([self.field_string_value(obj, f,
                                                     encode_in_iso=True)
                             for f in self.fields])
        self.add_response_headers()
        self.response.close()
        self.response.flush()
        return self.response


class CreatePDF(object):

    def __init__(self, short_description):
        self.response = HttpResponse()
        self.short_description = short_description
        self.__name__ = 'generate_mass_pdf'

    def __call__(self, modeladmin, request, queryset):

        self.response.content = ''

        self.response = HttpResponse(mimetype='application/pdf')
        self.response['Content-Disposition'] = 'attachment; filename=mass_pay_report.pdf'
        registerFont(TTFont('DroidSans', os.path.join(settings.MEDIA_ROOT,
                                                      'DroidSans.ttf')))
        registerFont(TTFont('DroidSans-Bold', os.path.join(settings.MEDIA_ROOT,
                                                           'DroidSans-Bold.ttf')))
    
        obj = PaymentCode.objects.all()
        dict_codes = {c.id: c.description for c in obj}
        dict_tax_codes = {c.id: c.is_tax for c in obj}
        tax_codes = [c for c in dict_codes.keys()]
        all_emp = rprts_from_file(queryset)    
        u = set([x['employee_id'] for x in all_emp])
         
        dict_emp = {c.id: [c.lastname, c.firstname, c.vat_number] for c in Employee.objects.filter(id__in=u)}
        
        elements = []
        reports = []
        for empx in u:
            
            gr, de, et = reports_calc_amount(filter(lambda s: s['employee_id'] == empx, all_emp), tax_codes)
            grd = [{'type':'gr','code_id':x[0],'amount':x[1]} for x in gr]
            ded = [{'type':'de','code_id':x[0],'amount':x[1]} for x in de]
            etd = [{'type':'et','code_id':x[0],'amount':x[1]} for x in et]
            calctd_payments_list = [x for x in chain(grd,ded)]
            report = {}
        
            report['report_type'] = '1'
            report['type'] = ''
            report['year'] = ''
            report['emp_type'] = 0
            #if emptype == 1:
            #    report['registration_number'] = emp.registration_number
            report['vat_number'] = dict_emp[empx][2]
            report['lastname'] = dict_emp[empx][0]
            report['firstname'] = dict_emp[empx][1]
            report['rank'] = None
            report['net_amount1'] = ''
            report['net_amount2'] = ''
    
            pay_cat_list = []
            pay_cat_dict = {}
            pay_cat_dict['title'] = u'Επιμέρους Σύνολα'
            pay_cat_dict['month'] = ''
            pay_cat_dict['year'] = ''
            pay_cat_dict['start_date'] = ''
            pay_cat_dict['end_date'] = ''
            pay_cat_dict['payments'] = []
            for o in calctd_payments_list:
                p = {}
                p['type'] = o['type']
                p['code'] = dict_codes[o['code_id']]
                p['amount'] = o['amount']
                p['info'] = None
                p['code_tax'] = dict_tax_codes[o['code_id']]
                pay_cat_dict['payments'].append(p)
            pay_cat_list.append(pay_cat_dict)
            report['payment_categories'] = pay_cat_list
            reports.append(report)
        
        elements = generate_pdf_structure(reports)
        
            
        doc = SimpleDocTemplate(self.response, pagesize=A4)
        doc.topMargin = 1.0 * cm
        doc.build(elements)
        return self.response


class FieldAction(object):

    def __init__(self, short_description, field_name, changer):
        self.short_description = short_description
        self.__name__ = 'change_selected_' + field_name
        self.changer = changer
        self.field_name = field_name

    def __call__(self, modeladmin, request, queryset):
        opts = modeladmin.model._meta
        app_label = opts.app_label

        if not modeladmin.has_change_permission(request):
            raise PermissionDenied

        using = router.db_for_write(modeladmin.model)
        changeable_objects, perms_needed, protected = get_deleted_objects(
            queryset, opts, request.user, modeladmin.admin_site, using)

        if request.POST.get('post'):
            rows_updated = 0
            if len(inspect.getargspec(self.changer)[0]) == 0:
                rows_updated = queryset.update(**{self.field_name:
                                                  self.changer()})
            else:
                for o in queryset:
                    old = getattr(o, self.field_name)
                    setattr(o, self.field_name, self.changer(o))
                    o.save()
                    if old != getattr(o, self.field_name):
                        rows_updated += 1
            if rows_updated == 1:
                msg = u'%s αντικείμενο τροποποιήθηκε'
            else:
                msg = u'%s αντικείμενα τροποποιήθηκαν'
            modeladmin.message_user(request, msg % rows_updated)
            return None

        if len(queryset) == 1:
            objects_name = force_unicode(opts.verbose_name)
        else:
            objects_name = force_unicode(opts.verbose_name_plural)

        title = _("Are you sure?")

        context = {
            "title": title,
            "objects_name": objects_name,
            'queryset': queryset,
            "opts": opts,
            "app_label": app_label,
            'action_title': self.short_description,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
            'changeable_objects': [changeable_objects],
            'action_name': self.__name__,
            }
        new_changeable_objects = parse_deletable_list(changeable_objects)
        extra_context = {'changeable_objects': [new_changeable_objects]}
        context.update(extra_context or {})

        # Display the confirmation page
        return TemplateResponse(request,
                                'admin/change_selected_confirmation.html',
                                context,
                                current_app=modeladmin.admin_site.name)


class DeleteAction(object):

    def __init__(self, short_description):
        self.short_description = short_description
        self.__name__ = 'delete_selected'

    def __call__(self, modeladmin, request, queryset):
        """
        Our action which deletes the selected objects.

        This action first displays a confirmation page whichs shows all the
        deleteable objects without the payment ones, or,
        if the user has no permission one of the related
        childs (foreignkeys), a "permission denied" message.

        Next, it deletes all selected objects and redirects back
        to the change list.
        """

        opts = modeladmin.model._meta
        app_label = opts.app_label

        # Check that the user has delete permission for the actual model
        if not modeladmin.has_delete_permission(request):
            raise PermissionDenied

        using = router.db_for_write(modeladmin.model)

        # Populate deletable_objects, a data structure of all related objects that
        # will also be deleted.
        deletable_objects, perms_needed, protected = get_deleted_objects(
            queryset, opts, request.user, modeladmin.admin_site, using)

        # The user has already confirmed the deletion.
        # Do the deletion and return a None to display the change list view again.
        if request.POST.get('post'):
            if perms_needed:
                raise PermissionDenied
            n = queryset.count()
            if n:
                for obj in queryset:
                    obj_display = force_unicode(obj)
                    modeladmin.log_deletion(request, obj, obj_display)
                queryset.delete()
                modeladmin.message_user(request, _("Successfully deleted %(count)d %(items)s.") % {
                    "count": n, "items": model_ngettext(modeladmin.opts, n)
                })
            # Return None to display the change list page again.
            return None

        if len(queryset) == 1:
            objects_name = force_unicode(opts.verbose_name)
        else:
            objects_name = force_unicode(opts.verbose_name_plural)

        if perms_needed or protected:
            title = _("Cannot delete %(name)s") % {"name": objects_name}
        else:
            title = _("Are you sure?")

        context = {
            "title": title,
            "objects_name": objects_name,
            "deletable_objects": [deletable_objects],
            'queryset': queryset,
            "perms_lacking": perms_needed,
            "protected": protected,
            "opts": opts,
            "app_label": app_label,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        }
        new_deletable_objects = parse_deletable_list(deletable_objects)
        extra_context = {'deletable_objects': [new_deletable_objects]}
        context.update(extra_context or {})

        # Display the confirmation page
        return TemplateResponse(request, modeladmin.delete_selected_confirmation_template or [
            "admin/%s/%s/delete_selected_confirmation.html" % (app_label, opts.object_name.lower()),
            "admin/%s/delete_selected_confirmation.html" % app_label,
            "admin/delete_selected_confirmation.html"
        ], context, current_app=modeladmin.admin_site.name)
    

class XMLReadAction(object):

    def __init__(self, short_description):
        self.short_description = short_description
        self.__name__ = 'read_xml_file'

    def __call__(self, modeladmin, request, queryset):
        opts = modeladmin.model._meta
        app_label = opts.app_label

        if not modeladmin.has_change_permission(request):
            raise PermissionDenied

        using = router.db_for_write(modeladmin.model)
        changeable_objects, perms_needed, protected = get_deleted_objects(
            queryset, opts, request.user, modeladmin.admin_site, using)

        total_elapsed = 0
        rows_updated = 0
        read_results = []
        for o in queryset:
            if o.status == 0:
                success, recs_affected, elapsed, recs_missed = xml.read(os.path.join(settings.MEDIA_ROOT,
                                                str(o.xml_file).split('/', 1)[0],
                                                str(o.xml_file).split('/', 1)[1]),
                                                o.id)
                o.status = success
                o.imported_records = recs_affected
                o.save()
                
                total_elapsed = total_elapsed + elapsed
                rows_updated += 1
                for (key), val in recs_missed.items():
                    read_results.append([o.description, key, val])
        if rows_updated == 1:
            msg = u'%s αρχείο αναγνώστηκε'
        else:
            msg = u'%s αρχεία αναγνώστηκαν'
        modeladmin.message_user(request, msg % rows_updated)
        if len(queryset) == 1:
            objects_name = force_unicode(opts.verbose_name)
            title = u"Αποτελέσματα ανάγνωσης αρχείου XML"

        else:
            objects_name = force_unicode(opts.verbose_name_plural)
            title = u"Αποτελέσματα ανάγνωσης αρχείων XML"

        context = {
            "title": title,
            "objects_name": objects_name,
            "opts": opts,
            "app_label": app_label,
            'action_title': self.short_description,
            'read_results': read_results,
            'action_time_elapsed': total_elapsed,
            'read_files': rows_updated,
        }

        # Display the results page
        return TemplateResponse(request,
                                'admin/xmlread_selected_result.html',
                                context,
                                current_app=modeladmin.admin_site.name)
