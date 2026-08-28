# -*- coding: utf-8 -*-
from django import forms
from dideman.dide.models import Permanent
from django.utils.translation import gettext as _
from dideman.dide.myinfo.myselect import MySelectDateWidget


SEX_TYPES = (('', '---------'),
             ('Άνδρας', 'Άνδρας'),
             ('Γυναίκα', 'Γυναίκα'))

class MyInfoForm(forms.Form):
    sex = forms.ChoiceField(label='Φύλο', required=False, choices=SEX_TYPES)
    email = forms.EmailField(label='Email',
                             required=False, widget=forms.TextInput(attrs={'size':30}))
    telephone_number1 = forms.CharField(label='Σταθερό Τηλέφωνο',
                                        required=False)
    telephone_number2 = forms.CharField(label='Κινητό Τηλέφωνο',
                                        required=False)
    mothername = forms.CharField(label='Όνομα Μητέρας', required=False,
                                    widget=forms.TextInput(attrs={'size':20}))
    social_security_registration_number = forms.CharField(label='Α.Μ.Κ.Α.',
                                                          required=False)
    ama = forms.CharField(label='ΑΜΑ ΙΚΑ ΕΤΑΜ', required=False)
    address = forms.CharField(label='Διεύθυνση Κατοικίας - Οδός', max_length=200, required=False,
                              widget=forms.TextInput(attrs={'size':60}))
    address_postcode = forms.CharField(label='Ταχ. Κωδικός', max_length=6, required=False,
                              widget=forms.TextInput(attrs={'size':6}))
    address_city = forms.CharField(label='Πόλη', max_length=30, required=False,
                              widget=forms.TextInput(attrs={'size':30}))

    tax_office = forms.CharField(label='Δ.Ο.Υ.', required=False)
    birth_date = forms.DateField(label='Ημερομηνία Γέννησης', required=False, widget=MySelectDateWidget(years=list(range(1930, 2030))))
