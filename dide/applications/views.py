# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from dideman.dide.models import (Employee, Permanent, School, Application,
                                 ApplicationSet, ApplicationType,
                                 ApplicationChoice, MoveInside)
from dideman.dide.employee.decorators import match_required
from dideman.lib.common import get_class
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect
from django.db.models.loading import get_model
from dideman import settings
from dideman.dide.util.settings import SETTINGS
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus.doctemplate import SimpleDocTemplate
from reportlab.platypus import Paragraph, Table
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import datetime
import os


def get_form(klass):
    return get_class('dideman.dide.applications.forms.%sForm' % klass)


@match_required
def print_app(request, set_id):
    base_app = Application.objects.get(
        set_id=set_id, employee_id=request.session['matched_employee_id'])
    emp = Permanent.objects.get(pk=base_app.employee_id)
    set = base_app.set
    app = get_model('dide', set.klass).objects.get(parent=base_app)
    form = get_form(set.klass)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=app_report.pdf'
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
                                     fontName='DroidSans-Bold', fontSize=12))
    heading_style.add(ParagraphStyle(name='Spacer', spaceBefore=5,
                                     spaceAfter=5, fontName='DroidSans-Bold',
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

    tsh = [('ALIGN', (1, 1), (-1, -1), 'LEFT'),
           ('BOX', (0, 0), (-1, -1), 0.25, colors.black)]
    ts = [('ALIGN', (1, 1), (-1, -1), 'LEFT'),
          ('FONT', (0, 0), (-1, 0), 'DroidSans'),
          ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
          ('GRID', (0, 0), (-1, -1), 0.5, colors.black)]
    tsf = [('ALIGN', (1, 1), (-1, -1), 'CENTER')]

    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []

    elements.append(Paragraph(u'Δ.Δ.Ε. %s' % SETTINGS['dide_place'],
                              heading_style['Center']))
    elements.append(Paragraph(u'%s' % set.title, heading_style['Center']))
    elements.append(Paragraph(u' ', heading_style['Spacer']))
    headdata = [
        [Paragraph(u'ΑΡ. ΜΗΤΡΩΟΥ', tbl_style['Left']),
         Paragraph('%s' % emp.registration_number, tbl_style['Left']),
         Paragraph('ΚΛΑΔΟΣ', tbl_style['Left']),
         Paragraph(u'%s' % emp.profession, tbl_style['Left'])],
        [Paragraph(u'ΕΠΩΝΥΜΟ', tbl_style['Left']),
         Paragraph('%s' % emp.lastname, tbl_style['Left']),
         Paragraph('', tbl_style['Left']),
         Paragraph('', tbl_style['Left'])],
        [Paragraph(u'ΟΝΟΜΑ', tbl_style['Left']),
         Paragraph('%s' % emp.firstname, tbl_style['Left']),
         Paragraph(u'ΠΕΡΙΟΧΗ ΜΕΤΑΘΕΣΗΣ', tbl_style['Left']),
         Paragraph(u'%s' % emp.transfer_area, tbl_style['Left'])],
        [Paragraph(u'Α.Α. ΑΙΤΗΣΗΣ', tbl_style['Left']),
         Paragraph('%s' % app.id, tbl_style['Left']),
         Paragraph(u' ', tbl_style['Left']),
         Paragraph(u' ', tbl_style['Left'])]]
    table1 = Table(headdata, style=tsh, colWidths=[3 * cm, 6 * cm,
                                                   4 * cm, 4 * cm])
    elements.append(table1)
    elements.append(Paragraph(u' ', heading_style['Spacer']))

    data = []
    for field in form.base_fields:
        val = getattr(app, field)
        if val:
            if val is True:
                val = u'Ναι'
            data.append(
                [Paragraph('%s' % app._meta.get_field(field).verbose_name,
                           tbl_style['Left']),
                 Paragraph('%s' % val, tbl_style['Right'])])

    table2 = Table(data, style=ts, colWidths=[10.0 * cm, 7.0 * cm])
    elements.append(table2)
    elements.append(Paragraph(u' ', heading_style['Spacer']))
    elements.append(Paragraph(u' ', heading_style['Spacer']))
    del data
    data = []
    data.append([Paragraph('Επιλογές', tbl_style['BoldLeft'])])
    for x in ApplicationChoice.objects.filter(application=app). \
            order_by('position'):
        data.append(
            [Paragraph('%s. %s' % (x.position + 1, x.choice.name),
                       tbl_style['Left'])])
    elements.append(Paragraph(u' ', heading_style['Spacer']))
    table3 = Table(data, style=ts, colWidths=[17.0 * cm])
    elements.append(table3)
    elements.append(Paragraph(u' ', heading_style['Spacer']))
    elements.append(Paragraph(u' ', heading_style['Spacer']))
    del data
    data = []
    today = datetime.date.today()
    data.append([Paragraph(u' ', signature['Center']),
                 Paragraph(u'Ρόδος, %s / %s / %s' %
                           (today.day, today.month, today.year),
                           signature['Center'])])
    data.append([Paragraph(u' ', signature['Center']),
                 Paragraph(u' ', signature['Center'])])
    data.append([Paragraph(u' ', signature['Center']),
                 Paragraph(u'Υπογραφή', signature['Center'])])
    data.append([Paragraph(u' ', signature['Center']),
                 Paragraph(u'  ', signature['Center'])])
    data.append([Paragraph(u' ', signature['Center']),
                 Paragraph(u'  ', signature['Center'])])
    data.append([Paragraph(u' ', signature['Center']),
                 Paragraph(u'  ', signature['Center'])])
    data.append([Paragraph(u' ', signature['Center']),
                 Paragraph(u'  ', signature['Center'])])
    data.append([Paragraph(u' ', signature['Center']),
                 Paragraph('%s %s' % (emp.firstname, emp.lastname),
                           signature['Center'])])
    table4 = Table(data, style=tsf, colWidths=[11.0 * cm, 6.0 * cm])
    elements.append(table4)
    doc.build(elements)
    return response


@csrf_protect
@match_required
def edit(request, set_id):
    today = datetime.date.today()
    new_form = False
    if 'logout' in request.GET:
        request.session.clear()
        return HttpResponseRedirect(
            '/employee/match/?next=/applications/edit/%s' % set_id)
    else:
        emp = Permanent.objects.get(pk=request.session['matched_employee_id'])
        try:
            set = ApplicationSet.objects.get(pk=set_id)
        except:
            return HttpResponse('invalid application')

        if not set.start_date <= today <= set.end_date:
            return render_to_response(
                'applications/error.html',
                {'error_message': 'Τέλος προθεσμίας υποβολής'})

        model = get_model('dide', set.klass)

        base_app = Application.objects.filter(employee=emp, set=set)
        if base_app:
            try:
                app = model.objects.get(employee=emp, set=set)
            except:
                return render_to_response(
                    'applications/error.html',
                    {'error_message': 'Σφάλμα τύπου αιτήσεων'})
        else:
            new_form = True

        if new_form:
            app = model(employee=emp, set=set)
            app.save()

        if 'print' in request.GET:
            return print_app(request, set_id)

        if 'emp-action' in request.POST:
            action = request.POST['emp-action']
            choices = request.POST['emp-choices'].split(';')
            form = get_form(set.klass)(request.POST)

            if form.is_valid():
                for key in form.cleaned_data:
                    if hasattr(app, key) and form.cleaned_data[key]:
                        setattr(app, key, form.cleaned_data[key])
            else:
                for n, f in form.fields.items():
                    try:
                        value = f.clean(
                            f.widget.value_from_datadict(form.data,
                                                         form.files,
                                                         form.add_prefix(n)))
                        if hasattr(app, n) and value:
                            setattr(app, n, value)
                    except:
                        pass

            if request.POST['emp-choices']:
                app_choices = []
                for i, choice in enumerate(choices):
                    app_choices.append(
                        ApplicationChoice(application=app, choice_id=choice,
                                          position=i))
                    ApplicationChoice.objects.filter(application=app).delete()
                    ApplicationChoice.objects.bulk_create(app_choices)

            if request.POST['emp-action'] == 'submit' and form.is_valid():
                app.datetime_finalised = datetime.datetime.now()
                app.save()
            else:
                app.save()
            return HttpResponseRedirect('/applications/edit/%s' % set_id)
        else:
            if new_form:
                app_form = get_form(set.klass)()
            else:
                app_form = get_form(set.klass)(app.__dict__)

            schools = app_form.choices(emp)
            choices_schools = [(x.choice_id, x.choice.name) for x in
                               ApplicationChoice.objects
                               .filter(application=app).order_by('position')]
            choices = [x.choice_id for x in
                       ApplicationChoice.objects
                       .filter(application=app).order_by('position')]
            app_len = app_form.choices_length()
            choices += [0] * (app_len - len(choices))
            options = []
            for i in range(0, app_len):
                acc = []
                for s in schools:
                    acc.append({'id': s.id, 'name': s.name,
                                'selected': s.id == choices[i]})
                options.append(acc)

            return render_to_response(
                'applications/application.html',
                RequestContext(request, {'emp': emp,
                                         'form': app_form,
                                         'schools': schools,
                                         'application': app,
                                         'options': options,
                                         'choices_schools': choices_schools}))
