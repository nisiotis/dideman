# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from dideman.dide.models import (Permanent, NonPermanent, Employee, Placement,
                                 EmployeeLeave, Application, EmployeeResponsibility,
                                 Administrative)
from dideman.dide.employee.decorators import match_required
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect
from dideman import settings
from dideman.dide.util.settings import SETTINGS
from dideman.dide.myinfo.forms import MyInfoForm
from dideman.dide.applications.views import print_app
from django.contrib import messages
from cStringIO import StringIO
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email import Charset
from email.generator import Generator
import smtplib
import datetime
import os


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
def edit(request):
    if 'logout' in request.GET:
        request.session.clear()
        return HttpResponseRedirect('/?logout=True')
        
    elif 'print' in request.GET:
        return print_app(request, request.GET['app'])
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

        p = Placement.objects.filter(employee=emp.id).order_by('-date_from')
        l = EmployeeLeave.objects.filter(employee=emp.id).order_by('-date_from')
        r = EmployeeResponsibility.objects.filter(employee=emp.id).order_by('date_to')
        a = Application.objects.filter(employee=emp.id).exclude(datetime_finalised=None).order_by('-datetime_finalised')
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
                                                           'form': emp_form}))
