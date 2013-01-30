# -*- coding: utf-8 -*-
from django import forms
from django.forms.models import ModelForm
from dideman.dide.models import SubstitutePlacement, NonPermanent, PlacementType
from dideman.lib.date import current_year_date_to


class SubstitutePlacementForm(ModelForm):

    class Meta:
        model = SubstitutePlacement

    pltype = PlacementType.objects.get(pk=3)

    def _post_clean(self):
        super(SubstitutePlacementForm, self)._post_clean()
        self.instance.date_to = current_year_date_to()
        self.instance.type = SubstitutePlacementForm.pltype


class PaymentFileNameMassForm(forms.Form):
    is_bound = 0
    
    xml_file =  forms.FileField(label=u'Αρχείο ZIP', required=True)
    description = forms.CharField(label=u'Εμφανιζόμενο όνομα',
                                        required=True)
