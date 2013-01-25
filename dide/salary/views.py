# -*- coding: utf-8 -*-
from dideman import settings
from dideman.dide.employee.decorators import match_required
from dideman.dide.models import (Permanent, PaymentReport, PaymentCategory,
                                 NonPermanent, Employee, Payment, PaymentCode)
from dideman.dide.util.settings import SETTINGS
from dideman.dide.util.pay_reports import (generate_pdf_structure,
                                           generate_pdf_landscape_structure,
                                           reports_calc_amount)
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
from itertools import chain
import datetime
import os


@match_required
def print_pay(request, id):
    rpt = PaymentReport.objects.get(pk=id)
    emptype = 0
    if request.session['matched_employee_id'] == rpt.employee_id:
        emp = Employee.objects.get(id=request.session['matched_employee_id'])
        try:
            emp = Permanent.objects.get(parent_id=emp.id)
            emptype = 1
        except Permanent.DoesNotExist:
            emp = NonPermanent.objects.get(parent_id=emp.id)
            emptype = 2
        except NonPermanent.DoesNotExist:
            emptype = 0
            raise
        except:
            raise
    else:
        request.session.clear()
        return HttpResponseRedirect(
            '/employee/match/?next=/salary/view/')

    dict_tax_codes = {c.id: c.is_tax for c in PaymentCode.objects.all()}
    report = {}
    report['report_type'] = '0'
    report['type'] = rpt.type
    report['year'] = rpt.year
    report['emp_type'] = emptype
    if emptype == 1:
        report['registration_number'] = emp.registration_number
    report['vat_number'] = emp.vat_number
    report['lastname'] = emp.lastname
    report['firstname'] = emp.firstname
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

    response = HttpResponse(mimetype='application/pdf')
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


@match_required
def print_mass_pay(request, year):

    rpt = PaymentReport.objects.filter(employee_id=request.session['matched_employee_id'],
                                       year=year)
    emptype = 0
    emp = Employee.objects.get(id=request.session['matched_employee_id'])
    try:
        emp = Permanent.objects.get(parent_id=emp.id)
        emptype = 1
    except Permanent.DoesNotExist:
        emp = NonPermanent.objects.get(parent_id=emp.id)
        emptype = 2
    except NonPermanent.DoesNotExist:
        emptype = 0
        raise
    except:
        raise

    obj = PaymentCode.objects.all()
    dict_codes = {c.id: c.description for c in obj}
    dict_tax_codes = {c.id: c.is_tax for c in obj}

    tax_codes = [c for c in dict_codes.keys()]

    payments_list = []

    for o in rpt:
        if o.type_id > 15:
            taxed_list = [p.code_id for p in Payment.objects.select_related().filter(category__paymentreport=o.id,
                                                                                     code__is_tax=1)]
            if taxed_list:
                for p in Payment.objects.select_related().filter(category__paymentreport=o.id):
                    payments_list.append({'code_id': p.code_id, 'type': p.type, 'amount': p.amount})
        else:
            for p in Payment.objects.select_related().filter(category__paymentreport=o.id):
                payments_list.append({'code_id': p.code_id, 'type': p.type, 'amount': p.amount})

    gr, de, et = reports_calc_amount(payments_list, tax_codes)
    grd = [{'type': 'gr', 'code_id': x[0], 'amount': x[1]} for x in gr]
    ded = [{'type': 'de', 'code_id': x[0], 'amount': x[1]} for x in de]
    etd = [{'type': 'et', 'code_id': x[0], 'amount': x[1]} for x in et]

    calctd_payments_list = [x for x in chain(grd, ded)]
    report = {}

    report['report_type'] = '1'
    report['type'] = ''
    report['year'] = year
    report['emp_type'] = emptype
    if emptype == 1:
        report['registration_number'] = emp.registration_number
    report['vat_number'] = emp.vat_number
    report['lastname'] = emp.lastname
    report['firstname'] = emp.firstname
    report['rank'] = emp.rank()
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

    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=pay_report_%s.pdf' % year
    registerFont(TTFont('DroidSans', os.path.join(settings.MEDIA_ROOT,
                                                  'DroidSans.ttf')))
    registerFont(TTFont('DroidSans-Bold', os.path.join(settings.MEDIA_ROOT,
                                                       'DroidSans-Bold.ttf')))

    doc = SimpleDocTemplate(response, pagesize=A4)
    doc.topMargin = 0.5 * cm
    doc.bottomMargin = 0.5 * cm
    doc.leftMargin = 0.5 * cm
    doc.rightMargin = 0.5 * cm

    doc.pagesize = landscape(A4) 
    elements = generate_pdf_landscape_structure([report])
    doc.build(elements)
    return response


@csrf_protect
@match_required
def view(request):
    if 'logout' in request.GET:
        request.session.clear()
        return HttpResponseRedirect(
            '/employee/match/?next=/salary/view/')
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
            emptype = NonPermanent.objects.get(parent_id=emp.id)
        except NonPermanent.DoesNotExist:
            emptype = 0
            raise
        except:
            raise

        pay = PaymentReport.objects.filter(employee=emp.id).order_by('-year','-type')
        per_year = {p.year: p for p in pay}
        paginator = Paginator(pay, 10)

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
                                                           'payments': pay_page}))
