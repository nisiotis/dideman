# -*- coding: utf-8 -*-
from dideman import settings
from django.db import connection, transaction
from itertools import groupby
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
from dideman.dide.util.settings import SETTINGS
from django.http import HttpResponse
import os, re
import datetime
from collections import defaultdict


def calc_reports(emp_reports): 
    types = {1: u'Φόρος που αναλογεί', 2: u'Σύνολο Κρατήσεων', 3: u'Απεργία', 4: u'Σύνταξη', 5:u'Εισφορά', 0: u'Άλλο'}
    groups = defaultdict(lambda : defaultdict(float))
    sums = defaultdict(float)
    d_fact = 0.00
    for r in emp_reports:
        amount = float(r['amount'])
        key = (r['category_id'], r['title'])
        
        if r['group_name']:
            groups[key][r['group_name']] += amount
            sums[r['group_name']] += amount

        if r['type'] == 'gr':
            groups[key][u'1. Αποδοχές από μισθούς ή συντάξεις'] += amount
            sums[u'1. Αποδοχές από μισθούς ή συντάξεις'] += amount

            groups[key][u'Φορολογητέο Ποσό'] += amount
            sums[u'Φορολογητέο Ποσό'] += amount

        if r['calc_type'] == 1: 
            d_fact = (amount * float(SETTINGS['tax_reduction_factor']))
            groups[key][types[r['calc_type']]] += d_fact
            sums[types[r['calc_type']]] += d_fact

        if r['calc_type'] == 2: 
            if r['info'] == None:
                groups[key][types[r['calc_type']]] += amount
                sums[types[r['calc_type']]] += amount
                groups[key][u'Φορολογητέο Ποσό'] -= amount
                sums[u'Φορολογητέο Ποσό'] -= amount

        if r['calc_type'] == 3: 
            groups[key][u'Φορολογητέο Ποσό'] -= amount
            sums[u'Φορολογητέο Ποσό'] -= amount

        if r['calc_type'] == 5: 
            pass


    headers = set()
    for cat, d in groups.items():
        headers |= set(d.keys())

    headers = list(headers)
    headers.sort()
    try:
        headers.remove(types[2])
        headers.append(types[2])
        headers.remove(u'Φορολογητέο Ποσό')
        headers.append(u'Φορολογητέο Ποσό')
        headers.remove(types[1])
        headers.append(types[1])
        headers.remove(u'Φόρος που παρακρατήθηκε')
        headers.append(u'Φόρος που παρακρατήθηκε')

    except:
        pass
    rows = []

    for (cat_id, cat_title), d in groups.items():
        rows.append([cat_title] + [d.get(h, 0) for h in headers])
    rows.append([u' '] + [u' ' for h in headers])
    rows.append([u'Σύνολα'] + [sums[h] for h in headers])
    headers.insert(0, u'Είδος Αποδοχών ή Συντάξεων') 
    return [headers] + rows


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

def rprts_from_user(emp_id, year):
    """ Returns a list of dicts of employee's payments
    defined in paymentreports from a set of paymentreports 
    filtered by year and employee.
    Accepts a year and employee """

    cursor = connection.cursor()
    sql = """SELECT dide_paymentreport.employee_id, dide_paymentreport.year, 
            dide_paymentreport.type_id, dide_paymentcategory.id, dide_paymentcategorytitle.title, 
            dide_paymentcategory.start_date, dide_paymentcategory.end_date, 
            dide_payment.*, dide_paymentcode.calc_type, dide_paymentcode.group_name, dide_paymentcode.description   
            FROM dide_paymentreport
            INNER JOIN dide_paymentcategory
            ON dide_paymentcategory.paymentreport_id = dide_paymentreport.id
            INNER JOIN dide_payment
            ON dide_payment.category_id = dide_paymentcategory.id
            INNER JOIN dide_paymentcode ON dide_payment.code_id = dide_paymentcode.id
            INNER JOIN dide_paymentcategorytitle ON dide_paymentcategory.title_id = dide_paymentcategorytitle.id
            WHERE dide_paymentreport.year = {0}
            AND dide_paymentreport.employee_id = {1}             
            AND dide_payment.type IN ('de', 'gr')
            AND dide_paymentreport.taxed <> 0
            ORDER BY dide_payment.type DESC;"""

    s_emp_id = ''.join('%s' % emp_id)
    s_year = ''.join('%s' % year)

    result = cursor.execute(sql.format(s_year, s_emp_id))
    return dict_fetch_all(cursor)


def rprts_from_file(queryset):
    """ Returns a list of dicts of employees and their payments
    defined in paymentreports from a set of paymentreportfiles.
    Accepts a queryset of paymentfilenames """

    cursor = connection.cursor()
    sql = """SELECT dide_paymentreport.employee_id, dide_paymentreport.year, 
            dide_paymentreport.type_id, dide_paymentcategory.id, dide_paymentcategorytitle.title, 
            dide_paymentcategory.start_date, dide_paymentcategory.end_date, 
            dide_payment.*, dide_paymentcode.calc_type, dide_paymentcode.group_name, dide_paymentcode.description   
            FROM dide_paymentfilename
            INNER JOIN dide_paymentreport
            ON dide_paymentreport.paymentfilename_id = dide_paymentfilename.id
            INNER JOIN dide_paymentcategory
            ON dide_paymentcategory.paymentreport_id = dide_paymentreport.id
            INNER JOIN dide_payment
            ON dide_payment.category_id = dide_paymentcategory.id
            INNER JOIN dide_paymentcode ON dide_payment.code_id = dide_paymentcode.id
            INNER JOIN dide_paymentcategorytitle ON dide_paymentcategory.title_id = dide_paymentcategorytitle.id
            
            WHERE dide_paymentfilename.id
            IN ({0}) AND dide_payment.type IN ('de', 'gr') 
            AND dide_paymentreport.taxed <> 0
            ORDER BY dide_payment.type DESC;"""

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
            elements.append(Paragraph(u'ΒΕΒΑΙΩΣΗ ΑΠΟΔΟΧΩΝ',
                                      heading_style['Center']))
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
            elements.append(Paragraph(u'ΒΕΒΑΙΩΣΗ ΑΠΟΔΟΧΩΝ %s' % report['year'],
                                      heading_style['Center']))
            elements.append(Paragraph(u' ', heading_style['Spacer']))

        if report['emp_type'] == 1:
            headdata = [[Paragraph(u'ΑΡ. ΜΗΤΡΩΟΥ', tbl_style['Left']),
                         Paragraph('%s' % report['registration_number'] or u'Δ/Υ',
                                   tbl_style['Left']),
                         Paragraph('ΑΦΜ', tbl_style['Left']),
                         Paragraph(u'%s' % report['vat_number'],
                                   tbl_style['Left'])],
                        [Paragraph(u'ΕΠΩΝΥΜΟ', tbl_style['Left']),
                         Paragraph('%s' % report['lastname'],
                                   tbl_style['Left']),
                         Paragraph('', tbl_style['Left']),
                         Paragraph('', tbl_style['Left'])],
                        [Paragraph(u'ΟΝΟΜΑ', tbl_style['Left']),
                         Paragraph('%s' % report['firstname'],
                                   tbl_style['Left']),
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
                         Paragraph('%s' % report['lastname'],
                                   tbl_style['Left']),
                         Paragraph('', tbl_style['Left']),
                         Paragraph('', tbl_style['Left'])],
                        [Paragraph(u'ΟΝΟΜΑ', tbl_style['Left']),
                         Paragraph('%s' % report['firstname'],
                                   tbl_style['Left']),
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
            if (i['month'] and i['month'] != 'NULL') and (i['year'] and i['year'] != 'NULL'):
                s += ' %s %s' % (months[int(i['month'] - 1)], i['year'])
            data.append([Paragraph('%s' % s, tbl_style['BoldLeft'])])
            if data: 
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

# mass pay report
def to_float(s):
    if len(s) > 0:
        try:
            return float(s)
        except ValueError:
            return None
    else:
        return None


def generate_pdf_landscape_structure(reports):
    """
    Returns the elements object for the report to be generated in PDF
    for reports in landscape format
    Accepts a schema of the report
    """

    def numtoStr(s):
        """Convert string to either int or float."""
        try:
            ret = int(s)
        except ValueError:
            ret = float(s)
        return ret

    elements = []
    for report in reports:
        data = []
        height, width = A4


        report_content = getSampleStyleSheet()
        report_content.add(ParagraphStyle(name='Center', alignment=TA_CENTER,
                                        fontName='DroidSans',
                                        fontSize=8))


        report_title = getSampleStyleSheet()

        report_title.add(ParagraphStyle(name='Center', alignment=TA_CENTER,
                                        fontName='DroidSans-Bold',
                                        fontSize=12,
                                        leading=20))
        report_title.add(ParagraphStyle(name='Left', alignment=TA_LEFT,
                                        fontName='DroidSans-Bold',
                                        fontSize=12,
                                        leading=20))

        report_sub_title = getSampleStyleSheet()
        report_sub_title.add(ParagraphStyle(name='Left', alignment=TA_LEFT,
                                            fontName='DroidSans',
                                            fontSize=10))
        report_sub_title.add(ParagraphStyle(name='Center', alignment=TA_CENTER,
                                            fontName='DroidSans',
                                            fontSize=10))

        report_section_titles = getSampleStyleSheet()
        report_section_titles.add(ParagraphStyle(name='Left', alignment=TA_LEFT,
                                        fontName='DroidSans',
                                        fontSize=8))
        report_signature = getSampleStyleSheet()
        report_small_captions = getSampleStyleSheet()
        report_small_captions.add(ParagraphStyle(name='Left', alignment=TA_LEFT,
                                        fontName='DroidSans',
                                        fontSize=6))
        report_small_captions.add(ParagraphStyle(name='Center', alignment=TA_CENTER,
                                        fontName='DroidSans',
                                        fontSize=6))

        report_normal_captions_9 = getSampleStyleSheet()
        report_normal_captions_9.add(ParagraphStyle(name='Left', alignment=TA_LEFT,
                                        fontName='DroidSans',
                                        fontSize=9))
        report_normal_captions_9.add(ParagraphStyle(name='Center', alignment=TA_CENTER,
                                        fontName='DroidSans',
                                        fontSize=9))


        report_normal_captions = getSampleStyleSheet()
        report_normal_captions.add(ParagraphStyle(name='Left', alignment=TA_LEFT,
                                        fontName='DroidSans',
                                        fontSize=11))
        report_normal_captions.add(ParagraphStyle(name='Center', alignment=TA_CENTER,
                                        fontName='DroidSans',
                                        fontSize=11))
       
        report_table_style = getSampleStyleSheet()
        signature = getSampleStyleSheet()

        heading_style = getSampleStyleSheet()
        heading_style.add(ParagraphStyle(name='Center', alignment=TA_CENTER,
                                         fontName='DroidSans-Bold',
                                         fontSize=12))
        heading_style.add(ParagraphStyle(name='Spacer', spaceBefore=5,
                                         spaceAfter=5,
                                         fontName='DroidSans-Bold',
                                         fontSize=12))
        signature.add(ParagraphStyle(name='Center', alignment=TA_CENTER,
                                     fontName='DroidSans', fontSize=12))
        signature.add(ParagraphStyle(name='Spacer', alignment=TA_CENTER,
                                     fontName='DroidSans', fontSize=12, leading=40))

        tbl_style = getSampleStyleSheet()
        tbl_style.add(ParagraphStyle(name='Left', alignment=TA_LEFT,
                                     fontName='DroidSans', fontSize=12))
        tbl_style.add(ParagraphStyle(name='Right', alignment=TA_RIGHT,
                                     fontName='DroidSans', fontSize=12))
        tbl_style.add(ParagraphStyle(name='BoldLeft', alignment=TA_LEFT,
                                     fontName='DroidSans-Bold', fontSize=12))
        tsl = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
               ('VALIGN',(0, 0), (-1, -1), 'TOP'),
               ('FONT', (0, 0), (-1, 0), 'DroidSans'),
               ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
               ('TOPPADDING', (0, 0), (-1, -1), 0),
               ('VALIGN',(-1,-1),(-1,-1),'MIDDLE')]
        
        tsh = [('ALIGN', (1, 1), (-1, -1), 'LEFT'),
               ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
               ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
               ('TOPPADDING', (0, 0), (-1, -1), 0)]

        ts = [('ALIGN', (1, 1), (-1, -1), 'LEFT'),
              ('VALIGN', (1, 1), (-1, -1), 'MIDDLE'),
              ('FONT', (0, 0), (-1, 0), 'DroidSans'),
              ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
              ('GRID', (0, 0), (-1, -1), 0.5, colors.black)]

        tsf = [('ALIGN', (1, 1), (-1, -1), 'CENTER')]

        elements.append(Table([[Paragraph('ΣΤΟΙΧΕΙΑ ΕΡΓΟΔΟΤΗ - ΦΟΡΕΑ',
                                          report_sub_title['Left'])]], style=tsl,
                       colWidths=[28 * cm]))
   
        data = []
        somedata = [[Paragraph(u'ΔΙΕΥΘΥΝΣΗ ΔΕΥΤΕΡΟΒΑΘΜΙΑΣ ΕΚΠΑΙΔΕΥΣΗΣ %s' % SETTINGS['dide_place'].upper(),
                               report_normal_captions['Left'])],
                    [Paragraph(u'Επωνυμία', report_small_captions['Left'])],
                    [Paragraph(u'ΔΗΜΟΣΙΑ ΥΠΗΡΕΣΙΑ', report_sub_title['Left'])], 
                    [Paragraph(u'Είδος επιχείρησης', report_small_captions['Left'])],
                    [Paragraph(u'%s, %s' % (SETTINGS['address'], SETTINGS['economics_contact_telephone_number']),
                               report_sub_title['Left'])],
                    [Paragraph(u'Δ/νση: Οδός - Αριθ. - Τ.Κ. - Πόλη - Αριθ. Τηλ.',
                               report_small_captions['Left'])],
                    [Paragraph(u'ΑΦΜ: %s' % SETTINGS['afm_dide'], report_title['Left'])]]
        table = Table(somedata, style=tsh,
                       colWidths=[14.5 * cm])

        headdata = [[table, [Paragraph('ΒΕΒΑΙΩΣΗ ΑΠΟΔΟΧΩΝ', report_title['Center']),
                             Paragraph(u'που καταβλήθηκαν από 01/01/%s μέχρι 31/12/%s' % (report['year'], report['year']),
                                       report_normal_captions['Center']),
                             Paragraph('(ΠΑΡΑΓΡΑΦΟΣ 3 ΑΡΘΡΟΥ 83 Ν 2238/1994)',
                                       report_small_captions['Center'])]]]
        
        table0 = Table(headdata, style=tsl,
                       colWidths=[14.5 * cm, 13.5 * cm])
        elements.append(table0)
        elements.append(Paragraph(' ', heading_style['Spacer']))
        elements.append(Table([[Paragraph('Ι. ΣΤΟΙΧΕΙΑ ΤΟΥ ΔΙΚΑΙΟΥΧΟΥ ΜΙΣΘΩΤΟΥ ή ΣΥΝΤΑΞΙΟΥΧΟΥ',
                                          report_sub_title['Left'])]], 
                              style=tsl, colWidths=[28 * cm]))

        headdata = [[Paragraph('%s' % report['lastname'], report_normal_captions['Left']),
                     Paragraph('%s' % report['firstname'], report_normal_captions['Left']),
                     Paragraph('%s' % report['fathername'], report_normal_captions['Left']),
                     Paragraph('%s' % report['vat_number'], report_normal_captions['Left'])],
                    [Paragraph('Επώνυμο', report_small_captions['Left']),
                     Paragraph('Όνομα', report_small_captions['Left']),
                     Paragraph('Όνομα Πατέρα', report_small_captions['Left']),
                     Paragraph('Αριθμ. Φορολ. Μητρώου', report_small_captions['Left'])]]
        table1 = Table(headdata, style=tsh,
                       colWidths=[5.5 * cm, 9 * cm, 8 * cm, 5.5 * cm])
        elements.append(table1)
        headdata = [[Paragraph(u'%s' % report['address'] or '-', report_normal_captions['Left']),
                     
                     Paragraph(u'%s' % report['telephone_number1']  or  '-', report_normal_captions['Left']),
                     Paragraph(u'%s' % report['tax_office'] or  '-', report_normal_captions['Left'])],
                    [Paragraph('Διεύθυνση κατοικίας: Οδός - Αριθ. - Τ.Κ. - Πόλη', report_small_captions['Left']),
                     
                     Paragraph('Αρ. Τηλ.', report_small_captions['Left']),
                     Paragraph('Αρμόδια για τη φορολογία του ΔΟΥ', report_small_captions['Left'])]]
        table1 = Table(headdata, style=tsh,
                       colWidths=[14.5 * cm, 8 * cm, 5.5 * cm])
        elements.append(table1)

        org = report.get('organization_serving', u'') or u''

        headdata = [[Paragraph(' '.join((u'%s' % (report['profession'] or  '-'), u'στο %s' % org)), report_normal_captions['Left'])],
                    [Paragraph('Είδος υπηρεσίας', report_small_captions['Left'])]]
        table1 = Table(headdata, style=tsh, colWidths=[28 * cm])
        elements.append(table1)

        elements.append(Paragraph(' ', heading_style['Spacer']))
        elements.append(Table([[Paragraph('ΙΙ. ΑΜΟΙΒΕΣ ΠΟΥ ΦΟΡΟΛΟΓΟΥΝΤΑΙ',
                                          report_sub_title['Left'])]],
                              style=tsl, colWidths=[28 * cm]))

        del data
        data = [] 
        headdata = []
        for line in report['payment_categories']:
            
            w = 28.00 / len(line)
            d = [w * cm for x in range(len(line))]
            l = []
            for i in line:
                if to_float(unicode(i)) is None:
                    l.append(Paragraph('%s' % i, report_content['Center']))
                else:
                    if float(i) == 0:
                        l.append(Paragraph('-', report_content['Center']))
                    else:
                        l.append(Paragraph('%.2f' % round(float(i), 2), report_content['Center']))
            
            headdata.append(l)

        table1 = Table(headdata, style=ts, colWidths=d)
        elements.append(table1)
 
        elements.append(Paragraph(' ', heading_style['Spacer']))
        elements.append(Table([[Paragraph('ΙIΙ. ΑΜΟΙΒΕΣ ΠΟΥ ΑΠΑΛΛΑΣΣΟΝΤΑΙ ΑΠΟ ΤΟ ΦΟΡΟ ή ΔΕ ΘΕΩΡΟΥΝΤΑΙ ΕΙΣΟΔΗΜΑ ή ΦΟΡΟΛΟΓΟΥΝΤΑΙ ΑΥΤΟΤΕΛΩΣ', 
                                          report_sub_title['Left'])]],
                              style=tsl, colWidths=[28 * cm]))


        today = datetime.date.today()
        del somedata
        somedata = []
        somedata = [[Paragraph(u'Είδος αμοιβής', report_normal_captions_9['Center']),
                     Paragraph(u'Διάταξη Νόμου που παρέχει την απαλλαγή ή επιβάλλει αυτοτελή φορολογία',
                               report_normal_captions_9['Center']),
                     Paragraph(u'Ακαθάριστο ποσό', report_normal_captions_9['Center']),
                     Paragraph(u'Σύνολο κρατήσεων που αφορούν τις αμοιβές που απαλλάσσονται',
                               report_normal_captions_9['Center']),
                     Paragraph(u'Καθαρό ποσό', report_normal_captions_9['Center']),
                     Paragraph(u'Φόρος που παρακρατήθηκε (για την αυτοτελή φορολογία)',
                               report_normal_captions_9['Center'])],

                    [Paragraph(u'-', report_normal_captions['Left']),
                     Paragraph(u'-', report_normal_captions['Left']),
                     Paragraph(u'-', report_normal_captions['Left']),
                     Paragraph(u'-', report_normal_captions['Left']),
                     Paragraph(u'-', report_normal_captions['Left']),
                     Paragraph(u'-', report_normal_captions['Left'])]

        ]

        table_1 = Table(somedata, style=ts, colWidths=[3 * cm, 4 * cm, 2 * cm, 4 * cm, 2 * cm, 3 * cm])
        del somedata
        somedata = []
        somedata = [[Paragraph(u'ΣΥΝΟΛΟ', report_normal_captions['Center']),
                     
                     Paragraph(u'-', report_normal_captions['Left']),
                     Paragraph(u'-', report_normal_captions['Left']),
                     Paragraph(u'-', report_normal_captions['Left']),
                     Paragraph(u'-', report_normal_captions['Left'])]]
        
        table_2 = Table(somedata, style=ts, colWidths=[7 * cm, 2 * cm, 4 * cm, 2 * cm, 3 * cm])
        
        data = []
        
        del headdata
        sign = os.path.join(settings.MEDIA_ROOT, "signature.png")
        im = Image(sign)
        im.drawHeight = 3.2 * cm
        im.drawWidth = 6.5 * cm
        #import pdb; pdb.set_trace()
        
        headdata = [[[table_1,table_2], 
                     [Paragraph(u'Ρόδος, %s / %s / %s' % (today.day, today.month, today.year), signature['Center']),
                      Paragraph(' ', heading_style['Spacer']),
                      im
                      #Paragraph('Ο/Η Βεβαιών/ούσα ', signature['Center']),
                      #Paragraph(' ', heading_style['Spacer']),
                      #Paragraph(' ', heading_style['Spacer']),
                      #Paragraph(' ', heading_style['Spacer'])
                      ],]]
        
        table0 = Table(headdata, style=tsl, colWidths=[18 * cm, 10 * cm])
        elements.append(table0)
        elements.append(PageBreak())
    return elements
