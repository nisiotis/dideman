# -*- coding: utf-8 -*-
from django import forms
from dideman.dide.models import Permanent, Employee
from dideman.dide.util.common import without_accented
from django.utils.translation import ugettext as _
from django.db.models import Q


class EmployeeMatchForm(forms.Form):
    identification_number = forms.CharField(label=u'Αναγνωριστικό',
                                               max_length=9)
    lastname = forms.CharField(label=u'Επώνυμο', max_length=100)
    iban_4 = forms.CharField(label=u'IBAN (4 τελευταία ψηφία',
                             widget=forms.PasswordInput,
                             min_length=4, max_length=4)

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
        identification_number = self.cleaned_data.get('identification_number')
        lastname = self.cleaned_data.get('lastname')
        iban_4 = self.cleaned_data.get('iban_4')
        if identification_number and lastname:
            lastname = without_accented(lastname.upper())
            self.employee_cache = Permanent.objects.match(
                identification_number, identification_number,
                lastname, iban_4) or \
                Employee.objects.match(identification_number, lastname, iban_4)
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
