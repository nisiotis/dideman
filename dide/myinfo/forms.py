# -*- coding: utf-8 -*-
from django import forms
from dideman.dide.models import Permanent
from django.utils.translation import ugettext as _
from dideman.dide.myinfo.myselect import MySelectDateWidget


SEX_TYPES = ((u'', u'---------'),
             (u'Άνδρας', u'Άνδρας'),
             (u'Γυναίκα', u'Γυναίκα'))

class MyInfoForm(forms.Form):
    sex = forms.ChoiceField(label=u'Φύλο', required=False, choices=SEX_TYPES)
    email = forms.EmailField(label=u'Email',
                             required=False, widget=forms.TextInput(attrs={'size':30}))
    telephone_number1 = forms.CharField(label=u'Σταθερό Τηλέφωνο',
                                        required=False)
    telephone_number2 = forms.CharField(label=u'Κινητό Τηλέφωνο',
                                        required=False)
    mothername = forms.CharField(label=u'Όνομα Μητέρας', required=False,
                                    widget=forms.TextInput(attrs={'size':20}))
    social_security_registration_number = forms.CharField(label=u'Α.Μ.Κ.Α.',
                                                          required=False)
    ama = forms.CharField(label=u'ΑΜΑ ΙΚΑ ΕΤΑΜ', required=False)
    address = forms.CharField(label=u'Διεύθυνση Κατοικίας - Οδός', max_length=200, required=False,
                              widget=forms.TextInput(attrs={'size':60}))
    address_postcode = forms.CharField(label=u'Ταχ. Κωδικός', max_length=6, required=False,
                              widget=forms.TextInput(attrs={'size':6}))
    address_city = forms.CharField(label=u'Πόλη', max_length=30, required=False,
                              widget=forms.TextInput(attrs={'size':30}))

    tax_office = forms.CharField(label=u'Δ.Ο.Υ.', required=False)
    birth_date = forms.DateField(label=u'Ημερομηνία Γέννησης', required=False, widget=MySelectDateWidget(years=range(1930, 2030)))
