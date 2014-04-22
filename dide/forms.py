# -*- coding: utf-8 -*-
from django import forms
from django.forms.models import ModelForm
from dideman.dide.models import SubstitutePlacement, NonPermanent, PlacementType, School, SchoolCommission
from dideman.lib.date import current_year_date_to_half


class SubstitutePlacementForm(ModelForm):

    class Meta:
        model = SubstitutePlacement

    pltype = PlacementType.objects.get(pk=3)

    def _post_clean(self):
        super(SubstitutePlacementForm, self)._post_clean()
        if not self.instance.date_to:
            self.instance.date_to = current_year_date_to_half()
        self.instance.type = SubstitutePlacementForm.pltype


class PaymentFileNameMassForm(forms.Form):
    is_bound = 0
    
    xml_file =  forms.FileField(label=u'Αρχείο ZIP', required=True)
    description = forms.CharField(label=u'Εμφανιζόμενο όνομα',
                                  required=True)
    taxed = forms.BooleanField(label=u'Συμπεριλαμβάνεται την φορολογία',
                               initial=True, required=False)


class SchoolCommissionForm(forms.ModelForm):

    class Meta:
        model = SchoolCommission

    schools = forms.ModelMultipleChoiceField(label=u'Σχολεία', queryset=School.objects.all(),
                                             widget=forms.SelectMultiple(attrs={'size':'40'}))

    def __init__(self, *args, **kwargs):
        super(SchoolCommissionForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields['schools'].initial = self.instance.school_set.all()

    def save(self, *args, **kwargs):
        # FIXME: 'commit' argument is not handled
        # TODO: Wrap reassignments into transaction
        # NOTE: Previously assigned Foos are silently reset
        instance = super(SchoolCommissionForm, self).save(commit=False)
        self.fields['schools'].initial.update(commission=None)
        self.cleaned_data['schools'].update(commission=instance)
        return instance
