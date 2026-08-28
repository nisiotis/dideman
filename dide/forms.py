# -*- coding: utf-8 -*-
from django import forms
from django.utils.encoding import force_str
from django.utils.html import mark_safe
from django.forms.widgets import flatatt

from django.forms.models import ModelForm
from django.forms import Widget
from django.contrib.admin.widgets import AdminDateWidget 
from dideman.dide.models import OrderedSubstitution, SubstitutePlacement, NonPermanent, PlacementType, School, SchoolCommission
from dideman.lib.date import current_year_date_to_half


class SubstituteInput(forms.HiddenInput):

    def render(self, name, value, attrs=None, renderer=None):
        # Το renderer μπήκε στην υπογραφή των widgets στο Django 1.11 και
        # το build_attrs δέχεται πλέον δύο λεξικά αντί για keyword args.
        try:
            nid = value
            value = str(NonPermanent.objects.get(parent_id=value))
        except Exception:
            nid = None
            value = ''
        final_attrs = self.build_attrs(self.attrs, attrs)
        final_attrs['type'] = self.input_type
        final_attrs['name'] = name
        final_attrs.setdefault('id', 'id_%s' % name)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_str(self.format_value(nid))
        wid = final_attrs['id']
        output = []
        output.append('<input%s />' % flatatt(final_attrs))
        output.append('<input readonly="true" type="text" id="display_%s" value="%s" size="40" />&nbsp;' % (wid, force_str(value)))
        output.append('<a href="#" id="link_%s" onclick="this.href=\'/admin/dide/nonpermanent/list/\'+\'?id=\'+django.jQuery(this).attr(\'id\');return focusOrOpen(this, \'Αναπληρωτές\',{\'width\': 500, \'height\': 600});">Επιλογή</a>&nbsp;' % wid)
        output.append('<a href="/admin/dide/nonpermanent/add/" class="add-another" id="add_%s" onclick="return showAddAnotherPopup(this);"> <img src="/static/admin/img/icon-addlink.svg" width="10" height="10" alt="Προσθέστε κι άλλο"></a>' % wid)
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

    # Ο τύπος τοποθέτησης αναζητείται εδώ και όχι στο σώμα της κλάσης: ένα
    # ερώτημα σε import time εκτελείται πριν υπάρξουν οι πίνακες και σπάει
    # κάθε manage.py εντολή σε καθαρή βάση.
    PLACEMENT_TYPE_PK = 3

    def _post_clean(self):
        super(SubstitutePlacementForm, self)._post_clean()
        if not self.instance.date_to:
            self.instance.date_to = current_year_date_to_half()
        self.instance.type = PlacementType.objects.get(pk=self.PLACEMENT_TYPE_PK)

TAXED_TYPES = [(11, 'Τακτικές Μονίμων'), 
               (12, 'Τακτικές Αναπληρωτών'), 
               (21, 'Έκτακτες που φορολογούνται'), 
               (22, 'Έκτακτες που δεν φορολογούνται'),  
               (23, 'Έκτακες με αυτοτελή φόρο')]


class PaymentFileNameMassForm(forms.Form):
    is_bound = 0
    xml_file =  forms.FileField(label='Αρχείο ZIP', required=True)
    description = forms.CharField(label='Εμφανιζόμενο όνομα',
                                  required=True)
    taxed = forms.TypedChoiceField(label='Τύπος αποδοχών', choices=TAXED_TYPES, coerce=int)


class SchoolCommissionForm(forms.ModelForm):

    class Meta:
        model = SchoolCommission
        fields = '__all__'

    schools = forms.ModelMultipleChoiceField(label='Σχολεία', queryset=School.objects.all(),
                                             widget=forms.SelectMultiple(attrs={'size':'40'}))

    def __init__(self, *args, **kwargs):
        super(SchoolCommissionForm, self).__init__(*args, **kwargs)
        # Σε νέα εγγραφή το instance δεν έχει ακόμη pk· από το Django 2.0 η
        # πρόσβαση στο reverse manager ενός μη αποθηκευμένου αντικειμένου
        # σηκώνει ValueError αντί να επιστρέψει κενό queryset.
        if self.instance.pk:
            self.fields['schools'].initial = self.instance.school_set.all()
        else:
            self.fields['schools'].initial = School.objects.none()

    def save(self, *args, **kwargs):
        # FIXME: 'commit' argument is not handled
        # TODO: Wrap reassignments into transaction
        # NOTE: Previously assigned Foos are silently reset
        instance = super(SchoolCommissionForm, self).save(commit=False)
        self.fields['schools'].initial.update(commission=None)
        self.cleaned_data['schools'].update(commission=instance)
        return instance
