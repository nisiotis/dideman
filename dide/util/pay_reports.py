# -*- coding: utf-8 -*-
#---- usage ----
#p = PaymentFileName.objects.filter(description__startswith = 'Ένταλμα')
#all_emp = prtest.rprts_from_file(p)
#u = set([x['employee_id'] for x in all_emp])

#tg = []; td = []; te = []
#for x in u:
#    g, d, e = prtest.calc_amount(filter(lambda s: s['employee_id'] == x, all_emp))
#    tg.append(g)
#    td.append(d)
#    te.append(e)

# we need to remove the loans and the non taxed codes (added the code, maybe fixed)
from dideman import settings
from django.db import connection, transaction
from itertools import groupby
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
from dideman.dide.util.settings import SETTINGS
from django.http import HttpResponse
import os
import datetime



def reports_calc_amount(dict_list, taxed_codes):
    """
    Returns the totals for an employee from a set of paymentreports
    Accepts a list of dicts of payments and a list of taxed codes
    """
    dic_lst = sorted(dict_list, key=lambda x: x['type'])
    de_l = filter(lambda x: x['type'] == 'de', dic_lst)
    gr_l = filter(lambda x: x['type'] == 'gr', dic_lst)
    et_l = filter(lambda x: x['type'] == 'et', dic_lst)
    
    de_ca = [[x['code_id'], x['amount']] for x in de_l if x['code_id'] in taxed_codes] if len(de_l) > 0 else []
    gr_ca = [[x['code_id'], x['amount']] for x in gr_l] if len(gr_l) > 0 else []
    et_ca = [[x['code_id'], x['amount']] for x in et_l] if len(et_l) > 0 else []
    de_ca_ex = []

    sde_ca = sorted(de_ca, key=lambda x: x[0])
    sgr_ca = sorted(gr_ca, key=lambda x: x[0])
    set_ca = sorted(et_ca, key=lambda x: x[0])

    de = []
    for k, g in groupby(sde_ca, key=lambda x: x[0]):
 	de.append([k,sum([float(i[1]) for i in g])])
    gr = []
    for k, g in groupby(sgr_ca, key=lambda x: x[0]):
 	gr.append([k,sum([float(i[1]) for i in g])])
    et = []
    for k, g in groupby(set_ca, key=lambda x: x[0]):
 	et.append([k,sum([float(i[1]) for i in g])])
    return gr, de, et


def dict_fetch_all(cursor):
    """
    Returns all rows from a cursor as a dict
    Accepts a populated cursor
    """
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


def rprts_from_file(queryset):
    """
    Returns a list of dicts of employees and their payments
    defined in paymentreports from a set of paymentreportfiles.
    Accepts a queryset of paymentfilenames
    """
    cursor = connection.cursor()
    sql ="""SELECT dide_paymentreport.employee_id, dide_payment.*
            FROM dide_paymentfilename
            INNER JOIN dide_paymentreport
            ON dide_paymentreport.paymentfilename_id = dide_paymentfilename.id
            INNER JOIN dide_paymentcategory
            ON dide_paymentcategory.paymentreport_id = dide_paymentreport.id
            INNER JOIN dide_payment
            ON dide_payment.category_id = dide_paymentcategory.id
            WHERE dide_paymentfilename.id
            IN ({0});"""

    qry = ','.join(['%s' % x.id for x in queryset])

    result = cursor.execute(sql.format(qry))
    return dict_fetch_all(cursor)


def generate_pdf_structure(reports):
    """
    Returns the elements object for the report to be generated in PDF
    Accepts a schema of the report
    """

    def numtoStr(s):
        """Convert string to either int or float."""
        try:
            ret = int(s)
        except ValueError:
            ret = float(s)
        return ret

    months = [u'Ιανουάριος', u'Φεβρουάριος', u'Μάρτιος',
              u'Απρίλιος', u'Μάιος', u'Ιούνιος',
              u'Ιούλιος', u'Αύγουστος', u'Σεπτέμβριος',
              u'Οκτώβριος', u'Νοέμβριος', u'Δεκέμβριος']
    elements = []
    for report in reports:
        logo = os.path.join(settings.MEDIA_ROOT, "logo.png")
    
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
        
        if report['report_type'] == '0':
            elements.append(Paragraph(u'ΒΕΒΑΙΩΣΗ ΑΠΟΔΟΧΩΝ', heading_style['Center']))
            if report['type'] > 12:
                elements.append(Paragraph(u'Αποδοχές %s %s' %
                                          (report['type'], report['year']),
                                          heading_style["Center"]))
            else:
                elements.append(Paragraph(u'Μισθοδοσία %s %s' %
                                          (report['type'], report['year']),
                                          heading_style['Center']))
            elements.append(Paragraph(u' ', heading_style['Spacer']))
        
        else:
            elements.append(Paragraph(u'ΒΕΒΑΙΩΣΗ ΑΠΟΔΟΧΩΝ %s' % report['year'], heading_style['Center']))
            elements.append(Paragraph(u' ', heading_style['Spacer']))
        
        if report['emp_type'] == 1:
            headdata = [[Paragraph(u'ΑΡ. ΜΗΤΡΩΟΥ', tbl_style['Left']),
                         Paragraph('%s' % report['registration_number'] or u'Δ/Υ',
                                   tbl_style['Left']),
                         Paragraph('ΑΦΜ', tbl_style['Left']),
                         Paragraph(u'%s' % report['vat_number'], tbl_style['Left'])],
                        [Paragraph(u'ΕΠΩΝΥΜΟ', tbl_style['Left']),
                         Paragraph('%s' % report['lastname'], tbl_style['Left']),
                         Paragraph('', tbl_style['Left']),
                         Paragraph('', tbl_style['Left'])],
                        [Paragraph(u'ΟΝΟΜΑ', tbl_style['Left']),
                         Paragraph('%s' % report['firstname'], tbl_style['Left']),
                         Paragraph(u'ΒΑΘΜΟΣ - ΚΛΙΜΑΚΙΟ', tbl_style['Left']),
                         Paragraph(u'%s' % report['rank'] if report['rank'] is not None else u'Δ/Υ',
                                   tbl_style['Left'])]]
        else:
            headdata = [[Paragraph(u'ΑΦΜ', tbl_style['Left']),
                         Paragraph('%s' % report['vat_number'],
                                   tbl_style['Left']),
                         Paragraph('', tbl_style['Left']),
                         Paragraph('', tbl_style['Left'])],
                        [Paragraph(u'ΕΠΩΝΥΜΟ', tbl_style['Left']),
                         Paragraph('%s' % report['lastname'], tbl_style['Left']),
                         Paragraph('', tbl_style['Left']),
                         Paragraph('', tbl_style['Left'])],
                        [Paragraph(u'ΟΝΟΜΑ', tbl_style['Left']),
                         Paragraph('%s' % report['firstname'], tbl_style['Left']),
                         Paragraph('', tbl_style['Left']),
                         Paragraph('', tbl_style['Left'])]]
    
        table1 = Table(headdata, style=tsh,
                       colWidths=[3 * cm, 6 * cm, 5 * cm, 3 * cm])
        elements.append(table1)
        elements.append(Paragraph(u' ', heading_style['Spacer']))
        del data
        data = []
        total_amount = 0
        total_tax_amount = 0
        for i in report['payment_categories']:
            elements.append(Paragraph(u' ', heading_style['Spacer']))
            s = u'%s' % i['title']
            if (i['start_date'] and i['start_date'] != 'NULL') and (i['end_date'] and i['start_date'] != 'NULL'):
                s1 = "/".join(list(reversed(i['start_date'].split('-'))))
                s2 = "/".join(list(reversed(i['end_date'].split('-'))))
                s += ' (%s - %s) ' % (s1, s2)
            if (i['month'] and i['month'] != 'NULL') and (i['year'] and i['year'] !='NULL'):
                s += ' %s %s' % (months[int(i['month']-1)], i['year'])
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
            gret = []
            de = []
            data = []
            grnum = 0
            denum = 0
            for p in i['payments']:
                if p['type'] == 'gr' or p['type'] == 'et':
                    s = u'%s' % p['code']
                    gret.append([Paragraph(s, tbl_style['Left']),
                                 Paragraph('%.2f €' % p['amount'],
                                           tbl_style['Right'])])
                    if p['type'] == 'gr':
                        grnum += float(p['amount'])
                else:
                    s = u'%s' % p['code']
                    if p['info'] is not None:
                        s = s + " (%s)" % p['info']
                    if int(p['code_tax']) == 1:
                        total_tax_amount += p['amount']
                    
                    de.append([Paragraph(s, tbl_style['Left']),
                               Paragraph('%.2f €' % p['amount'],
                                         tbl_style['Right'])])
                    denum += float(p['amount'])
            _get = lambda l, i: l[i] if i < len(l) else ['', '']
            data = [_get(gret, i) + _get(de, i) for i in range(0, max(len(gret),
                                                                      len(de)))]
            table4 = Table(data, style=ts, colWidths=[6.5 * cm, 2.0 * cm,
                                                      6.5 * cm, 2.0 * cm])
            elements.append(table4)
            total_amount += float(grnum) - float(denum)
            del data
            data = []
            elements.append(Paragraph(u' ', heading_style['Spacer']))
        elements.append(Paragraph(u' ', heading_style['Spacer']))
        elements.append(Paragraph(u' ', heading_style['Spacer']))
        del data
        if report['report_type'] == '0':
            data = []
            data.append([Paragraph('Πληρωτέο', tbl_style['BoldLeft'])])
            table5 = Table(data, style=ts, colWidths=[17 * cm])
            elements.append(table5)
            del data
            data = []
        
            if report['net_amount1'] != '0' and report['net_amount2'] != '0':
                data.append([Paragraph('Α\' δεκαπενθήμερο', tbl_style['Left']),
                             Paragraph('%.2f €' % numtoStr(report['net_amount1']),
                                       tbl_style['Right']), '', ''])
                data.append([Paragraph('Β\' δεκαπενθήμερο', tbl_style['Left']),
                             Paragraph('%.2f €' % numtoStr(report['net_amount2']),
                                       tbl_style['Right']), '', ''])
            else:
                data.append([Paragraph('Σύνολο', tbl_style['Left']),
                             Paragraph('%.2f €' % total_amount,
                                       tbl_style['Right']), '', ''])
                total_amount = 0
        
            table5 = Table(data, style=ts, colWidths=[6.5 * cm, 2.0 * cm,
                                                      6.5 * cm, 2.0 * cm])
            elements.append(table5)
            del data
        else:
            data = []
            data.append([Paragraph('Καθαρό Ποσό', tbl_style['Left']),
                         Paragraph('%.2f €' % total_amount, tbl_style['Right']),
                         Paragraph('%s' % SETTINGS.get_desc('tax_reduction_factor'), tbl_style['Left']),
                         Paragraph('%.2f €' % (total_tax_amount / float(SETTINGS['tax_reduction_factor'])), tbl_style['Right'])
                         ])
            total_amount = 0
            total_tax_amount = 0
            table5 = Table(data, style=ts, colWidths=[6.5 * cm, 2.0 * cm,
                                                      6.5 * cm, 2.0 * cm])
            elements.append(table5)
            del data



        today = datetime.date.today()
        elements.append(Paragraph(u' ', heading_style['Spacer']))
        elements.append(Paragraph(u' ', heading_style['Spacer']))
        
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
        elements.append(PageBreak())
    return elements
