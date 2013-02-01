# -*- coding: utf-8 -*-
from __future__ import division
from functools import reduce
import collections
from dideman.lib.date import *
from django.contrib import admin
from django.db import models
import dideman.dide.models as dide


def int300(days):
    return DateInterval(days // 300, (days % 300) // 25, (days % 300) % 25)


class PrivateTeacher(dide.Employee):

    class Meta:
        verbose_name = u'Ιδιωτικός Εκπαιδευτικός'
        verbose_name_plural = u'Ιδιωτικοί Εκπαιδευτικοί'
        ordering = ['lastname']

    parent = models.OneToOneField(dide.Employee, parent_link=True)
    school = models.ForeignKey('PrivateSchool', verbose_name=u'Σχολείο', blank=True, null=True)
    no_pay_days = models.IntegerField(u'Μέρες άδειας άνευ αποδοχών', default=0)
    series_number = models.CharField(u'Αρ. Επετηρίδας', max_length=20, blank=True, null=True)
    active = models.BooleanField(u'Ενεργός', default=True)
    current_hours = models.IntegerField(u'Τρέχον ωράριο', null=True, blank=True, default=18)
    current_placement_date = models.DateField(u'Ημερομηνία τρέχουσας τοποθέτησης', blank=True, null=True)

    def total_experience(self, periods=None):
        periods = periods or self.workingperiod_set.all()
        ranges = [DateRange(Date(w.date_from), Date(w.date_to)) for w in periods]
        splitted = DateRange.split_all(ranges)
        intersections = [(r, p) for r in splitted
                         for i, p in enumerate(periods)
                         if r.intersects(ranges[i])]
        d = collections.defaultdict(list)
        for r, p in intersections:
            d[r].append(p)

        exp = [(r.total, sum([p.range_experience(r) for p in l]))
               for r, l in d.items()]

        # all the reduced experience is summed before the conversion
        # Δ2/2988/27.2.89
        total, reduced = map(sum,
                             zip(*[(t, 0) if r * 1.2 > t else (0, r)
                                   for t, r in exp]))
        return (DateInterval(int(total)) +
                int300(int(reduced)) -
                DateInterval(self.no_pay_days))
    total_experience.short_description = u"Προϋπηρεσία"

    def total_service(self):
        if not self.current_placement_date:
            return self.total_experience()

        wp = WorkingPeriod(teacher=self, date_from=self.current_placement_date,
                           date_to=datetime.date.today(),
                           hours_weekly=self.current_hours, full_week=18)
        periods = list(self.workingperiod_set.all()) + [wp]
        return self.total_experience(periods)

    total_service.short_description = u'Συνολική υπηρεσία'

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
    comments = models.CharField(u'Σχόλια', max_length=255, null=True, blank=True)

    def range_experience(self, arange):
        if self.hours_weekly >= self.full_week:
            return arange.total
        else:
            dr = self.date_range()
            if self.hours_total:
                hours = self.hours_total * (arange.total / dr.total)
                return (hours / self.full_week) * 6
            else:
                days = arange.total * (300 / 360)
                return days * (self.hours_weekly / self.full_week)

    def date_range(self):
        return DateRange(Date(self.date_from), Date(self.date_to))

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
