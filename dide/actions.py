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


def xml_escape(value):
    if value is None:
        return u''
    return unicode(value).replace(u'&', u'&amp;') \
                         .replace(u'<', u'&lt;') \
                         .replace(u'>', u'&gt;')


def try_value(fn, default=u''):
    """Evaluate fn(), falling back to default on any error or None."""
    try:
        v = fn()
    except Exception:
        return default
    return default if v is None else v


def format_ergani_date(d, default=u'01/01/2001'):
    if not d:
        return default
    return u'%02d/%02d/%s' % (d.day, d.month, d.year)


def parse_amount(value):
    """Read a money value that may be stored in either notation.

    The pay fields are free-text CharFields, so the same column holds
    '1688', '1688.00', '1688,00' and '1.688,00' depending on who typed
    it. Returns a float, or None when nothing numeric can be read.
    """
    s = unicode(value if value is not None else u'').strip()
    if not s:
        return None
    if u',' in s and u'.' in s:
        # 1.688,00 -- dot groups thousands, comma is the decimal mark
        s = s.replace(u'.', u'').replace(u',', u'.')
    elif u',' in s:
        s = s.replace(u',', u'.')
    try:
        return float(s)
    except ValueError:
        return None


def format_ergani_amount(value):
    """Greek money format with thousands separator: 1688 -> u'1.688,00'.

    Mirrors format_apodoxes() from the E7N converter script.
    """
    f = parse_amount(value)
    if f is None:
        return u'0,00'
    s = u'{:,.2f}'.format(f)
    return s.replace(u',', u'X').replace(u'.', u',').replace(u'X', u'.')


def format_legacy_amount(value):
    """Greek money format without thousands separator: 1688 -> u'1688,00'.

    The E3N converter passes f_apodoxes / f_hour_apodoxes straight through
    from the old file, so E3N keeps the plain formatting rather than the
    grouped one E7N applies.
    """
    f = parse_amount(value)
    if f is None:
        return u'0,00'
    return u'{:.2f}'.format(f).replace(u'.', u',')


def write_ergani_fields(out, fields, indent):
    """Serialize an ordered list of (tag, value) pairs.

    A value that is itself a list/tuple of pairs is written as a nested
    element, which is how E3N carries EpikourikiSelections.
    """
    for tag, value in fields:
        if isinstance(value, (list, tuple)):
            out.write(u'%s<%s>\n' % (indent, tag))
            write_ergani_fields(out, value, indent + u'\t')
            out.write(u'%s</%s>\n' % (indent, tag))
        else:
            text = xml_escape(value)
            if text == u'':
                out.write(u'%s<%s/>\n' % (indent, tag))
            else:
                out.write(u'%s<%s>%s</%s>\n' % (indent, tag, text, tag))


def render_ergani_document(root_tag, record_tag, namespace, records,
                           schema_location=None):
    """Build a complete Ε.Ρ.Γ.Α.Ν.Η. document.

    The announcement elements carry xmlns="" so that, as in the converter
    scripts, only the root sits in the E3N/E7N namespace and every field
    below it is in no namespace at all.
    """
    out = StrIO.StringIO()
    out.write(u'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
    root_attrs = u'xmlns="%s" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' % namespace
    if schema_location:
        root_attrs += u' xsi:schemaLocation="%s %s"' % (namespace, schema_location)
    out.write(u'<%s %s>\n' % (root_tag, root_attrs))
    for fields in records:
        out.write(u'\t<%s xmlns="">\n' % record_tag)
        write_ergani_fields(out, fields, u'\t\t')
        out.write(u'\t</%s>\n' % record_tag)
    out.write(u'</%s>\n' % root_tag)
    return out


# Πεδία που πρόσθεσε το E3N και δεν προκύπτουν από την βάση.
# Ακολουθεί τις τιμές του convertE3.py.
E3N_DEFAULTS = [
    ('f_trial_period', u'0'),
    ('f_trial_date_to', u''),
    ('f_basics_acceptance', u'1'),  # με αποδοχή όρων από myergani
    ('f_file', u''),
    ('f_file_symbash', u''),
    ('f_comments', u''),
    ('f_foreign_file', u''),
    ('f_young_file', u''),
    ('f_xronos_katavolis_apodoxon', u'καθε 10 επομενου μήνα '),
    ('f_ipoxreotiki_katartisi', u'0'),
    ('f_efarmoste_sillogiki_simbasi', u'0'),
    ('f_efarmoste_sillogiki_simbasi_comments', u''),
    ('f_kyria_asfalisi', u'001'),
    # Το EpikourikiSelections παρεμβάλλεται εδώ, αμέσως μετά το
    # f_kyria_asfalisi, όπως το παράγει ο convertE3.py.
    ('EpikourikiSelections',
     [('EpikourikiSelectionsE3N', [('f_kod_epikourikis', u'001')])]),
    ('f_prosthetes_asfalistikes', u''),
    ('f_mh_provlepsimo_programma', u'0'),
    ('f_paraggelia_hmeres_hours', u''),
    ('f_paraggelia_min_notification', u''),
    ('f_paraggelia_notes', u''),
    ('f_topos_ergasias', u'0'),
    ('f_topos_ergasias_comment', u''),
]


class ErganiXMLAction(object):
    """Common plumbing for the E3N / E7N announcement exports.

    Subclasses provide the document identity and build the field list for
    one employee; everything else -- serialization, schema validation and
    the download / error response -- is shared.
    """

    root_tag = None
    record_tag = None
    namespace = None
    schema_file = None
    file_prefix = None

    def __init__(self, short_description):
        self.short_description = short_description

    def record_fields(self, o):
        raise NotImplementedError

    def validate(self, request, xml_value):
        """Validate against the XSD when it is available.

        Returns (ok, errors). The E3N/E7N schemas are distributed
        separately, so when the file is absent the document is still
        produced and the operator is told it went out unvalidated rather
        than being blocked.
        """
        schema_path = os.path.join(settings.MEDIA_ROOT, 'xsd', self.schema_file)
        if not os.path.exists(schema_path):
            messages.warning(
                request,
                u'Το αρχείο δεν ελέγχθηκε: λείπει το σχήμα %s από τον φάκελο xsd.'
                % self.schema_file)
            return True, ''
        with open(schema_path, 'r') as f:
            schema = etree.XMLSchema(etree.XML(f.read()))
        exml = etree.XML(bytes(bytearray(xml_value, encoding='utf-8')))
        if schema.validate(exml):
            return True, ''
        return False, u''.join([u'Γραμμή %s: %s' % (e.line, e.message)
                                for e in schema.error_log])

    def __call__(self, modeladmin, request, queryset):
        opts = modeladmin.model._meta
        app_label = opts.app_label

        using = router.db_for_write(modeladmin.model)
        changeable_objects, perms_needed, protected = get_deleted_objects(
            queryset, opts, request.user, modeladmin.admin_site, using)

        xml_file = render_ergani_document(
            self.root_tag, self.record_tag, self.namespace,
            [self.record_fields(o) for o in queryset],
            schema_location=self.schema_file)
        xml_value = xml_file.getvalue()

        ok, res = self.validate(request, xml_value)
        if ok:
            self.response = HttpResponse(xml_value)
            self.response['Content-Type'] = 'text/xml'
            self.response['Content-Disposition'] = 'attachment; ' + \
                'filename=%s_list_of_%s.xml' % (self.file_prefix, len(queryset))
            add_never_cache_headers(self.response)
            self.response.close()
            self.response.flush()
            return self.response

        messages.error(request,
                       u'Σφάλμα έκδοσης XML. Δεν ακολουθεί το πρότυπο. %s' % res)
        context = {
            "title": 'Σφάλμα εξαγωγής XML',
            'queryset': queryset,
            "opts": opts,
            "app_label": app_label,
            'action_title': self.short_description,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
            'changeable_objects': [changeable_objects],
            'action_name': self.__name__,
            'xml_file': xml_value.replace('\t', '    ').split('\n'),
        }
        return TemplateResponse(request,
                                'admin/ergani_xml_error_results.html',
                                context,
                                current_app=modeladmin.admin_site.name)

    def identity_fields(self, o):
        """The person block shared by E3N and E7N, in schema order."""
        children = Child.objects.filter(employee=o.parent.id).count()
        return [
            ('f_aa_pararthmatos', u'0'),
            ('f_rel_protocol', u''),
            ('f_rel_date', u''),
            ('f_ypiresia_sepe', SETTINGS['ergani_sepe']),
            ('f_ypiresia_oaed', SETTINGS['ergani_oaed']),
            ('f_kad_pararthmatos', SETTINGS['ergani_kad_parartimatos']),
            ('f_kallikratis_pararthmatos', SETTINGS['ergani_kallikratis']),
            ('f_eponymo', manage_len(o.parent.lastname or u'', 50)),
            ('f_onoma', manage_len(o.parent.firstname or u'', 30)),
            ('f_onoma_patros', manage_len(o.parent.fathername or u'', 30)),
            ('f_onoma_mitros', manage_len(o.parent.mothername or u'', 30)),
            ('f_birthdate', format_ergani_date(o.parent.birth_date, u'01/01/1901')),
            ('f_sex', u'0' if o.parent.sex == u'Άνδρας' else u'1'),
            ('f_yphkoothta', o.parent.citizenship_code or u''),
            ('f_typos_taytothtas', u'ΔAT'),
            ('f_ar_taytothtas', o.parent.identity_number or u''),
            ('f_ekdousa_arxh', u''),
            ('f_date_ekdosis', u''),
            ('f_date_ekdosis_lixi', u''),
            ('f_res_permit_inst', u''),
            ('f_res_permit_inst_type', u''),
            ('f_res_permit_inst_ar', u''),
            ('f_res_permit_inst_lixi', u''),
            ('f_res_permit_ap', u''),
            ('f_res_permit_ap_type', u''),
            ('f_res_permit_ap_ar', u''),
            ('f_res_permit_ap_lixi', u''),
            ('f_res_permit_visa', u''),
            ('f_res_permit_visa_ar', u''),
            ('f_res_permit_visa_from', u''),
            ('f_res_permit_visa_to', u''),
            ('f_marital_status', o.parent.marital_status or u'0'),
            ('f_arithmos_teknon', children),
            ('f_afm', o.parent.vat_number or u''),
            ('f_doy', u''),
            ('f_amika', u''),
            ('f_amka', o.parent.social_security_registration_number or u''),
            ('f_code_anergias', u''),
            ('f_ar_vivliou_anilikou', u''),
            ('f_epipedo_morfosis', o.educational_level),
        ]


class XMLWriteE3Action(ErganiXMLAction):
    """Αναγγελία πρόσληψης Ε3 (πρότυπο E3N)."""

    root_tag = 'AnaggeliesE3N'
    record_tag = 'AnaggeliaE3N'
    namespace = 'http://www.yeka.gr/E3N'
    schema_file = 'E3N_v1.xsd'
    file_prefix = 'ergani_e3n'

    def __init__(self, short_description):
        super(XMLWriteE3Action, self).__init__(short_description)
        self.__name__ = 'create_xml_e3_for_erganh'

    def record_fields(self, o):
        placement = try_value(lambda: o.current_placement(), None)
        sub = try_value(lambda: placement.substituteplacement, None)
        start = try_value(lambda: sub.date_from_show or sub.date_from, None)
        end = try_value(lambda: placement.date_to, None)
        hours = parse_amount(try_value(lambda: sub.week_hours, None))
        week_hours = u'{:3.1f}'.format(hours).replace(u'.', u',') \
            if hours is not None else u'23,0'

        return self.identity_fields(o) + [
            ('f_proslipsidate', format_ergani_date(start)),
            ('f_proslipsitime',
             (datetime.datetime.now() + timedelta(hours=2)).strftime('%H:%M')),
            ('f_apoxwrisitime', u'20:00'),
            ('f_week_hours', week_hours),
            ('f_eidikothta', o.profession_code_oaed or u''),
            ('f_eidikothta_anal', u''),
            ('f_proipiresia', try_value(lambda: sub.work_experience_years)),
            ('f_apodoxes',
             format_legacy_amount(try_value(lambda: sub.last_total_grosspay, 0))),
            ('f_hour_apodoxes',
             format_legacy_amount(try_value(lambda: sub.last_hourspay, 0))),
            ('f_sxeshapasxolisis', u'1'),
            ('f_orismenou_apo', format_ergani_date(start)),
            ('f_orismenou_ews', format_ergani_date(end)),
            ('f_kathestosapasxolisis', try_value(lambda: o.type().work_mode)),
            ('f_xaraktirismos', u'1'),
            ('f_special_case', u''),
            ('f_responsible_position', u''),
            ('f_working_time_digital_organization', u'0'),
            ('f_full_employment_hours', u'030,0'),
            ('f_week_days', u'5'),
            ('f_euelikto_wrario_minutes', u'0'),
            ('f_working_card', u'0'),
            ('f_dialeimma_minutes', u'0'),
            ('f_dialeimma_entos_wrariou', u'0'),
            ('f_topothetisioaed', u'0'),
            ('f_programaoaed', u''),
            ('f_replaceprograma', u''),
            ('f_replaceprograma_afm', u''),
            ('f_replaceprograma_amka', u''),
        ] + E3N_DEFAULTS


class XMLWriteE7Action(ErganiXMLAction):
    """Αναγγελία λύσης σύμβασης Ε7 (πρότυπο E7N)."""

    root_tag = 'AnaggeliesE7N'
    record_tag = 'AnaggeliaE7N'
    namespace = 'http://www.yeka.gr/E7N'
    schema_file = 'E7N_v1.xsd'
    file_prefix = 'ergani_e7n'

    def __init__(self, short_description):
        super(XMLWriteE7Action, self).__init__(short_description)
        self.__name__ = 'create_xml_e7_for_erganh'

    def record_fields(self, o):
        placement = try_value(lambda: o.current_placement(), None)
        sub = try_value(lambda: placement.substituteplacement, None)
        start = try_value(lambda: sub.date_from_show or sub.date_from, None)
        end = try_value(lambda: placement.date_to, None)

        return self.identity_fields(o) + [
            ('f_xaraktirismos', u'1'),
            ('f_sxeshapasxolisis', u'1'),
            ('f_kathestosapasxolisis', try_value(lambda: o.type().work_mode, u'0')),
            ('f_oros', u'0'),
            ('f_eidikothta', o.profession_code_oaed or u''),
            ('f_apodoxes',
             format_ergani_amount(try_value(lambda: sub.last_total_grosspay, 0))),
            ('f_proslipsidate', format_ergani_date(start)),
            ('f_lixisymbashdate', format_ergani_date(end)),
            ('f_apolysisdate', format_ergani_date(end)),
            ('f_comments', u''),
            ('f_logosperatosis', u'0'),
            ('f_logosperatosiscomments', u''),
            ('f_foreign_file', u''),
            ('f_young_file', u''),
        ]


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
