# -*- coding: utf-8 -*-
import StringIO as StrIO
from cStringIO import StringIO

from dideman.dide.util.pay_reports import (generate_pdf_structure,
                                           generate_pdf_landscape_structure,
                                           calc_reports, rprts_from_file, 
                                           rprts_from_user)
from dideman import settings

from dideman.dide.util import xml
from dideman.dide.util import pdfreader
from dideman.dide.util import xlsreader

from dideman.dide.util.settings import SETTINGS
from dideman.settings import TEMPLATE_DIRS
from django.contrib import messages
from django.contrib.admin import helpers
from django.contrib.admin.util import get_deleted_objects, model_ngettext
from django.core.exceptions import PermissionDenied
from django.db import router
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import render
from django.template import Context, loader, Template
from django.template.response import TemplateResponse
from django.utils.cache import add_never_cache_headers
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from dideman.lib.date import current_year_date_from, current_year_date_to
from dideman.lib.common import without_accented, parse_deletable_list
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Image, Table
from reportlab.platypus.doctemplate import NextPageTemplate, SimpleDocTemplate
from reportlab.platypus.flowables import PageBreak
from itertools import chain
from collections import defaultdict
from itertools import groupby
from dideman.dide.models import Employee, PaymentCode, PaymentCategoryTitle, Child 
from dideman.lib.common import try_many

from datetime import timedelta
from lxml import etree
import pandas as pd
import operator
import csv
import datetime
import inspect
import os
import zipfile


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

    def get_description(self, model, field):

        def foreign_key_desc():
            index = field.find("__")
            if index > 0:
                first = field[:index]
                rest = field[index + 2:]
                fieldobj = model._meta.get_field_by_name(first)[0]
                return "%s %s" % (self.get_description(model, first),
                                  self.get_description(fieldobj.rel.to, rest))
            else:
                raise Exception("foreign key not found")

        return try_many(lambda : model._meta.get_field_by_name(field)[0].verbose_name,
                        lambda : getattr(model, field).short_description,
                        foreign_key_desc, default=field)

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
        attr = ''
        try:
            if callable(field):
                return field(obj)
            try:
                attr = getattr(obj, field)
                if callable(attr):
                    attr = attr()
            except:
                if '__' in field:
                    t = obj
                    for sf in field.split('__'):
                        t = getattr(t, sf, '')
                        if callable(t):
                            t = t()
                    attr = t
        except:
            pass
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
                           'email': SETTINGS['email_dide'],
                           'fax_number': SETTINGS['fax_number'],
                           'telephone_number': SETTINGS['telephone_number'],
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
        super(CSVReport, self).__init__(short_description, None, 'csv')

    def __call__(self, modeladmin, request, queryset, *args, **kwargs):
        self.response = HttpResponse()
        self.merge_fields(modeladmin, self.add, self.exclude)
        writer = csv.writer(self.response, delimiter=';', quotechar='"',
                            quoting=csv.QUOTE_NONNUMERIC)
        descriptions = [
            self.convert_to_string(
                self.get_description(modeladmin.model, field),
                encode_in_iso=True)
            for field in self.fields]
        writer.writerow(descriptions)
        for obj in queryset:
            row = [self.field_string_value(obj, f, encode_in_iso=True).replace("\n", "").replace(";","")
                   for f in self.fields]
            writer.writerow(row)
        self.add_response_headers()
        self.response.close()
        self.response.flush()
        return self.response


# the following class will be deleted in the near future as is not well written
# and is not working as expected. Needs to be redesigned. 
class CSVEconomicsReport(TemplateAction):
    """
    This class contains the required methods to create a CSV
    KEPYO List. It will be merged with the salary app some time 
    later.
    
    To be deleted.
    """
    def __init__(self, short_description=u'Εξαγωγή λίστας ΚΕΠΥΟ %s' % str(datetime.date.today().year - 1),
                 fields=None, add=None, exclude=None, types=None):
        self.fields = fields
        self.add = add
        self.exclude = exclude
        self.types = types
        super(CSVEconomicsReport, self).__init__(short_description, None, 'csv')

    def __call__(self, modeladmin, request, queryset, *args, **kwargs):
        rpt_types = self.types
        final = defaultdict(list)
        all_types = PaymentCategoryTitle.objects.all()

        emp_dict = {}
        for obj in queryset:
            emp_payments = rprts_from_user(obj.id, datetime.date.today().year - 1, rpt_types)            
            u = set([x['employee_id'] for x in emp_payments])
            dict_emp = {obj.id: [obj.lastname, obj.firstname, obj.vat_number]}
            
            elements = []
            reports = []
            r_list = []
            for empx in u:
                r_list = calc_reports(filter(lambda s: s['employee_id'] == empx, emp_payments))
            hd = []
            ft = []
            if len(r_list) > 0:
                hd = r_list[0]
                ft = [r_list[-2]] + [r_list[-1]]
            dt = r_list
            if len(dt) > 0:
                del dt[0]
                del dt[-2]
                del dt[-1]
            newlist = []
            output = dict()
            for sublist in dt:
                try:
                    output[sublist[0]] = map(operator.add, output[sublist[0]], sublist[1:])
                except KeyError:
                    output[sublist[0]] = sublist[1:]
            for key in output.keys():
                newlist.append([key] + output[key])
            newlist.sort(key=lambda x: x[0], reverse=True)
            r_list = [hd] + newlist + ft
            emp_dict[obj.vat_number] = [hd] + newlist
        
        data = []
        dtFrame = []
        for emp, values in emp_dict.iteritems():
            localhd = values[0]
            r = range(len(localhd))
        
            fin = defaultdict(list)
            for row in values[1:]:
                for i in r:                    
                    fin[localhd[i]].append(unicode(row[i]))
            data.append({emp: fin})

        for data_rows in data:
            for i in data_rows:
                for head_item in data_rows[i]:
                    dtFrame.append([i, head_item, data_rows[i][head_item]])
        dfA = pd.DataFrame(dtFrame)
        dfA.columns = [u'Εργαζόμενος','field','data']
        dfB = dfA.groupby(u'Εργαζόμενος').apply(
            lambda grp: pd.DataFrame(zip(*grp['data']), columns=grp['field']))
        dfB.index = dfB.index.droplevel(-1)
        data = StringIO()
        dfB.to_csv(data, sep=';', encoding='utf-8')
        
        self.response = HttpResponse(data.getvalue(), mimetype='text/csv')
        self.add_response_headers()
        self.response.close()
        self.response.flush()
        return self.response

# the following class will be deleted in the near future as is not well written
# and is not working as expected. Needs to be redesigned. 
class CreatePDF(object):
    """
    This class contains the required methods to create a PDF
    report. It will be merged with the salary app some time 
    later.
    
    To be deleted.
    """

    def __init__(self, short_description):
        self.response = HttpResponse()
        self.short_description = short_description
        self.__name__ = 'generate_mass_pdf'
    def sch (self, c):
        try:
            return c.permanent and c.permanent.organization_serving()
        except:
            return c.organization_serving()
        

    def __call__(self, modeladmin, request, queryset):
        self.response.content = ''
        self.response = HttpResponse(mimetype='application/pdf')
        self.response['Content-Disposition'] = 'attachment; filename=mass_pay_report.pdf'
        registerFont(TTFont('DroidSans', os.path.join(settings.MEDIA_ROOT,
                                                      'DroidSans.ttf')))
        registerFont(TTFont('DroidSans-Bold', os.path.join(settings.MEDIA_ROOT,
                                                           'DroidSans-Bold.ttf')))
        payment_codes = PaymentCode.objects.all()
        category_titles = PaymentCategoryTitle.objects.all()
        all_emp = rprts_from_file(queryset)
        u = set([x['employee_id'] for x in all_emp])
        y = {x['employee_id']: x['year'] for x in all_emp}
        dict_emp = {c.id: [c.lastname,
                           c.firstname,
                           c.vat_number,
                           c.fathername,
                           c.address,
                           c.tax_office,
                           u'%s' % c.profession,
                           u'%s' % c.profession.description,
                           c.telephone_number1,
                           self.sch(c)] for c in Employee.objects.filter(id__in=u)}
            
        elements = []
        reports = []
        for empx in u:
            r_list = calc_reports(filter(lambda s: s['employee_id'] == empx, all_emp))
            report = {}
            report['report_type'] = '1'
            report['type'] = ''
            report['year'] = y[empx]
            report['emp_type'] = 0
            report['vat_number'] = dict_emp[empx][2]
            report['lastname'] = dict_emp[empx][0]
            report['firstname'] = dict_emp[empx][1]
            report['fathername'] = dict_emp[empx][3]
            report['address'] = dict_emp[empx][4]
            report['tax_office'] = dict_emp[empx][5]
            report['profession'] = ' '.join([dict_emp[empx][6], dict_emp[empx][7]])
            report['telephone_number1'] = dict_emp[empx][8]      
            report['rank'] = None
            report['net_amount1'] = ''
            report['net_amount2'] = ''
            report['organization_serving'] = dict_emp[empx][9]
            report['payment_categories'] = r_list
            reports.append(report)
            
        doc = SimpleDocTemplate(self.response, pagesize=A4)
        doc.topMargin = 0.5 * cm
        doc.bottomMargin = 0.5 * cm
        doc.leftMargin = 1.5 * cm
        doc.rightMargin = 1.5 * cm
        doc.pagesize = landscape(A4) 
        elements = generate_pdf_landscape_structure(reports)
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


class ShowOption(object):
    def __init__(self, short_description, field):
        self.short_description = short_description
        self.field = field
        self.__name__ = 'show_option'

    def __call__(self, modeladmin, request, queryset):
        f = modeladmin.model._meta.get_field(self.field)
        for o in queryset:
            setattr(o, self.field, True)
            o.save()

        if len(queryset) == 1:
            msg = u'%s αντικείμενo τροποποιήθηκε.' % str(len(queryset))
        else:
            msg = u'%s αντικείμενα τροποποιήθηκαν.' % str(len(queryset))
        modeladmin.message_user(request, msg)


class HideOption(object):
    def __init__(self, short_description, field):
        self.short_description = short_description
        self.field = field
        self.__name__ = 'hide_option'

    def __call__(self, modeladmin, request, queryset):
        f = modeladmin.model._meta.get_field(self.field)
        for o in queryset:
            setattr(o, self.field, False)
            o.save()

        if len(queryset) == 1:
            msg = u'%s αντικείμενo τροποποιήθηκε.' % str(len(queryset))
        else:
            msg = u'%s αντικείμενα τροποποιήθηκαν.' % str(len(queryset))
        modeladmin.message_user(request, msg)



class EmployeeBecome(object):
    def __init__(self, short_description, to_model):
        self.short_description = short_description
        self.__name__ = 'employee -> ' + to_model._meta.db_table
        self.to_model = to_model

    def __call__(self, modeladmin, request, queryset):
        from warnings import filterwarnings
        import MySQLdb as Database
        filterwarnings('ignore', category=Database.Warning)

        errors = []
        for employee in queryset:
            try:
                employee.become(self.to_model)
            except Exception as e:
                errors.append(unicode(employee))
                continue

        msg = u'%s αντικείμενα τροποποιήθηκαν.' % str(len(queryset) - len(errors))
        if errors:
            msg += u"Λάθη για τους: %s" % ", ".join(errors)
        modeladmin.message_user(request, msg)

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


class PDFReadAction(object):
    def __init__(self, short_description):
        self.short_description = short_description
        self.__name__ = 'read_pdf_file'

    def __call__(self, modeladmin, request, queryset):
        opts = modeladmin.model._meta
        app_label = opts.app_label
        if not modeladmin.has_change_permission(request):
            raise PermissionDenied
        using = router.db_for_write(modeladmin.model)
        changeable_objects, perms_needed, protected = get_deleted_objects(
            queryset, opts, request.user, modeladmin.admin_site, using)
        status = 0
        records = 0
        rows_updated = 0
        for o in queryset:
            if o.status == 0:
                status, records = pdfreader.read(o.pdf_file, o.pdf_file_type, o.id)
                o.extracted_files = records
                o.status = status
                o.save()
                rows_updated += 1

        if rows_updated == 1:
            msg = u'%s αρχείο αναγνώστηκε'
        else:
            msg = u'%s αρχεία αναγνώστηκαν'
        modeladmin.message_user(request, msg % rows_updated)


class XLSReadAction(object):
    def __init__(self, short_description):
        self.short_description = short_description
        self.__name__ = 'read_pdf_file'

    def __call__(self, modeladmin, request, queryset):
        opts = modeladmin.model._meta
        app_label = opts.app_label

        if not modeladmin.has_change_permission(request):
            raise PermissionDenied

        using = router.db_for_write(modeladmin.model)
        changeable_objects, perms_needed, protected = get_deleted_objects(
            queryset, opts, request.user, modeladmin.admin_site, using)

        read_results = []
        rows_updated = 0
        for o in queryset:
            if o.status == 0:
                recs_missed = xlsreader.xlsread(o.id, os.path.join(settings.MEDIA_ROOT,
                                                          str(o.xls_file1).split('/', 1)[0],
                                                          str(o.xls_file1).split('/', 1)[1]))
                for (key), val in recs_missed.items():
                    read_results.append([o.description, key, val])

                recs_missed = xlsreader.xlsread(o.id, os.path.join(settings.MEDIA_ROOT,
                                                          str(o.xls_file2).split('/', 1)[0],
                                                          str(o.xls_file2).split('/', 1)[1]))
                for (key), val in recs_missed.items():
                    read_results.append([o.description, key, val])

                recs_missed = xlsreader.xlsread(o.id, os.path.join(settings.MEDIA_ROOT,
                                                          str(o.xls_file3).split('/', 1)[0],
                                                          str(o.xls_file3).split('/', 1)[1]))
                for (key), val in recs_missed.items():
                    read_results.append([o.description, key, val])
                o.status = 1
                o.save()
                rows_updated += 1
        if rows_updated == 1:
            msg = u'%s αρχείο αναγνώστηκε'
        else:
            msg = u'%s αρχεία αναγνώστηκαν'
        modeladmin.message_user(request, msg % rows_updated)

        if len(queryset) == 1:
            objects_name = force_unicode(opts.verbose_name)
            title = u"Αποτελέσματα ανάγνωσης αρχείου XLS"

        else:
            objects_name = force_unicode(opts.verbose_name_plural)
            title = u"Αποτελέσματα ανάγνωσης αρχείων XLS"

        context = {
            "title": title,
            "objects_name": objects_name,
            "opts": opts,
            "app_label": app_label,
            'action_title': self.short_description,
            'read_results': read_results,
            'read_files': rows_updated,
            
        }

        # Display the results page
        return TemplateResponse(request,
                                'admin/xlsread_selected_result.html',
                                context,
                                current_app=modeladmin.admin_site.name)


def manage_len(f, l):
    sl = len(unicode(f))
    return u"%s%s" % (f, (" " * (l-sl)))


class XMLWriteE3Action(object):
    def __init__(self, short_description):
        self.short_description = short_description
        self.__name__ = 'create_xml_e3_for_erganh'

    def __call__(self, modeladmin, request, queryset):
        opts = modeladmin.model._meta
        app_label = opts.app_label

        using = router.db_for_write(modeladmin.model)
        changeable_objects, perms_needed, protected = get_deleted_objects(
            queryset, opts, request.user, modeladmin.admin_site, using)

        header = ""
        header += "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n"
        header += "<ns1:AnaggeliesE3 xmlns:ns1=\"http://www.yeka.gr/E3\">\n"

        footer = "</ns1:AnaggeliesE3>\n"

        xml_file = StrIO.StringIO()
        xml_file.write(header)

        for o in queryset:
            c = Child.objects.filter(employee=o.parent.id).count()
            xml_file.write(u"\t<AnaggeliaE3>\n")
            xml_file.write(u"\t\t<f_aa_pararthmatos>0</f_aa_pararthmatos>\n")
            xml_file.write(u"\t\t<f_rel_protocol/>\n")
            xml_file.write(u"\t\t<f_rel_date/>\n")
            xml_file.write(u"\t\t<f_ypiresia_sepe>%s</f_ypiresia_sepe>\n" % SETTINGS['ergani_sepe'])
            xml_file.write(u"\t\t<f_ypiresia_oaed>%s</f_ypiresia_oaed>\n" % SETTINGS['ergani_oaed'])
            xml_file.write(u"\t\t<f_ergodotikh_organwsh/>\n")
            xml_file.write(u"\t\t<f_kad_kyria>%s</f_kad_kyria>\n" % SETTINGS['ergani_kad_kyria'])
            xml_file.write(u"\t\t<f_kad_deyt_1/>\n")
            xml_file.write(u"\t\t<f_kad_deyt_2/>\n")
            xml_file.write(u"\t\t<f_kad_deyt_3/>\n")
            xml_file.write(u"\t\t<f_kad_deyt_4/>\n")
            xml_file.write(u"\t\t<f_kad_pararthmatos>%s</f_kad_pararthmatos>\n" % SETTINGS['ergani_kad_parartimatos'])
            xml_file.write(u"\t\t<f_kallikratis_pararthmatos>%s</f_kallikratis_pararthmatos>\n" % SETTINGS['ergani_kallikratis'])
            xml_file.write(u"\t\t<f_eponymo>%s</f_eponymo>\n" % manage_len(o.parent.lastname, 50))
            xml_file.write(u"\t\t<f_onoma>%s</f_onoma>\n" % manage_len(o.parent.firstname, 30))
            
            xml_file.write(u"\t\t<f_eponymo_patros/>\n")
            xml_file.write(u"\t\t<f_onoma_patros>%s</f_onoma_patros>\n" % manage_len(o.parent.fathername, 30))
            xml_file.write(u"\t\t<f_eponymo_mitros/>\n")
            xml_file.write(u"\t\t<f_onoma_mitros>%s</f_onoma_mitros>\n" % manage_len(o.parent.mothername, 30))
            xml_file.write(u"\t\t<f_topos_gennhshs/>\n")
            if o.parent.birth_date:
                xml_file.write(u"\t\t<f_birthdate>%s/%s/%s</f_birthdate>\n" % ('{:02d}'.format(o.parent.birth_date.day), '{:02d}'.format(o.parent.birth_date.month), o.parent.birth_date.year))
            else:
                xml_file.write(u"\t\t<f_birthdate>01/01/1901</f_birthdate>\n")
            if o.parent.sex == u"Άνδρας":
                xml_file.write(u"\t\t<f_sex>0</f_sex>\n")
            else:
                xml_file.write(u"\t\t<f_sex>1</f_sex>\n")
            xml_file.write(u"\t\t<f_yphkoothta>%s</f_yphkoothta>\n" % o.parent.citizenship_code)
            xml_file.write(u"\t\t<f_typos_taytothtas>ΔAT</f_typos_taytothtas>\n")
            xml_file.write(u"\t\t<f_ar_taytothtas>%s</f_ar_taytothtas>\n" % o.parent.identity_number)
            xml_file.write(u"\t\t<f_ekdousa_arxh/>\n")
            xml_file.write(u"\t\t<f_date_ekdosis/>\n")
            xml_file.write(u"\t\t<f_date_ekdosis_lixi/>\n")
            xml_file.write(u"\t\t<f_res_permit_inst/>\n")
            xml_file.write(u"\t\t<f_res_permit_inst_type/>\n")
            xml_file.write(u"\t\t<f_res_permit_inst_ar/>\n")
            xml_file.write(u"\t\t<f_res_permit_inst_lixi/>\n")
            xml_file.write(u"\t\t<f_res_permit_ap/>\n")
            xml_file.write(u"\t\t<f_res_permit_ap_type/>\n")
            xml_file.write(u"\t\t<f_res_permit_ap_ar/>\n")
            xml_file.write(u"\t\t<f_res_permit_ap_lixi/>\n")
            xml_file.write(u"\t\t<f_res_permit_visa/>\n")
            xml_file.write(u"\t\t<f_res_permit_visa_ar/>\n")
            xml_file.write(u"\t\t<f_res_permit_visa_from/>\n")
            xml_file.write(u"\t\t<f_res_permit_visa_to/>\n")
            if o.parent.marital_status:
                xml_file.write(u"\t\t<f_marital_status>%s</f_marital_status>\n" % o.parent.marital_status)
            else:
                xml_file.write(u"\t\t<f_marital_status>0</f_marital_status>\n")

            xml_file.write(u"\t\t<f_arithmos_teknon>%s</f_arithmos_teknon>\n" % str(c))
            xml_file.write(u"\t\t<f_afm>%s</f_afm>\n" % o.parent.vat_number)
            xml_file.write(u"\t\t<f_doy/>\n")
            xml_file.write(u"\t\t<f_amika/>\n")
            xml_file.write(u"\t\t<f_amka>%s</f_amka>\n" % o.parent.social_security_registration_number)
            xml_file.write(u"\t\t<f_code_anergias/>\n")
            xml_file.write(u"\t\t<f_ar_vivliou_anilikou/>\n")
            xml_file.write(u"\t\t<f_dieythinsi/>\n")
            xml_file.write(u"\t\t<f_kallikratis/>\n")
            

            
            xml_file.write(u"\t\t<f_tk/>\n")
            xml_file.write(u"\t\t<f_til/>\n")
            xml_file.write(u"\t\t<f_fax/>\n")
            xml_file.write(u"\t\t<f_email/>\n")
            xml_file.write(u"\t\t<f_epipedo_morfosis>%s</f_epipedo_morfosis>\n" % o.educational_level)
            xml_file.write(u"\t\t<f_professional_education/>\n")
            xml_file.write(u"\t\t<f_expertise_field/>\n")
            xml_file.write(u"\t\t<f_subject_area/>\n")
            xml_file.write(u"\t\t<f_subject_group/>\n")
            xml_file.write(u"\t\t<f_education_agency/>\n")
            xml_file.write(u"\t\t<f_education_date_from/>\n")
            xml_file.write(u"\t\t<f_education_date_to/>\n")
            xml_file.write(u"\t\t<f_duration/>\n")
            xml_file.write(u"\t\t<f_education_year/>\n")
            xml_file.write(u"\t\t<f_fl1/>\n")
            xml_file.write(u"\t\t<f_fl2/>\n")
            xml_file.write(u"\t\t<f_fl3/>\n")
            xml_file.write(u"\t\t<f_fl4/>\n")
            xml_file.write(u"\t\t<f_pc/>\n")
            xml_file.write(u"\t\t<f_pc_other/>\n")

            try:
                f_d = ""
                if o.current_placement().substituteplacement.date_from_show:
                    f_d = o.current_placement().substituteplacement.date_from_show
                else:
                    f_d = o.current_placement().substituteplacement.date_from
                xml_file.write(u"\t\t<f_proslipsidate>%s/%s/%s</f_proslipsidate>\n" % ('{:02d}'.format(f_d.day),
                                                                                       '{:02d}'.format(f_d.month),
                                                                                       f_d.year))
            except:
                xml_file.write(u"\t\t<f_proslipsidate>01/01/2001</f_proslipsidate>\n")
            xml_file.write(u"\t\t<f_proslipsitime>%s</f_proslipsitime>\n" % (datetime.datetime.now() + timedelta(hours=2)).strftime('%H:%m'))
            
            xml_file.write(u"\t\t<f_apoxwrisitime>20:00</f_apoxwrisitime>\n") # added for xsd v4
            xml_file.write(u"\t\t<f_orario>%s</f_orario>\n" % manage_len(' ', 100))
            xml_file.write(u"\t\t<f_wresexternal/>\n")
            try:
                if o.current_placement().substituteplacement.week_hours:
                    xml_file.write(u"\t\t<f_week_hours>%s</f_week_hours>\n" % str('{:3.1f}'.format(float(o.current_placement().substituteplacement.week_hours))).replace('.',','))
                else:
                    xml_file.write(u"\t\t<f_week_hours>23,0</f_week_hours>\n")
            except:
                xml_file.write(u"\t\t<f_week_hours>23,0</f_week_hours>\n")

            xml_file.write(u"\t\t<f_orariodialeima/>\n")
            xml_file.write(u"\t\t<f_eidikothta>%s</f_eidikothta>\n" % o.profession_code_oaed)
            try:
                xml_file.write(u"\t\t<f_proipiresia>%s</f_proipiresia>\n" % o.current_placement().substituteplacement.work_experience_years)
            except:
                xml_file.write(u"\t\t<f_proipiresia></f_proipiresia>\n")
            try:
                if o.current_placement().substituteplacement.last_total_grosspay:
                    fstr = str(o.current_placement().substituteplacement.last_total_grosspay).replace('.',',')
                    if fstr.find(',') != -1:
                        xml_file.write(u"\t\t<f_apodoxes>%s</f_apodoxes>\n" % fstr)
                    else:
                        xml_file.write(u"\t\t<f_apodoxes>%s,00</f_apodoxes>\n" % fstr)
                else:
                    xml_file.write(u"\t\t<f_apodoxes>0,00</f_apodoxes>\n")
            except:
                xml_file.write(u"\t\t<f_apodoxes>0,00</f_apodoxes>\n")

            try:
                if o.current_placement().substituteplacement.last_hourspay:
                    xml_file.write(u"\t\t<f_hour_apodoxes>%s</f_hour_apodoxes>\n" % str(o.current_placement().substituteplacement.last_hourspay).replace('.',','))
                else:
                    xml_file.write(u"\t\t<f_hour_apodoxes>0,00</f_hour_apodoxes>\n")
            except:
                xml_file.write(u"\t\t<f_hour_apodoxes>0,00</f_hour_apodoxes>\n")
            
            if o.ergani_new == True:
                xml_file.write(u"\t\t<f_protiergasia>1</f_protiergasia>\n")
            else:
                xml_file.write(u"\t\t<f_protiergasia>0</f_protiergasia>\n")

            xml_file.write(u"\t\t<f_sxeshapasxolisis>1</f_sxeshapasxolisis>\n")

            try:
                f_d = ""
                if o.current_placement().substituteplacement.date_from_show:
                    f_d = o.current_placement().substituteplacement.date_from_show
                else:
                    f_d = o.current_placement().substituteplacement.date_from
                xml_file.write(u"\t\t<f_orismenou_apo>%s/%s/%s</f_orismenou_apo>\n" % ('{:02d}'.format(f_d.day),
                                                                                       '{:02d}'.format(f_d.month),
                                                                                       f_d.year))
                xml_file.write(u"\t\t<f_orismenou_ews>%s/%s/%s</f_orismenou_ews>\n" % ('{:02d}'.format(o.current_placement().date_to.day),
                                                                                       '{:02d}'.format(o.current_placement().date_to.month), o.current_placement().date_to.year))

            except:
                xml_file.write(u"\t\t<f_orismenou_apo>01/01/2001</f_orismenou_apo>\n")
                xml_file.write(u"\t\t<f_orismenou_ews>01/01/2001</f_orismenou_ews>\n")
            try:
                xml_file.write(u"\t\t<f_kathestosapasxolisis>%s</f_kathestosapasxolisis>\n" % o.type().work_mode)
            except:
                xml_file.write(u"\t\t<f_kathestosapasxolisis></f_kathestosapasxolisis>\n")
            xml_file.write(u"\t\t<f_xaraktirismos>1</f_xaraktirismos>\n")
            xml_file.write(u"\t\t<f_special_case/>\n")
            xml_file.write(u"\t\t<f_apoalliperioxi/>\n")
            xml_file.write(u"\t\t<f_nationalityalli/>\n")
            xml_file.write(u"\t\t<f_kallikratisalli/>\n")

            # added for xsd v4
            xml_file.write(u"\t\t<f_working_time_digital_organization>0</f_working_time_digital_organization>\n")
            xml_file.write(u"\t\t<f_full_employment_hours>030,0</f_full_employment_hours>\n")
            xml_file.write(u"\t\t<f_week_days>5</f_week_days>\n")
            xml_file.write(u"\t\t<f_euelikto_wrario_minutes>0</f_euelikto_wrario_minutes>\n")
            xml_file.write(u"\t\t<f_working_card>0</f_working_card>\n")
            xml_file.write(u"\t\t<f_dialeimma_minutes>0</f_dialeimma_minutes>\n")
            xml_file.write(u"\t\t<f_dialeimma_entos_wrariou>0</f_dialeimma_entos_wrariou>\n")
            # ---

            xml_file.write(u"\t\t<f_topothetisiepistoli>0</f_topothetisiepistoli>\n")
            xml_file.write(u"\t\t<f_topothetisioaed>0</f_topothetisioaed>\n")
            xml_file.write(u"\t\t<f_programaoaed/>\n")
            xml_file.write(u"\t\t<f_replaceprograma/>\n")
            xml_file.write(u"\t\t<f_replaceprograma_afm/>\n")
            xml_file.write(u"\t\t<f_replaceprograma_amka/>\n")
            try:
                if o.current_placement().substituteplacement.oaed_nopay == False:
                    xml_file.write(u"\t\t<f_epidomaoaed>0</f_epidomaoaed>\n")
                    xml_file.write(u"\t\t<f_epidoma_ypiresia_oaed/>\n")            
                else:
                    xml_file.write(u"\t\t<f_epidomaoaed>1</f_epidomaoaed>\n")
                    xml_file.write(u"\t\t<f_epidoma_ypiresia_oaed>%s</f_epidoma_ypiresia_oaed>\n" % o.current_placement().substituteplacement.oaed_nopay_from)
            except:
                xml_file.write(u"\t\t<f_epidomaoaed>0</f_epidomaoaed>\n")
                xml_file.write(u"\t\t<f_epidoma_ypiresia_oaed/>\n")            
            
            xml_file.write(u"\t\t<f_sk_protocol/>\n")
            xml_file.write(u"\t\t<f_sk_date/>\n")
            xml_file.write(u"\t\t<f_comments/>\n")
            xml_file.write(u"\t\t<f_eponymo_idiotitas>%s</f_eponymo_idiotitas>\n" % manage_len(SETTINGS['ergani_lastname_proistamenou'], 100))
            xml_file.write(u"\t\t<f_onoma_idiotitas>%s</f_onoma_idiotitas>\n" % manage_len(SETTINGS['ergani_firstname_proistamenou'], 50))
            xml_file.write(u"\t\t<f_idiotita_idiotitas>%s</f_idiotita_idiotitas>\n" % manage_len(SETTINGS['ergani_idiotita_proistamenou'], 50))
            xml_file.write(u"\t\t<f_dieythinsi_idiotitas>%s</f_dieythinsi_idiotitas>\n" % manage_len(SETTINGS['ergani_address_proistamenou'], 70))
            xml_file.write(u"\t\t<f_afm_idiotitas>%s</f_afm_idiotitas>\n" % SETTINGS['ergani_afm_rep_oaed'])
            xml_file.write(u"\t\t<f_afm_proswpoy>%s</f_afm_proswpoy>\n" % SETTINGS['ergani_afm_rep_oaed'])
            xml_file.write(u"\t\t<f_file/>\n")
            xml_file.write(u"\t\t<f_foreign_file/>\n")
            xml_file.write(u"\t\t<f_young_file/>\n")
            xml_file.write(u"\t</AnaggeliaE3>\n")

        xml_file.write(footer)
        with open(os.path.join(settings.MEDIA_ROOT, 'xsd', 'E3_v6.xsd'), 'r') as f:
            schema_root = etree.XML(f.read())
        res = ''
        schema = etree.XMLSchema(schema_root)
        
        xml = bytes(bytearray(xml_file.getvalue(), encoding='utf-8'))
        exml = etree.XML(xml)
        
        if schema.validate(exml): 
            self.response = HttpResponse(xml_file.getvalue())
            self.response['Content-Type'] = 'text/xml'
            self.response['Content-Disposition'] = 'attachment; ' + \
                'filename=ergani_e3_list_of_%s.xml' % len(queryset)
            add_never_cache_headers(self.response)
            self.response.close()
            self.response.flush()
            return self.response

        else:
            for error in schema.error_log:
                res += u'Γραμμή %s: %s' % (error.line, error.message)
            messages.error(request, u'Σφάλμα έκδοσης XML. Δεν ακολουθεί το πρότυπο. %s' % res)            
            context = {
                "title": 'Σφάλμα εξαγωγής XML',
                #"objects_name": objects_name,
                'queryset': queryset,
                "opts": opts,
                "app_label": app_label,
                'action_title': self.short_description,
                'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
                'changeable_objects': [changeable_objects],
                'action_name': self.__name__,
                'xml_file': xml_file.getvalue().replace('\t','    ').split('\n'),
            }
            # Display the error page
            return TemplateResponse(request,
                                    'admin/ergani_xml_error_results.html',
                                    context,
                                    current_app=modeladmin.admin_site.name)
            
        xml_file.close()


class XMLWriteE7Action(object):
    def __init__(self, short_description):
        self.short_description = short_description
        self.__name__ = 'create_xml_e7_for_erganh'

    def __call__(self, modeladmin, request, queryset):
        opts = modeladmin.model._meta
        app_label = opts.app_label

        using = router.db_for_write(modeladmin.model)
        changeable_objects, perms_needed, protected = get_deleted_objects(
            queryset, opts, request.user, modeladmin.admin_site, using)

        header = ""
        header += "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n"
        header += "<ns1:AnaggeliesE7 xmlns:ns1=\"http://www.yeka.gr/E7\">\n"
        
        footer = "</ns1:AnaggeliesE7>\n"

        xml_file = StrIO.StringIO()
        xml_file.write(header)
        
        for o in queryset:
            c = Child.objects.filter(employee=o.parent.id).count()
            xml_file.write(u"\t<AnaggeliaE7>\n")
            xml_file.write(u"\t\t<f_aa_pararthmatos>0</f_aa_pararthmatos>\n")
            xml_file.write(u"\t\t<f_rel_protocol/>\n")
            xml_file.write(u"\t\t<f_rel_date/>\n")
            xml_file.write(u"\t\t<f_ypiresia_sepe>%s</f_ypiresia_sepe>\n" % SETTINGS['ergani_sepe'])
            xml_file.write(u"\t\t<f_ypiresia_oaed>%s</f_ypiresia_oaed>\n" % SETTINGS['ergani_oaed'])
            xml_file.write(u"\t\t<f_ergodotikh_organwsh/>\n")
            xml_file.write(u"\t\t<f_kad_kyria>%s</f_kad_kyria>\n" % SETTINGS['ergani_kad_kyria'])
            xml_file.write(u"\t\t<f_kad_deyt_1/>\n")
            xml_file.write(u"\t\t<f_kad_deyt_2/>\n")
            xml_file.write(u"\t\t<f_kad_deyt_3/>\n")
            xml_file.write(u"\t\t<f_kad_deyt_4/>\n")
            xml_file.write(u"\t\t<f_kad_pararthmatos>%s</f_kad_pararthmatos>\n" % SETTINGS['ergani_kad_parartimatos'])
            xml_file.write(u"\t\t<f_kallikratis_pararthmatos>%s</f_kallikratis_pararthmatos>\n" % SETTINGS['ergani_kallikratis'])
            xml_file.write(u"\t\t<f_eponymo>%s</f_eponymo>\n" % manage_len(o.parent.lastname, 50))
            xml_file.write(u"\t\t<f_onoma>%s</f_onoma>\n" % manage_len(o.parent.firstname, 30))
            
            xml_file.write(u"\t\t<f_eponymo_patros/>\n")
            xml_file.write(u"\t\t<f_onoma_patros>%s</f_onoma_patros>\n" % manage_len(o.parent.fathername, 30))
            xml_file.write(u"\t\t<f_eponymo_mitros/>\n")
            xml_file.write(u"\t\t<f_onoma_mitros>%s</f_onoma_mitros>\n" % manage_len(o.parent.mothername, 30))
            xml_file.write(u"\t\t<f_topos_gennhshs/>\n")
            if o.parent.birth_date:
                xml_file.write(u"\t\t<f_birthdate>%s/%s/%s</f_birthdate>\n" % ('{:02d}'.format(o.parent.birth_date.day), '{:02d}'.format(o.parent.birth_date.month), o.parent.birth_date.year))
            else:
                xml_file.write(u"\t\t<f_birthdate>01/01/1901</f_birthdate>\n")
            if o.parent.sex == u"Άνδρας":
                xml_file.write(u"\t\t<f_sex>0</f_sex>\n")
            else:
                xml_file.write(u"\t\t<f_sex>1</f_sex>\n")
            xml_file.write(u"\t\t<f_yphkoothta>%s</f_yphkoothta>\n" % o.parent.citizenship_code)

            xml_file.write(u"\t\t<f_typos_taytothtas>ΔAT</f_typos_taytothtas>\n")
            xml_file.write(u"\t\t<f_ar_taytothtas>%s</f_ar_taytothtas>\n" % o.parent.identity_number)
            xml_file.write(u"\t\t<f_ekdousa_arxh/>\n")
            xml_file.write(u"\t\t<f_date_ekdosis/>\n")
            xml_file.write(u"\t\t<f_date_ekdosis_lixi/>\n")
            xml_file.write(u"\t\t<f_res_permit_inst/>\n")
            xml_file.write(u"\t\t<f_res_permit_inst_type/>\n")
            xml_file.write(u"\t\t<f_res_permit_inst_ar/>\n")
            xml_file.write(u"\t\t<f_res_permit_inst_lixi/>\n")
            xml_file.write(u"\t\t<f_res_permit_ap/>\n")
            xml_file.write(u"\t\t<f_res_permit_ap_type/>\n")
            xml_file.write(u"\t\t<f_res_permit_ap_ar/>\n")
            xml_file.write(u"\t\t<f_res_permit_ap_lixi/>\n")
            xml_file.write(u"\t\t<f_res_permit_visa/>\n")
            xml_file.write(u"\t\t<f_res_permit_visa_ar/>\n")
            xml_file.write(u"\t\t<f_res_permit_visa_from/>\n")
            xml_file.write(u"\t\t<f_res_permit_visa_to/>\n")
            if o.parent.marital_status:
                xml_file.write(u"\t\t<f_marital_status>%s</f_marital_status>\n" % o.parent.marital_status)
            else:
                xml_file.write(u"\t\t<f_marital_status>0</f_marital_status>\n")

            xml_file.write(u"\t\t<f_arithmos_teknon>%s</f_arithmos_teknon>\n" % str(c))
            xml_file.write(u"\t\t<f_afm>%s</f_afm>\n" % o.parent.vat_number)
            xml_file.write(u"\t\t<f_doy/>\n")
            xml_file.write(u"\t\t<f_amika/>\n")
            xml_file.write(u"\t\t<f_amka>%s</f_amka>\n" % o.parent.social_security_registration_number)
            xml_file.write(u"\t\t<f_code_anergias/>\n")
            xml_file.write(u"\t\t<f_ar_vivliou_anilikou/>\n")
            xml_file.write(u"\t\t<f_dieythinsi/>\n")
            xml_file.write(u"\t\t<f_kallikratis/>\n")            
            xml_file.write(u"\t\t<f_tk/>\n")
            xml_file.write(u"\t\t<f_til/>\n")
            xml_file.write(u"\t\t<f_fax/>\n")
            xml_file.write(u"\t\t<f_email/>\n")
            xml_file.write(u"\t\t<f_epipedo_morfosis>%s</f_epipedo_morfosis>\n" % o.educational_level)
            xml_file.write(u"\t\t<f_professional_education/>\n")
            xml_file.write(u"\t\t<f_expertise_field/>\n")
            xml_file.write(u"\t\t<f_subject_area/>\n")
            xml_file.write(u"\t\t<f_subject_group/>\n")
            xml_file.write(u"\t\t<f_education_agency/>\n")
            xml_file.write(u"\t\t<f_education_date_from/>\n")
            xml_file.write(u"\t\t<f_education_date_to/>\n")
            xml_file.write(u"\t\t<f_duration/>\n")
            xml_file.write(u"\t\t<f_education_year/>\n")
            xml_file.write(u"\t\t<f_fl1/>\n")
            xml_file.write(u"\t\t<f_fl2/>\n")
            xml_file.write(u"\t\t<f_fl3/>\n")
            xml_file.write(u"\t\t<f_fl4/>\n")
            xml_file.write(u"\t\t<f_pc/>\n")
            xml_file.write(u"\t\t<f_pc_other/>\n")
            xml_file.write(u"\t\t<f_xaraktirismos>1</f_xaraktirismos>\n")
            xml_file.write(u"\t\t<f_sxeshapasxolisis>1</f_sxeshapasxolisis>\n")
            try:
                xml_file.write(u"\t\t<f_kathestosapasxolisis>%s</f_kathestosapasxolisis>\n" % o.type().work_mode)
            except:
                xml_file.write(u"\t\t<f_kathestosapasxolisis>0</f_kathestosapasxolisis>\n")
            xml_file.write(u"\t\t<f_oros>0</f_oros>\n")
            xml_file.write(u"\t\t<f_eidikothta>%s</f_eidikothta>\n" % o.profession_code_oaed)
            try:
                if o.current_placement().substituteplacement.last_total_grosspay:
                    xml_file.write(u"\t\t<f_apodoxes>%s</f_apodoxes>\n" % str(o.current_placement().substituteplacement.last_total_grosspay).replace('.',','))
                else:
                    xml_file.write(u"\t\t<f_apodoxes>0,00</f_apodoxes>\n")
            except:
                xml_file.write(u"\t\t<f_apodoxes>0,00</f_apodoxes>\n")

            try:
                f_d = ""
                if o.current_placement().substituteplacement.date_from_show:
                    f_d = o.current_placement().substituteplacement.date_from_show
                else:
                    f_d = o.current_placement().substituteplacement.date_from
                xml_file.write(u"\t\t<f_proslipsidate>%s/%s/%s</f_proslipsidate>\n" % ('{:02d}'.format(f_d.day),
                                                                                       '{:02d}'.format(f_d.month),
                                                                                       f_d.year))
                xml_file.write(u"\t\t<f_lixisymbashdate>%s/%s/%s</f_lixisymbashdate>\n" % ('{:02d}'.format(o.current_placement().date_to.day),
                                                                                  '{:02d}'.format(o.current_placement().date_to.month),
                                                                                  o.current_placement().date_to.year))
                xml_file.write(u"\t\t<f_apolysisdate>%s/%s/%s</f_apolysisdate>\n" % ('{:02d}'.format(o.current_placement().date_to.day),
                                                                                  '{:02d}'.format(o.current_placement().date_to.month),
                                                                                  o.current_placement().date_to.year))
                #xml_file.write(u"\t\t<f_lastdaydate>%s/%s/%s</f_lastdaydate>\n" % ('{:02d}'.format(o.current_placement().date_to.day),
                #                                                                  '{:02d}'.format(o.current_placement().date_to.month),
                #                                                                  o.current_placement().date_to.year))
                
            except:
                xml_file.write(u"\t\t<f_proslipsidate>01/01/2001</f_proslipsidate>\n")
                xml_file.write(u"\t\t<f_lixisymbashdate>01/01/2001</f_lixisymbashdate>\n")
                xml_file.write(u"\t\t<f_apolysisdate>01/01/2001</f_apolysisdate>")
                
                #xml_file.write(u"\t\t<f_lastdaydate>01/01/2001</f_lastdaydate>\n")

            xml_file.write(u"\t\t<f_comments/>\n")
            xml_file.write(u"\t\t<f_logosperatosis>0</f_logosperatosis>\n")
            xml_file.write(u"\t\t<f_logosperatosiscomments/>\n")
            xml_file.write(u"\t\t<f_afm_proswpoy>%s</f_afm_proswpoy>\n" % SETTINGS['ergani_afm_rep_oaed'])
            xml_file.write(u"\t\t<f_file/>\n")
            xml_file.write(u"\t\t<f_foreign_file/>\n")
            xml_file.write(u"\t\t<f_young_file/>\n")
            xml_file.write(u"\t</AnaggeliaE7>\n")

        xml_file.write(footer)
        with open(os.path.join(settings.MEDIA_ROOT, 'xsd', 'E7_v2.xsd'), 'r') as f:
            schema_root = etree.XML(f.read())
        res = ''
        schema = etree.XMLSchema(schema_root)

        xml = bytes(bytearray(xml_file.getvalue(), encoding='utf-8'))
        exml = etree.XML(xml)

        if schema.validate(exml):
            self.response = HttpResponse(xml_file.getvalue())
            self.response['Content-Type'] = 'text/xml'
            self.response['Content-Disposition'] = 'attachment; ' + \
                'filename=ergani_e7_list_of_%s.xml' % len(queryset)
            add_never_cache_headers(self.response)
            self.response.close()
            self.response.flush()
            return self.response

        else:
            for error in schema.error_log:
                res += u'Γραμμή %s: %s' % (error.line, error.message)
            messages.error(request, u'Σφάλμα έκδοσης XML. Δεν ακολουθεί το πρότυπο. %s' % res)            
            context = {
                "title": 'Σφάλμα εξαγωγής XML',
                #"objects_name": objects_name,
                'queryset': queryset,
                "opts": opts,
                "app_label": app_label,
                'action_title': self.short_description,
                'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
                'changeable_objects': [changeable_objects],
                'action_name': self.__name__,
                'xml_file': xml_file.getvalue().replace('\t','    ').split('\n'),
            }
            # Display the error page
            return TemplateResponse(request,
                                    'admin/ergani_xml_error_results.html',
                                    context,
                                    current_app=modeladmin.admin_site.name)            
        xml_file.close()


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
        elapsed = 0
        rows_updated = 0
        read_results = []
        for o in queryset:
            if o.status == 0:
                success, recs_affected, elapsed, recs_missed = xml.read(os.path.join(settings.MEDIA_ROOT,
                                                str(o.xml_file).split('/', 1)[0],
                                                str(o.xml_file).split('/', 1)[1]),
                                                                        o.id, o.taxed)
                o.status = success
                o.imported_records = recs_affected
                o.save()

                total_elapsed += elapsed
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
            'action_time_elapsed': round(total_elapsed, 1),
            'read_files': rows_updated,
        }

        # Display the results page
        return TemplateResponse(request,
                                'admin/xmlread_selected_result.html',
                                context,
                                current_app=modeladmin.admin_site.name)
