# -*- coding: utf-8 -*-
from dideman.dide.models import Application, Permanent
from django.db.models.loading import get_model


class ApplicationPrint(object):

    class Positioner(object):
        ll = 50
        ul = 750
        vstep = 20
        col_diff = 300

        def __init__(self):
            self.hpos = self.ll
            self.vpos = self.ul

        def next_pos(self):
            r = (self.hpos, self.vpos)
            self.vpos -= self.vstep
            if self.vpos < 50:
                self.vpos = self.ul - self.vstep * 7
                self.hpos = self.ll + self.col_diff
            return r

    def __init__(self, klass, form, len_fn, schools):
            self.short_description = u'Δημιουργία Αποδεικτικού'
            self.klass = klass
            self.form = form
            self.len_fn = len_fn
            self.schools = schools

    def __call__(self, modeladmin, request, queryset, *args, **kwargs):
        # base_app = Application.objects.get(
        #     request.GET['set_id'],
        #     employee_id=request.session['matched_employee_id'])
        # emp = Permanent.objects.get(pk=base_app.employee_id)
        # set = base_app.set
        # app = get_model('dide', set.klass).objects.get(parent=base_app)
        response = HttpResponse(mimetype='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=app_report.pdf'
        registerFont(TTFont('DroidSans', os.path.join(settings.MEDIA_ROOT,
                                                      'DroidSans.ttf')))
        c = canvas.Canvas(response)
        c.setFont('DroidSans', 14)
        posn = Positioner()
        c.drawString(*posn.next_pos(),
                      text=u'Δ.Δ.Ε. Δωδεκανήσου - %s' % set.title)
        posn.next_pos()
        c.drawString(*posn.next_pos(), text='%s %s - %s'
                      % (emp.lastname, emp.firstname, emp.registration_number))
        posn.next_pos()
        c.drawString(*posn.next_pos(), text=u'Α.Α. Αίτησης : %s' % app.id)
        for field in form.base_fields:
            val = getattr(app, field)
            if val:
                if val == True:
                    val = u'Ναι'
                c.drawString(*posn.next_pos(),
                              text='%s: %s' % (
                        app._meta.get_field(field).verbose_name, val))

        posn.next_pos()
        c.drawString(*posn.next_pos(), text=u'Επιλογές')
        for x in ApplicationChoice.objects.filter(
            application=app).order_by('position'):
            c.drawString(*posn.next_pos(),
                          text='%s. %s' % (x.position + 1, x.choice.name))

        c.drawString(400, 150, text=u'Υπογραφή')
        c.showPage()
        c.save()
        return response


class MoveInsideApplicationPrint(ApplicationPrint):
    def __init__(self):
        pass
