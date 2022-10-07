# -*- coding: utf-8 -*-
from dideman import settings
from dideman.dide.employee.decorators import match_required
from dideman.dide.models import (Permanent, PaymentReport, PaymentCategory,
                                 NonPermanent, Employee, Payment, PaymentCode,
                                 Administrative, PaymentCategoryTitle, PaymentEmployeePDF)
from dideman.dide.util.settings import SETTINGS

from dideman.dide.util.pay_reports import (generate_pdf_structure,
                                           generate_pdf_landscape_structure,
                                           calc_reports, rprts_from_user)
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Image, Table
from reportlab.platypus.doctemplate import NextPageTemplate, SimpleDocTemplate
from reportlab.platypus.flowables import PageBreak
import pyPdf

from pyPdf import PdfFileWriter, PdfFileReader

from reportlab.pdfgen import canvas

from itertools import chain
import operator
import datetime
import os
import os.path
import mimetypes
from cStringIO import StringIO

pay_pdf = {}

@csrf_protect
@match_required
def help(request):
    return render_to_response('salary/help.html',
                              RequestContext(request, {}))


@csrf_protect
@match_required
def print_pay(request, id):
    non_p = 1
    rpt = PaymentReport.objects.get(pk=id)
    if request.session['matched_employee_id'] == rpt.employee_id:
        emp = Employee.objects.get(id=request.session['matched_employee_id'])
        try:
            emptype = Permanent.objects.get(parent_id=emp.id)
        except Permanent.DoesNotExist:
            try:
                emptype = NonPermanent.objects.get(parent_id=emp.id)
                non_p = 0
            except NonPermanent.DoesNotExist:
                try:
                    emptype = Administrative.objects.get(parent_id=emp.id)
                except Administrative.DoesNotExist:
                    emptype = 0
        except:
            raise
    else:
        request.session.clear()
        return HttpResponseRedirect(
            '/employee/match/?next=/salary/view/')
    print emptype
    dict_tax_codes = {c.id: c.calc_type for c in PaymentCode.objects.all()}
    report = {}
    report['report_type'] = '0'
    report['type'] = rpt.type
    report['year'] = rpt.year
    report['emp_type'] = non_p
    if non_p == 1:
        report['registration_number'] = emptype.registration_number
    report['vat_number'] = emp.vat_number
    report['lastname'] = emp.lastname
    report['firstname'] = emp.firstname
    report['fathername'] = emp.fathername
    report['address'] = emp.address
    report['tax_office'] = emp.tax_office
    report['profession'] = emp.profession
    report['telephone_number1'] = emp.telephone_number1
    report['rank'] = rpt.rank
    report['net_amount1'] = rpt.net_amount1
    report['net_amount2'] = rpt.net_amount2

    pay_cat_list = []
    for i in PaymentCategory.objects.filter(paymentreport=rpt.id):
        pay_cat_dict = {}
        pay_cat_dict['title'] = i.title
        pay_cat_dict['month'] = i.month
        pay_cat_dict['year'] = i.year
        pay_cat_dict['start_date'] = i.start_date
        pay_cat_dict['end_date'] = i.end_date
        pay_cat_dict['payments'] = []
        for o in Payment.objects.filter(category=i.id):
            p = {}
            p['type'] = o.type
            p['code'] = o.code
            p['amount'] = float(o.amount)
            p['info'] = o.info
            p['code_tax'] = dict_tax_codes[o.code_id]
            pay_cat_dict['payments'].append(p)
        pay_cat_list.append(pay_cat_dict)
    report['payment_categories'] = pay_cat_list

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=pay_report.pdf'
    registerFont(TTFont('DroidSans', os.path.join(settings.MEDIA_ROOT,
                                                  'DroidSans.ttf')))
    registerFont(TTFont('DroidSans-Bold', os.path.join(settings.MEDIA_ROOT,
                                                       'DroidSans-Bold.ttf')))

    doc = SimpleDocTemplate(response, pagesize=A4)
    doc.topMargin = 1.0 * cm
    elements = generate_pdf_structure([report])
    doc.build(elements)
    return response


@csrf_protect
@match_required
def print_mass_pay(request, year):
    """
    This function contains the required methods to create a PDF
    report. It will be merged with the salary app some time 
    later.
    """

    def sch (c):
        try:
            return c.permanent and c.permanent.organization_serving()
        except:
            return c.organization_serving()
        
    payment_codes = PaymentCode.objects.all()
    category_titles = PaymentCategoryTitle.objects.all()
    emp = Employee.objects.get(id=request.session['matched_employee_id'])
    try:
        emptype = Permanent.objects.get(parent_id=emp.id)
    except Permanent.DoesNotExist:
        try:
            emptype = NonPermanent.objects.get(parent_id=emp.id)
        except NonPermanent.DoesNotExist:
            try:
                emptype = Administrative.objects.get(parent_id=emp.id)
            except Administrative.DoesNotExist:
                emptype = 0
    except:
        raise

    emp_payments = rprts_from_user(emp.id, year, '11,12,21')

        

    u = set([x['employee_id'] for x in emp_payments])
    y = {x['employee_id']: x['year'] for x in emp_payments}
    dict_emp = {c.id: [c.lastname,
                       c.firstname,
                       c.vat_number,
                       c.fathername,
                       c.address,
                       c.tax_office,
                       u'%s' % c.profession,
                       u'%s' % c.profession.description,
                       c.telephone_number1,
                       sch(c)] for c in Employee.objects.filter(id__in=u)}
            
    elements = []
    reports = []
    for empx in u:
        r_list = calc_reports(filter(lambda s: s['employee_id'] == empx, emp_payments))
        hd = r_list[0]
        ft = [r_list[-2]] + [r_list[-1]]
        dt = r_list
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


    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=pay_report_%s.pdf' % year
    registerFont(TTFont('DroidSans', os.path.join(settings.MEDIA_ROOT,
                                                  'DroidSans.ttf')))
    registerFont(TTFont('DroidSans-Bold', os.path.join(settings.MEDIA_ROOT,
                                                       'DroidSans-Bold.ttf')))

    doc = SimpleDocTemplate(response, pagesize=A4)
    doc.topMargin = 0.5 * cm
    doc.bottomMargin = 0.5 * cm
    doc.leftMargin = 1.5 * cm
    doc.rightMargin = 1.5 * cm
    doc.pagesize = landscape(A4) 
        
    if year == '2012':
        style = getSampleStyleSheet()
        style.add(ParagraphStyle(name='Center', alignment=TA_CENTER,
                                 fontName='DroidSans', fontSize=12))
        elements = [Paragraph(u'ΠΑΡΑΚΑΛΟΥΜΕ ΑΠΕΥΘΥΝΘΕΙΤΕ ΣΤΗΝ ΥΠΗΡΕΣΙΑ ΓΙΑ ΤΗΝ ΜΙΣΘΟΛΟΓΙΚΗ ΚΑΤΑΣΤΑΣΗ ΤΟΥ 2012', style['Center'])]
    else:    
        elements = generate_pdf_landscape_structure(reports)
    


    doc.build(elements)
    return response


@csrf_protect
@match_required
def view(request):
                                                    
    f_path = '%s/pdffiles/extfiles' % settings.STATIC_URL
    mayhavepdf = 0
    pay_pdf = []
    show_pdf = 0
    if 'logout' in request.GET:
        request.session.clear()
        return HttpResponseRedirect('/?logout=True')

    if 'print' in request.GET:
        if 'id' in request.GET:
            return print_pay(request, request.GET['id'])
        else:
            return HttpResponseRedirect('/salary/view/')

    if 'emp-action' in request.POST:
        if request.POST['emp-action'] != '0':
            return print_mass_pay(request, request.POST['emp-action'])
        else:
            return HttpResponseRedirect('/salary/view/')

    else:
        emp = Employee.objects.get(id=request.session['matched_employee_id'])
        try:
            emptype = Permanent.objects.get(parent_id=emp.id)
        except Permanent.DoesNotExist:
            try:
                emptype = NonPermanent.objects.get(parent_id=emp.id)
                
            except NonPermanent.DoesNotExist:
                try:
                    emptype = Administrative.objects.get(parent_id=emp.id)
                except Administrative.DoesNotExist:
                    emptype = 0
        except:
            raise

        pay = PaymentReport.objects.filter(employee=emp.id).order_by('-year','-type')
        
        if emp.vat_number != "":
            
            pdf_month = PaymentEmployeePDF.objects.filter(employee_vat=emp.vat_number,pdf_file_type=1).order_by('-id')
            pdf_year = PaymentEmployeePDF.objects.filter(employee_vat=emp.vat_number,pdf_file_type=2).order_by('-id')
        current_year = datetime.date.today().year
        per_year = {p.year: p for p in pay if p.year < current_year}
        all_year = set(p.year for p in pay)
        
        year_t = {y: emptype.totals_per_year(y) for y in all_year}

        o_year_t = [(k, "{:12.2f}".format(v)) for k, v in year_t.iteritems()]
        o_year_t.sort(reverse=True)
        paginator = Paginator(pay, 15)

        page = request.GET.get('page')
        try:
            pay_page = paginator.page(page)
        except PageNotAnInteger:
            pay_page = paginator.page(1)
        except EmptyPage:
            pay_page = paginator.page(paginator.num_pages)

        return render_to_response('salary/salary.html',
                                  RequestContext(request, {'emp': emptype,
                                                           'yearly_reports': per_year,
                                                           'total_per_year': o_year_t,
                                                           'payments': pay_page,
                                                           'paypdf_year': pdf_year,
                                                           'paypdf_month': pdf_month
                                                            }))

@csrf_protect
@match_required
def showpdf(request):
    sign = os.path.join(settings.MEDIA_ROOT, "signature.png")
    mimetypes.init()
    response = None
    if 'f' in request.GET:
        
        fr = open(os.path.join(settings.MEDIA_ROOT,'pdffiles','extracted','%s' % request.GET['f']), "rb")
        imgTemp = StringIO()
        imgDoc = canvas.Canvas(imgTemp)
        if request.GET['o'] == 'l':
            imgDoc.drawImage(sign, 529, 40, 290/2, 154/2)
        else:
            imgDoc.drawImage(sign, 70, 40, 290/2, 154/2)

        imgDoc.save()
        overlay = PdfFileReader(StringIO(imgTemp.getvalue())).getPage(0)
        page = PdfFileReader(fr).getPage(0)
                            
        page.mergePage(overlay)
        pdf_out = PdfFileWriter()
        pdf_out.addPage(page)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=%s' % request.GET['f']

        pdf_out.write(response)
            
    return response
    
