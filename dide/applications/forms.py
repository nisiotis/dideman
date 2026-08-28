# -*- coding: utf-8 -*-
from django import forms
from dideman.dide.models import Permanent, MoveInside
from django.utils.translation import gettext as _
from dideman.dide.models import HEALTH_CHOICES, School

HEALTH_CHOICES = (('', ''),) + HEALTH_CHOICES


class TemporaryPositionForm(forms.Form):
    telephone_number = forms.CharField(label='Τηλέφωνο Επικοινωνίας')
    colocation_municipality = forms.CharField(label='Δήμος Συνυπηρέτησης',
                                              required=False)
    nativity_municipality = forms.CharField(label='Δήμος Εντοπιότητας',
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
    telephone_number = forms.CharField(label='Τηλέφωνο Επικοινωνίας')
    colocation_municipality = forms.CharField(label='Δήμος Συνυπηρέτησης',
                                              required=False)
    nativity_municipality = forms.CharField(label='Δήμος Εντοπιότητας',
                                            required=False)
    married = forms.BooleanField(label='Έγγαμος',
                                 required=False)
    custody = forms.BooleanField(label='Επιμέλεια παιδιών',
                                 required=False)
    single_parent = forms.BooleanField(label='Μονογονεϊκή οικογένεια',
                                       required=False)
    children = forms.IntegerField(label=('Αριθμός παιδιών που είναι ανήλικα'
                                        ' ή σπουδάζουν'), required=False)
    health_self = forms.ChoiceField(label='Λόγοι Υγείας',
                                    choices=HEALTH_CHOICES, required=False)
    health_spouse = forms.ChoiceField(label='Λόγοι υγείας συζύγου',
                                      choices=HEALTH_CHOICES, required=False)
    health_children = forms.ChoiceField(label='Λόγοι υγείας παιδιών',
                                        choices=HEALTH_CHOICES, required=False)
    health_parents = forms.ChoiceField(label='Λόγοι υγείας γονέων',
                                       choices=HEALTH_CHOICES, required=False)
    parents_place = forms.CharField(label='Περιοχή διαμονής γονέων',
                                      max_length=150, required=False)
    health_siblings = forms.BooleanField(
        label='Λόγοι υγείας αδερφών (> 67% με επιμέλεια)', required=False)
    siblings_place = forms.CharField(label='Περιοχή διαμονής αδερφών',
                                       max_length=150, required=False)
    in_vitro = forms.BooleanField(label='Θεραπεία εξωσωματικής γονιμοποίησης',
                                  required=False)
    post_graduate_subject = forms.CharField(
        label='Περιοχή μεταπτυχιακών σπουδών (εφόσον υπάρχει)',
        required=False, max_length=150)
    special_category = forms.CharField(label='Ειδική κατηγορία μετάθεσης',
                                        max_length=150, required=False)
    military_spouse = forms.BooleanField(label='Σύζυγος στρατιωτικού',
                                         required=False)
    elected = forms.BooleanField(label='Αιρετός Ο.Τ.Α.',
                                 required=False)
    judge_spouse = forms.BooleanField(label='Σύζυγος δικαστικού',
                                      required=False)
    move_primary = forms.BooleanField(
        label='Επιθυμώ απόσπαση και στην Α\'Βάθμια', required=False)
    other_reasons = forms.CharField(label='Άλλοι λόγοι',
                                    widget=forms.Textarea,
                                    max_length=500, required=False)

    def choices(self, employee):
        return School.objects.all()

    def choices_length(self):
        return 10
