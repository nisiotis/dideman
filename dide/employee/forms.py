# -*- coding: utf-8 -*-
from django import forms
from dideman.dide.models import Permanent
from django.utils.translation import ugettext as _


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
