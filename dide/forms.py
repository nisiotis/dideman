# -*- coding: utf-8 -*-
from django import forms
from django.utils.text import force_unicode
from django.utils.html import mark_safe
from django.forms.widgets import flatatt

from django.forms.models import ModelForm
from django.forms import Widget
from django.contrib.admin.widgets import AdminDateWidget 
from dideman.dide.models import OrderedSubstitution, SubstitutePlacement, NonPermanent, PlacementType, School, SchoolCommission
from dideman.lib.date import current_year_date_to_half


class SubstituteInput(forms.HiddenInput):

    def render(self, name, value, attrs=None):
        try:
            textname=NonPermanent.objects.get(parent_id=value).__unicode__()
            nid=value
            value=textname
        except:
            value = ''
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_unicode(self._format_value(nid))
        output = []
        output.append(u'<input%s />' % flatatt(final_attrs))
        output.append(u'<input readonly="true" type="text" id="display_%s" value="%s" size="40" />&nbsp;' % (self._format_value(final_attrs['id']), force_unicode(self._format_value(value))))
        output.append(u'<a href="#" id="link_%s" onclick="this.href=\'/admin/dide/nonpermanent/list/\'+\'?id=\'+django.jQuery(this).attr(\'id\');return focusOrOpen(this, \'Αναπληρωτές\',{\'width\': 500, \'height\': 600});">Επιλογή</a>&nbsp;' % self._format_value(final_attrs['id']) )
        output.append(u'<a href="/admin/dide/nonpermanent/add/" class="add-another" id="add_%s" onclick="return showAddAnotherPopup(this);"> <img src="/static/admin/img/icon_addlink.gif" width="10" height="10" alt="Προσθέστε κι άλλο"></a>' % self._format_value(final_attrs['id']))
        return mark_safe(''.join(output))   


class OrderedSubstitutionInlineForm(ModelForm):

    class Meta:
        model = OrderedSubstitution
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(OrderedSubstitutionInlineForm, self).__init__(*args, **kwargs)
        self.fields['substitute'].widget = SubstituteInput()



class SubstitutePlacementForm(ModelForm):

    class Meta:
        model = SubstitutePlacement
        fields = '__all__'

    pltype = PlacementType.objects.get(pk=3)

    def _post_clean(self):
        super(SubstitutePlacementForm, self)._post_clean()
        if not self.instance.date_to:
            self.instance.date_to = current_year_date_to_half()
        self.instance.type = SubstitutePlacementForm.pltype

TAXED_TYPES = [(11, u'Τακτικές Μονίμων'), 
               (12, u'Τακτικές Αναπληρωτών'), 
               (21, u'Έκτακτες που φορολογούνται'), 
               (22, u'Έκτακτες που δεν φορολογούνται'),  
               (23, u'Έκτακες με αυτοτελή φόρο')]


class PaymentFileNameMassForm(forms.Form):
    is_bound = 0
    xml_file =  forms.FileField(label=u'Αρχείο ZIP', required=True)
    description = forms.CharField(label=u'Εμφανιζόμενο όνομα',
                                  required=True)
    taxed = forms.TypedChoiceField(label=u'Τύπος αποδοχών', choices=TAXED_TYPES, coerce=int)


class SchoolCommissionForm(forms.ModelForm):

    class Meta:
        model = SchoolCommission
        fields = '__all__'

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
