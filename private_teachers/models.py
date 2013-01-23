# -*- coding: utf-8 -*-
from __future__ import division
import collections
from dideman.lib.date import *
from django.contrib import admin
from django.db import models
import dideman.dide.models as dide


class PrivateTeacher(models.Model):

    class Meta:
        verbose_name = u'Ιδιωτικός Εκπαιδευτικός'
        verbose_name_plural = u'Ιδιωτικοί Εκπαιδευτικοί'
        ordering = ['lastname']

    firstname = models.CharField(u'Όνομα', max_length=100)
    lastname = models.CharField(u'Επώνυμο', max_length=100)
    fathername = models.CharField(u'Όνομα Πατέρα', max_length=100)
    mothername = models.CharField(u'Όνομα Μητέρας', max_length=100, null=True, blank=True)

    profession = models.ForeignKey(dide.Profession, verbose_name=u'Ειδικότητα', related_name='private_teachers')
    registration_number = models.CharField(u'Βεβαίωση εγγραφής στην επετηρίδα', null=True, blank=True, max_length=25)
    sex = models.CharField(u'Φύλο', max_length=10, null=True, blank=True, choices=dide.SEX_TYPES)
    identity_number = dide.NullableCharField(u'Αρ. Δελτίου Ταυτότητας', max_length=8, null=True, unique=True, blank=True)
    recognised_experience = models.CharField(u'Αναγνωρισμένη προυπηρεσία (ΕΕΜΜΗΜΗΜ)', null=True, blank=True, default='000000', max_length=8)
    birth_date = models.DateField(u'Ημερομηνία Γέννησης', null=True, blank=True)
    has_master = models.BooleanField(u'Μεταπτυχιακό', default=False)
    has_phd = models.BooleanField(u'Διδακτορικό', default=False)
    no_pay_days = models.IntegerField(u'Μέρες άδειας άνευ αποδοχών', default=0)
    telephone_number = models.CharField(u'Τηλέφωνο επικοινωνίας', max_length=20, null=True, blank=True)

    school = models.ForeignKey('PrivateSchool', verbose_name=u'Σχολείο', blank=True, null=True)
    active = models.BooleanField(u'Ενεργός', default=True)
    date_created = models.DateField(u'Ημερομηνία δημιουργίας', auto_now_add=True)

    def total_experience(self):
        return reduce(DateInterval.__add__,
                      [o.experience() for o in self.workingperiod_set.all()],
                      DateInterval())
    total_experience.short_description = u'Συνολική προϋπηρεσία'

    def profession_description(self):
        return self.profession.description
    profession_description.short_description = u'Λεκτικό ειδικότητας'

    def __unicode__(self):
        return '%s %s' % (self.lastname, self.firstname)


class WorkingPeriod(models.Model):

    class Meta:
        verbose_name = u'Περίοδος Εργασίας'
        verbose_name_plural = u'Περίοδοι Εργασίας'
        ordering = ["-date_to"]

    teacher = models.ForeignKey(PrivateTeacher)
    date_from = models.DateField(u'Από')
    date_to = models.DateField(u'Μέχρι')
    hours_weekly = models.IntegerField(u'Εβδομαδιαίες ώρες εργασίας', max_length=2, null=True, blank=True)
    hours_total = models.IntegerField(u'Συνολικές ώρες εργασίας', max_length=4, null=True, blank=True)
    full_week = models.IntegerField(u'Εβδομαδιαίο ωράριο', max_length=2, default=18)

    def experience(self):
        fr = Date(self.date_from)
        to = Date(self.date_to)
        days = (to - fr).total + 1

        if self.hours_weekly >= self.full_week:
            return DateInterval(days=days)

        if self.hours_total:
            days = int((self.hours_total / self.full_week) * 6)
        else:
            days = days * (300 / 360)
            days = int(days * (self.hours_weekly / self.full_week))

        return DateInterval(days // 300, (days % 300) // 25, (days % 300) % 25)


class PrivateSchool(models.Model):

    class Meta:
        verbose_name = u'Ιδιωτικό Σχολείο'
        verbose_name_plural = u'Ιδιωτικά Σχολεία'
        ordering = ['name']

    name = models.CharField(u'Όνομα', max_length=200)
    address = models.CharField(u'Διεύθυνση', max_length=200, null=True, blank=True)
    post_code = models.CharField(u'Τ.Κ.', max_length=5, null=True, blank=True)
    telephone_number = models.CharField(u'Αρ. Τηλεφώνου', max_length=14, null=True, blank=True)
    fax_number = models.CharField(u'Αρ. Fax', max_length=14, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    def __unicode__(self):
        return self.name
