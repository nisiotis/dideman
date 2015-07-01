# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from dideman.dide.models import (Permanent, NonPermanent, Employee, Placement,
                                 EmployeeLeave, Application, EmployeeResponsibility,
                                 Administrative, NonPermanentUnemploymentMonth,
                                 NonPermanentInsuranceFile)
from dideman.dide.employee.decorators import match_required
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect
from dideman import settings
from dideman.dide.util.settings import SETTINGS
from dideman.lib.date import current_year, current_year_date_to_half
from dideman.dide.myinfo.forms import MyInfoForm
from dideman.dide.applications.views import print_app
from django.contrib import messages
from cStringIO import StringIO
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email import Charset
from email.generator import Generator
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Image, Table
from reportlab.platypus.doctemplate import NextPageTemplate, SimpleDocTemplate
from reportlab.platypus.flowables import PageBreak
from dideman.lib.date import current_year_date_from, current_year_date_to
from django.db.models.query import QuerySet

import smtplib
import datetime
import os

def protocol_number(order):
    try:
        return order.split("/")[0]
    except:
        return ''


def MailSender(name, email):
    mFrom = [u'ΔΔΕ %s' % SETTINGS['dide_place'], SETTINGS['email_dide']]
    mRecipient = [name, email]

    mSubject = u'Ενημέρωση στοιχείων του φακέλου σας.'
    mHtml = u"""<p>Πραγματοποιήθηκε ενημέρωση στοιχείων του φακέλου σας, στο """
    mHtml += u"""σύστημα προσωπικού της ΔΔΕ.</p>"""
    mHtml += u"""<p><a href="http://its.dide.dod.sch.gr">Συνδεθείτε στο """
    mHtml += u"""σύστημα για να δείτε τις αλλαγές</a></p>"""
    mHtml += u"""<p>Απο την ΔΔΕ %s</p>""" % SETTINGS['dide_place']
    Charset.add_charset('utf-8', Charset.QP, Charset.QP, 'utf-8')
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "%s" % Header(mSubject, 'utf-8')
    msg['From'] = "\"%s\" <%s>" % (Header(mFrom[0], 'utf-8'), mFrom[1])
    msg['To'] = "\"%s\" <%s>" % (Header(mRecipient[0], 'utf-8'), mRecipient[1])
    htmlpart = MIMEText(mHtml, 'html', 'UTF-8')
    msg.attach(htmlpart)
    str_io = StringIO()
    g = Generator(str_io, False)
    g.flatten(msg)
    s = smtplib.SMTP(settings.EMAIL_HOST, 587)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    s.sendmail(SETTINGS['email_dide'], email, str_io.getvalue())


@csrf_protect
@match_required
def print_emp_report(request, fid):
    emp = NonPermanent.objects.select_related().get(parent_id=request.session['matched_employee_id'])
    reports = NonPermanentUnemploymentMonth.objects.select_related().filter(employee_id=request.session['matched_employee_id'],insurance_file=fid)
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=exp_report.pdf'
    registerFont(TTFont('DroidSans', os.path.join(settings.MEDIA_ROOT,
                                                  'DroidSans.ttf')))
    registerFont(TTFont('DroidSans-Bold', os.path.join(settings.MEDIA_ROOT,
                                                       'DroidSans-Bold.ttf')))


    doc = SimpleDocTemplate(response, pagesize=A4)
    doc.topMargin = 1.0 * cm
    doc.leftMargin = 1.5 * cm
    doc.rightMargin = 1.5 * cm

    elements = []
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
    tbl_style.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY,
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

    for r in reports:
        data = []
        elements.append(Paragraph(u'ΒΕΒΑΙΩΣΗ ΕΡΓΟΔΟΤΗ', heading_style['Center']))
        elements.append(Paragraph(u' ', heading_style['Spacer']))

        data.append([Paragraph(u'ΕΠΩΝΥΜΙΑ ΕΡΓΟΔΟΤΗ ', tbl_style['Left']) , Paragraph(u'Διεύθυνση ΔΕ %s' % SETTINGS['dide_place'], tbl_style['Left'])])

        data.append([Paragraph(u'ΑΡΙΘΜΟΣ ΜΗΤΡΩΟΥ: %s' %  SETTINGS['ika_code_dde'], tbl_style['Left']), Paragraph(u'Α.Φ.Μ. ΕΡΓΟΔΟΤΗ: %s' % SETTINGS['afm_dide'], tbl_style['Left'])])

        data.append([Paragraph(u'ΑΡΜΟΔΙΟ ΥΠΟΚΑΤΑΣΤΗΜΑ ΙΚΑ ΕΛΕΓΧΟΥ ', tbl_style['Left']), Paragraph(u' ', tbl_style['Left'])])
        data.append([Paragraph(u'ΚΩΔΙΚΟΣ - ΟΝΟΜΑΣΙΑ ', tbl_style['Left']), Paragraph(u'%s' % SETTINGS['ika_code'] , tbl_style['Left'])])

        
        table = Table(data, style=tsf, colWidths=[7.0 * cm, 11.0 * cm])
        elements.append(table)
        elements.append(Paragraph(u' ', heading_style['Spacer']))

        data = []


        elements.append(Paragraph(u'Βεβαιώνουμε ότι:' , tbl_style['Left']))
        elements.append(Paragraph(u'Ο/Η ασφαλισμένος με τα κάτωθι ασφαλιστικά στοιχεία απασχολήθηκε στην επιχείρησή μας κατά τις μισθολογικές περιόδους που ακολουθούν:' , tbl_style['Left']))

        elements.append(Paragraph(u' ', heading_style['Spacer']))

        elements.append(Paragraph(u'ΣΤΟΙΧΕΙΑ ΥΠΑΛΛΗΛΟΥ', tbl_style['BoldLeft']))

        data.append([Paragraph(u'ΑΡ. ΠΑΡΑΡΤ. / Κ.Α.Δ. ', tbl_style['Left']), Paragraph(u'%s' % SETTINGS['subject_kad'], tbl_style['Right'])])
        data.append([Paragraph(u'ΑΜΑ: ', tbl_style['Left']), Paragraph(u'%s' % emp.ama, tbl_style['Right'])])
        data.append([Paragraph(u'Α.Μ.Κ.Α.: ', tbl_style['Left']), Paragraph(u'%s' % emp.social_security_registration_number, tbl_style['Right'])])

        data.append([Paragraph(u'ΕΠΩΝΥΜΟ: ', tbl_style['Left']), Paragraph(u'%s' % emp.lastname, tbl_style['Right'])])
        data.append([Paragraph(u'ΟΝΟΜΑ: ', tbl_style['Left']), Paragraph(u'%s' % emp.firstname, tbl_style['Right'])])
        data.append([Paragraph(u'ΟΝΟΜΑ ΠΑΤΡΟΣ: ', tbl_style['Left']), Paragraph(u'%s' % emp.fathername, tbl_style['Right'])])
        data.append([Paragraph(u'ΟΝΟΜΑ ΜΗΤΡΟΣ: ', tbl_style['Left']), Paragraph(u'%s' % emp.mothername, tbl_style['Right'])])
        data.append([Paragraph(u'ΗΜΕΡΟΜΗΝΙΑ ΓΝΝΕΣΕΩΣ: ', tbl_style['Left']), Paragraph(u'%s / %s / %s' % (emp.birth_date.day, emp.birth_date.month, emp.birth_date.year), tbl_style['Right'])])
        data.append([Paragraph(u'Α.Φ.Μ.: ', tbl_style['Left']), Paragraph(u'%s' % emp.vat_number, tbl_style['Right'])])
        data.append([Paragraph(u'ΚΩΔΙΚΟΣ ΕΙΔΙΚΟΤΗΤΑΣ: ', tbl_style['Left']), Paragraph(u'%s' % emp.type(), tbl_style['Right'])])
        if emp.other_social_security:
            ec = emp.other_social_security.code
        else:
            ec = '101'
            
        data.append([Paragraph(u'ΠΑΚΕΤΟ ΚΑΛΥΨΗΣ: ', tbl_style['Left']), Paragraph(u'%s' % ec, tbl_style['Right'])])
        data.append([Paragraph(u'ΜΙΣΘΟΛΟΓΙΚΗ ΠΕΡΙΟΔΟΣ: ', tbl_style['Left']), Paragraph(u'%s / %s' % (r.month, r.year), tbl_style['Right'])])
        data.append([Paragraph(u'ΑΠΟ ΗΜΕΡΟΜΗΝΙΑ ΑΠΑΣΧΟΛΙΣΗΣ: ', tbl_style['Left']), Paragraph(u'%s' % r.insured_from, tbl_style['Right'])])
        data.append([Paragraph(u'ΕΩΣ ΗΜΕΡΟΜΗΝΙΑ ΑΠΑΣΧΟΛΗΣΗΣ: ', tbl_style['Left']), Paragraph(u'%s' % r.insured_to, tbl_style['Right'])])
        data.append([Paragraph(u'ΤΥΠΟΣ ΑΠΟΔΟΧΩΝ: ', tbl_style['Left']), Paragraph(u'%s' % r.pay_type, tbl_style['Right'])])
        data.append([Paragraph(u'ΗΜΕΡΕΣ ΑΣΦΑΛΙΣΗΣ: ', tbl_style['Left']), Paragraph(u'%s' % r.days_insured, tbl_style['Right'])])
        lpam = r.total_earned.split('.')[0]
        rpam = r.total_earned.split('.')[1]
        if len(rpam) == 1:
            rpam = rpam + '0'

        data.append([Paragraph(u'ΑΠΟΔΟΧΕΣ: ', tbl_style['Left']), Paragraph(u'%s.%s' % (lpam, rpam), tbl_style['Right'])])
        data.append([Paragraph(u'ΕΙΣΦΟΡΕΣ ΑΣΦΑΛΙΣΜΕΝΟΥ: ', tbl_style['Left']), Paragraph(u'%s' % r.employee_contributions, tbl_style['Right'])])
        data.append([Paragraph(u'ΕΙΣΦΟΡΕΣ ΕΡΓΟΔΟΤΗ: ', tbl_style['Left']), Paragraph(u'%s' % r.employer_contributions, tbl_style['Right'])])
        data.append([Paragraph(u'ΣΥΝΟΛΙΚΕΣ ΕΙΣΦΟΡΕΣ: ', tbl_style['Left']), Paragraph(u'%s' % r.total_contributions, tbl_style['Right'])])
        data.append([Paragraph(u'ΚΑΤΑΒΛ. ΕΙΣΦΟΡΕΣ: ', tbl_style['Left']), Paragraph(u'%s' % r.total_contributions, tbl_style['Right'])])


        table = Table(data, style=tsf, colWidths=[12.0 * cm, 6.0 * cm])
        elements.append(table)

        data = []

        elements.append(Paragraph(u'Η παραπάνω βεβαίωση χορηγείται για απόδειξη της ασφάλισης στις πεοαναφερθείσες περιόδους.', tbl_style['Left']))
        elements.append(Paragraph(u'ΠΑΡΑΤΗΡΗΣΗ', tbl_style['Left']))

        elements.append(Paragraph(u'Τα αναγραφόμενα στην παρούσα Βεβαίωση ασφαλιστικά στοιχεία λαμβάνονται υπόψη μέχρι την επεξεργασία της Α.Π.Δ. των συγκεκριμένων μισθολογικών περιόδων και την υποβολή και έκδοση από το ΙΚΑ του αντίστοιχου Αποσπάσματος Ατομικού Λογαριασμού Ασφάλισης.', tbl_style['Justify']))
        
        
        today = datetime.date.today()
        
        data.append([Paragraph(u' ', signature['Center']) ,Paragraph(u'Ρόδος, %s / %s / %s' %
                               (today.day, today.month, today.year), signature['Center'])])
        
        table = Table(data, style=tsf, colWidths=[10.0 * cm, 7.0 * cm])
        elements.append(table)
        elements.append(Paragraph(u' ', heading_style['Spacer']))

        data = []

        sign = os.path.join(settings.MEDIA_ROOT, "signature.png")
        im = Image(sign)
        im.drawHeight = 3.2 * cm
        im.drawWidth = 6.5 * cm
        
        data.append([Paragraph(u' ', signature['Center']) ,im])
        
        table = Table(data, style=tsf, colWidths=[10.0 * cm, 7.0 * cm])
        elements.append(table)
        elements.append(PageBreak())
        
    doc.build(elements)
    return response



@csrf_protect
@match_required
def print_exp_report(request):
    emptype = NonPermanent.objects.select_related().get(parent_id=request.session['matched_employee_id'])
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=exp_report.pdf'
    registerFont(TTFont('DroidSans', os.path.join(settings.MEDIA_ROOT,
                                                  'DroidSans.ttf')))
    registerFont(TTFont('DroidSans-Bold', os.path.join(settings.MEDIA_ROOT,
                                                       'DroidSans-Bold.ttf')))


    doc = SimpleDocTemplate(response, pagesize=A4)
    doc.topMargin = 1.5 * cm
    doc.leftMargin = 1.5 * cm
    doc.rightMargin = 1.5 * cm

    elements = []
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
    tbl_style.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY,
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
    today = datetime.date.today()
    data.append([Paragraph(u'Ρόδος, %s / %s / %s' %
                               (today.day, today.month, today.year), tbl_style['Left'])])
    data.append([Paragraph(' ', heading_style['Spacer'])])
    data.append([Paragraph(' ', heading_style['Spacer'])])

    data.append([Paragraph(u'Αρ. Προτ.: %s' % protocol_number(emptype.order().order_end_manager), tbl_style['Left'])])
    tableh = Table(data, style=tsl, colWidths=[6.0 * cm])
    data = []
    data.append([im, '', tableh])
    data.append([Paragraph(u'ΕΛΛΗΝΙΚΗ ΔΗΜΟΚΡΑΤΙΑ', head_logo['Center']), '', ''])
    data.append([Paragraph(u'ΥΠΟΥΡΓΕΙΟ ΠΟΛΙΤΙΣΜΟΥ, ΠΑΙΔΕΙΑΣ,',
                           head_logo['Center']), '', ''])
    data.append([Paragraph(u'ΚΑΙ ΘΡΗΣΚΕΥΜΑΤΩΝ',
                           head_logo['Center']), '', ''])
    data.append([Paragraph(u'ΠΕΡΙΦΕΡΙΑΚΗ ΔΙΕΥΘΥΝΣΗ ΠΡΩΤΟΒΑΘΜΙΑΣ',
                           head_logo['Center']), '', ''])
    data.append([Paragraph(u'ΚΑΙ ΔΕΥΤΕΡΟΒΑΘΜΙΑΣ ΕΚΠΑΙΔΕΥΣΗΣ ΝΟΤΙΟΥ ΑΙΓΑΙΟΥ',
                           head_logo['Center']), '', ''])
    data.append([Paragraph(u'ΔΙΕΥΘΥΝΣΗ ΔΕΥΤΕΡΟΒΑΘΜΙΑΣ ΕΚΠΑΙΔΕΥΣΗΣ ΔΩΔΕΚΑΝΗΣΟΥ',
                           head_logo['Center']), '', Paragraph(u'ΠΡΟΣ: %s %s' % (emptype.lastname, emptype.firstname),
                           tbl_style['BoldLeft'])])
    table0 = Table(data, style=tsl, colWidths=[8.0 * cm, 3.0 * cm, 8.0 * cm])
    elements.append(table0)
    elements.append(Paragraph(u' ', heading_style['Spacer']))
    elements.append(Paragraph(u'Ταχ. Διεύθυνση: %s' % SETTINGS['address'], tbl_style['Left']))
    elements.append(Paragraph(u'Πληροφορίες: %s' % SETTINGS['substitutes_contact_person'], tbl_style['Left']))
    elements.append(Paragraph(u'Τηλέφωνο: %s' % SETTINGS['substitutes_contact_telephone_number'], tbl_style['Left']))
    elements.append(Paragraph(u'Email: %s' % SETTINGS['email_substitutes'], tbl_style['Left']))
    elements.append(Paragraph(u'Fax: %s' % SETTINGS['fax_number'], tbl_style['Left']))
    elements.append(Paragraph(u' ', heading_style['Spacer']))
    elements.append(Paragraph(u'ΘΕΜΑ: Αυτοδίκαιη Απόλυση', tbl_style['BoldLeft']))
    elements.append(Paragraph(u' ', heading_style['Spacer']))
    elements.append(Paragraph(u'Σας ανακοινώνουμε ότι με την ταυτάριθμη απόφαση του Διευθυντή Δευτεροβάθμιας Εκπαίδευσης Δωδεκανήσου απολύεστε αυτοδίκαια από τη θέση του/της προσωρινού/ης αναπληρωτή/τριας καθηγητή/τριας την %s/%s/%s.' % (emptype.current_placement().date_to.day, emptype.current_placement().date_to.month, emptype.current_placement().date_to.year), tbl_style['Justify']))
    elements.append(Paragraph(u' ', heading_style['Spacer']))
    elements.append(Paragraph(u' ', heading_style['Spacer']))

    elements.append(Paragraph(u'ΘΕΜΑ: Βεβαίωση Προϋπηρεσίας', tbl_style['BoldLeft']))
    elements.append(Paragraph(u' ', heading_style['Spacer']))
    elements.append(Paragraph(u'Σας ανακοινώνουμε ότι, όπως προκύπτει από το αρχείο που τηρείται στην υπηρεσία μας, ο/η %s %s με όνομα πατρός %s του κλάδου %s %s τοποθετήθηκε στο %s ως %s και υπηρέτησε από %s/%s/%s έως %s/%s/%s.' % (emptype.lastname, emptype.firstname, emptype.fathername, emptype.profession, emptype.profession.description, emptype.current_placement(), emptype.type(), emptype.current_placement().date_from.day,emptype.current_placement().date_from.month,emptype.current_placement().date_from.year, emptype.current_placement().date_to.day, emptype.current_placement().date_to.month,emptype.current_placement().date_to.year), tbl_style['Justify']))

    elements.append(Paragraph(u' ', heading_style['Spacer']))

    elements.append(Paragraph(u'Απόφαση διορισμού %s: %s %s/%s/%s' % (SETTINGS['ministry_title'], emptype.order().order, emptype.order().date.day, emptype.order().date.month, emptype.order().date.year), tbl_style['Left']))

    elements.append(Paragraph(u' ', heading_style['Spacer']))

    elements.append(Paragraph(u'Απόφαση τοποθέτησης Διευθυντή Δ.Ε. Δωδεκανήσου: %s' % emptype.order().order_start_manager, tbl_style['Left']))

    elements.append(Paragraph(u' ', heading_style['Spacer']))
    
    elements.append(Paragraph(u'Απόφαση απόλυσης Διευθυντή Δ.Ε. Δωδεκανήσου: %s' % emptype.order().order_end_manager, tbl_style['Left']))

    elements.append(Paragraph(u' ', heading_style['Spacer']))

    elements.append(Paragraph(u'Χρόνος υπηρεσίας: %s' % emptype.experience(), tbl_style['Left']))

    elements.append(Paragraph(u' ', heading_style['Spacer']))

    elements.append(Paragraph(u'Η βεβαίωση αυτή χορηγείται ύστερα από αίτηση του/της ενδιαφερόμενου/ης προκειμένου να τη χρησιμοποιήσει ως δικαιολογητικό για την αναγνώριση της προϋπηρεσίας του/της.', tbl_style['Justify']))

    elements.append(Paragraph(u' ', heading_style['Spacer']))
    elements.append(Paragraph(u' ', heading_style['Spacer']))

    data = []
    sign = os.path.join(settings.MEDIA_ROOT, "signature.png")
    im = Image(sign)
    im.drawHeight = 3.2 * cm
    im.drawWidth = 6.5 * cm

    data.append([Paragraph(u' ', signature['Center']) ,im])

    table6 = Table(data, style=tsf, colWidths=[10.0 * cm, 7.0 * cm])
    elements.append(table6)

    elements.append(Paragraph(u' ', heading_style['Spacer']))
    elements.append(Paragraph(u' ', heading_style['Spacer']))
    elements.append(Paragraph(u'ΚΟΙΝΟΠΟΙΗΣΗ', tbl_style['BoldLeft']))
    elements.append(Paragraph(u'1. %s' % emptype.current_placement(), tbl_style['Left']))
    elements.append(Paragraph(u'2. Α.Φ.', tbl_style['Left']))
    if emptype.order().order_type == 3:

        logo = os.path.join(settings.MEDIA_ROOT, "espa.png")
        im = Image(logo)
        im.drawHeight = 3.2 * cm
        im.drawWidth = 16.5 * cm
        elements.append(im)


    elements.append(PageBreak())

    doc.build(elements)
    return response


@csrf_protect
@match_required
def edit(request):
    exp = False
    if 'logout' in request.GET:
        request.session.clear()
        return HttpResponseRedirect('/?logout=True')
        
    elif 'print' in request.GET:
        return print_app(request, request.GET['app'])
    elif 'print_exp' in request.GET:
        return print_exp_report(request)
    elif 'print_emp' in request.GET:
        return print_emp_report(request, request.GET['f'])

    else:
        emp = Employee.objects.get(id=request.session['matched_employee_id'])
        try:
            emptype = Permanent.objects.get(parent_id=emp.id)
        except Permanent.DoesNotExist:
            try:
                emptype = NonPermanent.objects.get(parent_id=emp.id)
                if emptype.order().order_end_manager != u'' and emptype.order().show_online_order == True:
                    f = set(f.insurance_file for f in NonPermanentUnemploymentMonth.objects.filter(employee=emp.id))
                    exp = True

                
            except NonPermanent.DoesNotExist:
                try:
                    emptype = Administrative.objects.get(parent_id=emp.id)
                except Administrative.DoesNotExist:
                    emptype = 0
        except:
            raise

        p = Placement.objects.filter(employee=emp.id).order_by('-date_from')
        l = EmployeeLeave.objects.filter(employee=emp.id).order_by('-date_from')
        r = EmployeeResponsibility.objects.filter(employee=emp.id).order_by('date_to')
        a = Application.objects.filter(employee=emp.id).exclude(datetime_finalised=None).order_by('-datetime_finalised')
         

        import pdb; pdb.set_trace()

        emp_form = MyInfoForm(emp.__dict__)
        if request.POST:
            emp_form = MyInfoForm(request.POST)
            if emp_form.is_valid():
                for key in emp_form.cleaned_data:
                    if hasattr(emp, key):
                        setattr(emp, key, emp_form.cleaned_data[key])
                emp.save()
                messages.info(request, "Τα στοιχεία σας ενημερώθηκαν.")
                if emp.email:
                    MailSender(u' '.join([emp.firstname, emp.lastname]),
                               emp.email)
        return render_to_response('myinfo/edit.html',
                                  RequestContext(request, {'emp': emptype,
                                                           'messages': messages,
                                                           'leaves': l,
                                                           'positions': p,
                                                           'responsibilities': r,
                                                           'applications': a,
                                                           'form': emp_form,
                                                           'service': exp,
                                                           'insurance': f
                                                       }
                                        ))
