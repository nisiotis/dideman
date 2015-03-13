# -*- coding: utf-8 -*-
from django import forms
from dideman.dide.models import Permanent
from django.utils.translation import ugettext as _
from django.contrib.admin.widgets import AdminDateWidget

SEX_TYPES = ((u'', u'---------'),
             (u'Άνδρας', u'Άνδρας'),
             (u'Γυναίκα', u'Γυναίκα'))

class MyInfoForm(forms.Form):
    sex = forms.ChoiceField(label=u'Φύλο', required=False, choices=SEX_TYPES)
    email = forms.EmailField(label=u'Email',
                             required=False)
    telephone_number1 = forms.CharField(label=u'Σταθερό Τηλέφωνο',
                                        required=False)
    telephone_number2 = forms.CharField(label=u'Κινητό Τηλέφωνο',
                                        required=False)
    mothername = forms.CharField(label=u'Όνομα Μητέρας', required=False)
    social_security_registration_number = forms.CharField(label=u'Α.Μ.Κ.Α.',
                                                          required=False)
    ama = forms.CharField(label=u'ΑΜΑ ΙΚΑ ΕΤΑΜ', required=False)
    address = forms.CharField(label=u'Διεύθυνση Κατοικίας',
                              widget=forms.Textarea(attrs={'rows':3, 'cols':35}), required=False)
    tax_office = forms.CharField(label=u'Δ.Ο.Υ.', required=False)
    birth_date = forms.DateField(label=u'Ημερομηνία Γέννησης', required=False)
