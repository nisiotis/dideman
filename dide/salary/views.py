# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from dideman.dide.models import Permanent
from dideman.dide.employee.decorators import match_required
from dideman.dide.util.common import get_class
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect
from dideman import settings
from dideman.dide.util.settings import SETTINGS
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus.doctemplate import SimpleDocTemplate
from reportlab.platypus import Paragraph, Image, Table
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import datetime
import os


def get_form(klass):
    return get_class('dideman.dide.applications.forms.%sForm' % klass)


@match_required
def print_app(request, set_id):
    def numtoStr(s):
        """Convert string to either int or float."""
        try:
            ret = int(s)
        except ValueError:
            ret = float(s)
        return ret
    logo = os.path.join(settings.MEDIA_ROOT, "logo.png")
    pay = Payment.objects.get(pk=id)
    emp = Permanent.objects.get(pk=pay.employee_id)
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=pay_report.pdf'
    registerFont(TTFont('DroidSans', os.path.join(settings.MEDIA_ROOT,
                                                  'DroidSans.ttf')))
    registerFont(TTFont('DroidSans-Bold', os.path.join(settings.MEDIA_ROOT,
                                                       'DroidSans-Bold.ttf')))
    width, height = A4
    head_logo = getSampleStyleSheet()
    head_logo.add(ParagraphStyle(name='Center', alignment=TA_CENTER,
                                 fontName='DroidSans', fontSize=8))
    heading_style = getSampleStyleSheet()
    heading_style.add(ParagraphStyle(name='Center', alignment=TA_CENTER,
                                     fontName='DroidSans-Bold',
                                     fontSize=12))
    heading_style.add(ParagraphStyle(name='Spacer', spaceBefore=5,
                                     spaceAfter=5,
                                     fontName='DroidSans-Bold',
                                     fontSize=12))
    signature = getSampleStyleSheet()
    signature.add(ParagraphStyle(name='Center', alignment=TA_CENTER,
                                 fontName='DroidSans', fontSize=10))
    tbl_style = getSampleStyleSheet()
    tbl_style.add(ParagraphStyle(name='Left', alignment=TA_LEFT,
                                 fontName='DroidSans', fontSize=10))
    tbl_style.add(ParagraphStyle(name='Right', alignment=TA_RIGHT,
                                 fontName='DroidSans', fontSize=10))
    tbl_style.add(ParagraphStyle(name='BoldLeft', alignment=TA_LEFT,
                                 fontName='DroidSans-Bold', fontSize=10))

    tsl = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
           ('FONT', (0, 0), (-1, 0), 'DroidSans'),
           ('FONTSIZE', (0, 0), (-1, 0), 8),
           ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
           ('TOPPADDING', (0, 0), (-1, -1), 0)]
    tsh = [('ALIGN', (1, 1), (-1, -1), 'LEFT'),
           ('BOX', (0, 0), (-1, -1), 0.25, colors.black)]
    ts = [('ALIGN', (1, 1), (-1, -1), 'LEFT'),
          ('FONT', (0, 0), (-1, 0), 'DroidSans'),
          ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
          ('GRID', (0, 0), (-1, -1), 0.5, colors.black)]
    tsf = [('ALIGN', (1, 1), (-1, -1), 'CENTER')]
    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    im = Image(logo)
    im.drawHeight = 1.25 * cm
    im.drawWidth = 1.25 * cm
    data = []
    data.append([im, ""])
    data.append([Paragraph(u'ΕΛΛΗΝΙΚΗ ΔΗΜΟΚΡΑΤΙΑ', head_logo['Center']), ''])
    data.append([Paragraph(u'ΥΠΟΥΡΓΕΙΟ ΠΑΙΔΕΙΑΣ, ΘΡΗΣΚΕΥΜΑΤΩΝ,',
                           head_logo['Center']), ''])
    data.append([Paragraph(u'ΠΟΛΙΤΙΣΜΟΥ ΚΑΙ ΑΘΛΗΤΙΣΜΟΥ',
                           head_logo['Center']), ''])
    data.append([Paragraph(u'ΠΕΡΙΦΕΡΙΑΚΗ ΔΙΕΥΘΥΝΣΗ ΠΡΩΤΟΒΑΘΜΙΑΣ',
                           head_logo['Center']), ''])
    data.append([Paragraph(u'ΚΑΙ ΔΕΥΤΕΡΟΒΑΘΜΙΑΣ ΕΚΠΑΙΔΕΥΣΗΣ ΝΟΤΙΟΥ ΑΙΓΑΙΟΥ',
                           head_logo['Center']), ''])
    data.append([Paragraph(u'ΔΙΕΥΘΥΝΣΗ ΔΕΥΤΕΡΟΒΑΘΜΙΑΣ ΕΚΠΑΙΔΕΥΣΗΣ ΔΩΔΕΚΑΝΗΣΟΥ',
                           head_logo['Center']), ''])
    table0 = Table(data, style=tsl, colWidths=[8.0 * cm, 11.0 * cm])
    elements.append(table0)
    elements.append(Paragraph(u' ', heading_style['Spacer']))
    elements.append(Paragraph(u'ΒΕΒΑΙΩΣΗ ΑΠΟΔΟΧΩΝ', heading_style['Center']))
    if pay.month > 12:
        elements.append(Paragraph(u'Αποδοχές %s %s' % \
                                  (pay.get_month_display(), pay.year),
                                  heading_style["Center"]))
    else:
        elements.append(Paragraph(u'Μισθοδοσία %s %s' % \
                                  (pay.get_month_display(), pay.year),
                                  heading_style['Center']))
    elements.append(Paragraph(u' ', heading_style['Spacer']))
    headdata = [[Paragraph(u'ΑΡ. ΜΗΤΡΩΟΥ', tbl_style['Left']),
                 Paragraph('%s' % emp.registration_number, tbl_style['Left']),
                 Paragraph('ΑΦΜ', tbl_style['Left']),
                 Paragraph(u'%s' % emp.vat_number, tbl_style['Left'])],
                [Paragraph(u'ΕΠΩΝΥΜΟ', tbl_style['Left']),
                 Paragraph('%s' % emp.lastname, tbl_style['Left']),
                 Paragraph('', tbl_style['Left']),
                 Paragraph('', tbl_style['Left'])],
                [Paragraph(u'ΟΝΟΜΑ', tbl_style['Left']),
                 Paragraph('%s' % emp.firstname, tbl_style['Left']),
                 Paragraph(u'ΒΑΘΜΟΣ - ΚΛΙΜΑΚΙΟ', tbl_style['Left']),
                 Paragraph(u'%s' % pay.get_rank_display(), tbl_style['Left'])]]
    table1 = Table(headdata, style=tsh,
                   colWidths=[3 * cm, 6 * cm, 5 * cm, 3 * cm])
    elements.append(table1)
    elements.append(Paragraph(u' ', heading_style['Spacer']))
    del data
    data = []
    for i in PaymentIncome.objects.filter(payment=id):
        elements.append(Paragraph(u' ', heading_style['Spacer']))
        s = '%s' % i.get_type_display()
        data.append([Paragraph('%s' % s, tbl_style['BoldLeft'])])
        table2 = Table(data, style=tsh, colWidths=[17 * cm])
        elements.append(table2)
        del data
        data = []
        data.append([Paragraph('Αποδοχές', tbl_style['BoldLeft']),
                     Paragraph('Κρατήσεις', tbl_style['BoldLeft'])])
        table3 = Table(data, style=ts, colWidths=[8.5 * cm, 8.5 * cm])
        elements.append(table3)
        del data
        data = []
        for p in PaymentIncomeSection.objects.filter(paymentincome=i.id):
            if p.type == 'gr' or p.type == 'et':
                s = u'%s' % p.paymentcode
                data.append([Paragraph(s, tbl_style['Left']),
                             Paragraph('%.2f €' % numtoStr(p.amount),
                                       tbl_style['Right']), '', ''])
            else:
                s = u'%s' % p.paymentcode
                if p.moreinfo != '':
                    s = s + " (%s)" % p.moreinfo
                data.append(['', '', Paragraph(s, tbl_style['Left']),
                             Paragraph('%.2f €' % numtoStr(p.amount),
                                       tbl_style['Right'])])
        id = 0
        for index, item in enumerate(data):
            if data[index][3] == '':
                id = id + 1
        for index, item in enumerate(data):
            if index + id < len(data):
                data[index][2] = data[index + id][2]
                data[index][3] = data[index + id][3]
        for index in range(id):
            data.pop()
        table4 = Table(data, style=ts, colWidths=[6.5 * cm, 2.0 * cm,
                                                  6.5 * cm, 2.0 * cm])
        elements.append(table4)
        del data
        data = []
        elements.append(Paragraph(u' ', heading_style['Spacer']))
    elements.append(Paragraph(u' ', heading_style['Spacer']))
    elements.append(Paragraph(u' ', heading_style['Spacer']))
    del data
    data = []
    data.append([Paragraph('Πληρωτέο', tbl_style['BoldLeft'])])
    table5 = Table(data, style=ts, colWidths=[17 * cm])
    elements.append(table5)
    del data
    data = []
    data.append([Paragraph('Α\' δεκαπενθήμερο', tbl_style['Left']),
                 Paragraph('%.2f €' % numtoStr(pay.netamount1),
                           tbl_style['Right']), '', ''])
    data.append([Paragraph('Β\' δεκαπενθήμερο', tbl_style['Left']),
                 Paragraph('%.2f €' % numtoStr(pay.netamount2),
                           tbl_style['Right']), '', ''])
    table5 = Table(data, style=ts, colWidths=[6.5 * cm, 2.0 * cm,
                                              6.5 * cm, 2.0 * cm])
    elements.append(table5)
    today = datetime.date.today()
    elements.append(Paragraph(u' ', heading_style['Spacer']))
    elements.append(Paragraph(u' ', heading_style['Spacer']))
    del data
    data = []
    data.append([Paragraph(u' ', signature['Center']),
                 Paragraph(u'Ρόδος, %s / %s / %s' %
                           (today.day, today.month, today.year),
                           signature['Center'])])
    data.append([Paragraph(u' ', signature['Center']),
                 Paragraph(u' ', signature['Center'])])
    data.append([Paragraph(u' ', signature['Center']),
                 Paragraph(u'Ο Διευθυντής', signature['Center'])])
    data.append([Paragraph(u' ', signature['Center']),
                 Paragraph(u' ', signature['Center'])])
    data.append([Paragraph(u' ', signature['Center']),
                 Paragraph(u' ', signature['Center'])])
    data.append([Paragraph(u' ', signature['Center']),
                 Paragraph(u' ', signature['Center'])])
    data.append([Paragraph(u' ', signature['Center']),
                 Paragraph(u' ', signature['Center'])])
    data.append([Paragraph(u' ', signature['Center']),
                 Paragraph(SETTINGS['manager'], signature['Center'])])
    table6 = Table(data, style=tsf, colWidths=[11.0 * cm, 6.0 * cm])
    elements.append(table6)
    doc.build(elements)
    return response


@csrf_protect
@match_required
def view(request):
    if 'logout' in request.GET:
        request.session.clear()
        return HttpResponseRedirect(
            '/employee/match/?next=/salary/view/')
    else:
        set = Permanent.objects.get(pk=request.session['matched_employee_id'])
        pay = PaymentReport.objects.filter(
            employee=request.session['matched_employee_id']). \
            order_by('year', 'month')
        return render_to_response('salary/salary.html',
                                  RequestContext(request, {'emp': set,
                                                           'payments': pay}))
