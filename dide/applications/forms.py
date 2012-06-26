# -*- coding: utf-8 -*-
from django import forms
from dideman.dide.models import Permanent, MoveInsideApplication
from django.utils.translation import ugettext as _
from dideman.dide.models import HEALTH_CHOICES

HEALTH_CHOICES = ((u'', u''),) + HEALTH_CHOICES


class EmployeeMatchForm(forms.Form):
    registration_number = forms.CharField(label=u'Αρ. Μητρώου', max_length=6)
    lastname = forms.CharField(label=u'Επώνυμο', max_length=100)

    error_messages = {
        'invalid_match': ' Δεν βρέθηκε εκπαιδευτικός με αυτά τα στοιχεία',
        'no_cookies': _('Your Web browser doesn\'t appear to have cookies '
                        'enabled. Cookies are required for logging in.'),
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.employee_cache = None
        if request:
            super(EmployeeMatchForm, self).__init__(data=request.POST,
                                                    *args, **kwargs)
        else:
            super(EmployeeMatchForm, self).__init__(*args, **kwargs)

    def clean(self):
        registration_number = self.cleaned_data.get('registration_number')
        lastname = self.cleaned_data.get('lastname')
        if registration_number and lastname:
            self.employee_cache = Permanent.objects.match(
                registration_number=registration_number, lastname=lastname)
            if self.employee_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_match'])
        self.check_for_test_cookie()
        return self.cleaned_data

    def check_for_test_cookie(self):
        if self.request and not self.request.session.test_cookie_worked():
            raise forms.ValidationError(self.error_messages['no_cookies'])
        elif self.request:
            self.request.session.delete_test_cookie()

    def get_employee(self):
        return self.employee_cache


class TemporaryPositionApplicationForm(forms.Form):
    telephone_number = forms.CharField(label=u'Τηλέφωνο Επικοινωνίας')
    colocation_municipality = forms.CharField(label=u'Δήμος Συνυπηρέτησης',
                                              required=False)
    nativity_municipality = forms.CharField(label=u'Δήμος Εντοπιότητας',
                                            required=False)


class MoveInsideApplicationForm(forms.Form):
    telephone_number = forms.CharField(label=u'Τηλέφωνο Επικοινωνίας')
    colocation_municipality = forms.CharField(label=u'Δήμος Συνυπηρέτησης',
                                              required=False)
    nativity_municipality = forms.CharField(label=u'Δήμος Εντοπιότητας',
                                            required=False)
    married = forms.BooleanField(label=u'Έγγαμος',
                                 required=False)
    custody = forms.BooleanField(label=u'Επιμέλεια παιδιών',
                                 required=False)
    single_parent = forms.BooleanField(label=u'Μονογονεϊκή οικογένεια',
                                       required=False)
    children = forms.IntegerField(label=(u'Αριθμός παιδιών που είναι ανήλικα'
                                        u' ή σπουδάζουν'), required=False)
    health_self = forms.ChoiceField(label=u'Λόγοι Υγείας',
                                    choices=HEALTH_CHOICES, required=False)
    health_spouse = forms.ChoiceField(label=u'Λόγοι υγείας συζύγου',
                                      choices=HEALTH_CHOICES, required=False)
    health_children = forms.ChoiceField(label=u'Λόγοι υγείας παιδιών',
                                        choices=HEALTH_CHOICES, required=False)
    health_parents = forms.ChoiceField(label=u'Λόγοι υγείας γονέων',
                                       choices=HEALTH_CHOICES, required=False)
    parents_place = forms.CharField(label=u'Περιοχή διαμονής γονέων',
                                      max_length=150, required=False)
    health_siblings = forms.BooleanField(
        label=u'Λόγοι υγείας αδερφών (> 67% με επιμέλεια)', required=False)
    siblings_place = forms.CharField(label=u'Περιοχή διαμονής αδερφών',
                                       max_length=150, required=False)
    in_vitro = forms.BooleanField(label=u'Θεραπεία εξωσωματικής γονιμοποίησης',
                                  required=False)
    post_graduate_subject = forms.CharField(
        label=u'Περιοχή μεταπτυχιακών σπουδών (εφόσον υπάρχει)',
        required=False, max_length=150)
    special_category = forms.CharField(label=u'Ειδική κατηγορία μετάθεσης',
                                        max_length=150, required=False)
    military_spouse = forms.BooleanField(label=u'Σύζυγος στρατιωτικού',
                                         required=False)
    elected = forms.BooleanField(label=u'Αιρετός Ο.Τ.Α.',
                                 required=False)
    judge_spouse = forms.BooleanField(label=u'Σύζυγος δικαστικού',
                                      required=False)
    move_primary = forms.BooleanField(
        label=u'Επιθυμώ απόσπαση και στην Α\'Βάθμια', required=False)
    other_reasons = forms.CharField(label=u'Άλλοι λόγοι',
                                    widget=forms.Textarea,
                                    max_length=500, required=False)
