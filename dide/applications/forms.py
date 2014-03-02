# -*- coding: utf-8 -*-
from django import forms
from dideman.dide.models import Permanent, MoveInside
from django.utils.translation import ugettext as _
from dideman.dide.models import HEALTH_CHOICES, School

HEALTH_CHOICES = ((u'', u''),) + HEALTH_CHOICES


class TemporaryPositionForm(forms.Form):
    telephone_number = forms.CharField(label=u'Τηλέφωνο Επικοινωνίας')
    colocation_municipality = forms.CharField(label=u'Δήμος Συνυπηρέτησης',
                                              required=False)
    nativity_municipality = forms.CharField(label=u'Δήμος Εντοπιότητας',
                                            required=False)

    def choices(self, employee):
        return School.objects.filter(transfer_area=employee.transfer_area)

    def choices_length(self):
        return 39


class TemporaryPositionAllAreasForm(TemporaryPositionForm):
    def choices(self, employee):
        return School.objects.all()

    def choices_length(self):
        return 40


class MoveInsideForm(forms.Form):
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

    def choices(self, employee):
        return School.objects.all()

    def choices_length(self):
        return 10
