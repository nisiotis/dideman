# -*- coding: utf-8 -*-
from __future__ import division
import collections
from dideman.lib.date import *
from django.contrib import admin
from django.db import models
import dideman.dide.models as dide


class PrivateTeacher(dide.Employee):

    class Meta:
        verbose_name = u'Ιδιωτικός Εκπαιδευτικός'
        verbose_name_plural = u'Ιδιωτικοί Εκπαιδευτικοί'
        ordering = ['lastname']

    parent = models.OneToOneField(dide.Employee, parent_link=True)
    school = models.ForeignKey('PrivateSchool', verbose_name=u'Σχολείο', blank=True, null=True)
    no_pay_days = models.IntegerField(u'Μέρες άδειας άνευ αποδοχών', default=0)
    active = models.BooleanField(u'Ενεργός', default=True)

    def total_experience(self):
        periods = self.workingperiod_set.all()
        ranges = [DateRange(Date(w.date_from), Date(w.date_to)) for w in periods]
        splitted = DateRange.split_all(ranges)
        intersections = [(r, p) for r in splitted
                         for i, p in enumerate(periods)
                         if r.intersects(ranges[i])]
        d = collections.defaultdict(list)
        for r, p in intersections:
            d[r].append(p)

        # return DateInterval(
        #     days=sum([min(r.total, sum([p.experience(r).total
        #                                 for p in l]))
        #               for r, l in d.items()]))

    def save(self, *args, **kwargs):
        self.currently_serves = False
        super(PrivateTeacher, self).save(*args, **kwargs)


class WorkingPeriod(models.Model):

    class Meta:
        verbose_name = u'Περίοδος Εργασίας'
        verbose_name_plural = u'Περίοδοι Εργασίας'
        ordering = ["-date_to"]

    teacher = models.ForeignKey(dide.Employee)
    date_from = models.DateField(u'Από')
    date_to = models.DateField(u'Μέχρι')
    hours_weekly = models.IntegerField(u'Εβδομαδιαίες ώρες εργασίας', max_length=2, null=True, blank=True)
    hours_total = models.IntegerField(u'Συνολικές ώρες εργασίας', max_length=4, null=True, blank=True)
    full_week = models.IntegerField(u'Εβδομαδιαίο ωράριο', max_length=2, default=18)

    def experience(self):
        dr = DateRange(Date(self.date_from), Date(self.date_to))

        if self.hours_weekly >= self.full_week:
            return DateInterval(days=dr.total)

        #300 day year
        if self.hours_total:
            days = int((self.hours_total / self.full_week) * 6)
        else:
            days = dr.total * (300 / 360)
            days = int(days * (self.hours_weekly / self.full_week))

        return DateInterval(days // 300, (days % 300) // 25, (days % 300) % 25)

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "<WorkingPeriod %s - %s>" % (self.date_from, self.date_to)


class PrivateSchool(dide.Organization):

    class Meta:
        verbose_name = u'Ιδιωτικό Σχολείο'
        verbose_name_plural = u'Ιδιωτικά Σχολεία'
        ordering = ['name']

    parent = models.OneToOneField(dide.Organization, parent_link=True)
    address = models.CharField(u'Διεύθυνση', max_length=200, null=True, blank=True)
    post_code = models.CharField(u'Τ.Κ.', max_length=5, null=True, blank=True)
    telephone_number = models.CharField(u'Αρ. Τηλεφώνου', max_length=14, null=True, blank=True)
    fax_number = models.CharField(u'Αρ. Fax', max_length=14, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
