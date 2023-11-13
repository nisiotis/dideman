# -*- coding: utf-8 -*-
from __future__ import division
import collections
from dideman.lib.date import *
from django.db import models
from dideman.dide import models as dide
from dideman.lib.ranking import RANKS, next_index
import datetime
import operator


def int300(days):
    return DateInterval(days // 300, (days % 300) // 25, (days % 300) % 25)


class PrivateTeacher(dide.Employee):

    class Meta:
        verbose_name = u'Ιδιωτικός Εκπαιδευτικός'
        verbose_name_plural = u'Ιδιωτικοί Εκπαιδευτικοί'
        ordering = ['lastname']

    parent = models.OneToOneField(dide.Employee, parent_link=True)
    school = models.ForeignKey('PrivateSchool', verbose_name=u'Σχολείο', blank=True, null=True)
    not_service_days = models.IntegerField(u'Μέρες εκτός υπηρεσίας', default=0)
    series_number = models.CharField(u'Αρ. Επετηρίδας', max_length=20, blank=True, null=True)
    active = models.BooleanField(u'Ενεργός', default=True)
    current_hours = models.IntegerField(u'Τρέχον ωράριο', null=True, blank=True, default=18)
    current_placement_date = models.DateField(u'Ημερομηνία τρέχουσας τοποθέτησης', blank=True, null=True)

    def object_name(self):
        return self._meta.object_name

    def app_label(self):
        return self._meta.app_label

    def _total_days(self, periods=None):
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
                                   for t, r in exp])) or (0, 0)
        return total, reduced

    def total_experience(self, periods=None):
        total, reduced = self._total_days(periods)
        return DateInterval(int(total)) + int300(int(reduced))
    total_experience.short_description = u"Προϋπηρεσία"

    def total_service(self):
        if not self.current_placement_date:
            total_experience = self.total_experience()
        else:
            wp = WorkingPeriod(teacher=self, date_from=self.current_placement_date,
                               date_to=datetime.date.today(),
                               hours_weekly=self.current_hours, full_week=18)
            periods = list(self.workingperiod_set.all()) + [wp]
            
            total_experience = self.total_experience(periods)
        dli = reduce(operator.add,
                     [DateInterval(l.recognised_experience)
                      for l in self.leavewithoutpay_set.all()],
                     DateInterval("000000"))
        
        return total_experience - DateInterval(self.not_service_days) + dli
    total_service.short_description = u'Συνολική υπηρεσία'

# added by vasilis 
# functions to calculate service up to today and up to 31/12/2015
    def total_service_today(self):
        if not self.current_placement_date:
            total_experience = self.total_experience()
        else:
            wp = WorkingPeriod(teacher=self, date_from=self.current_placement_date,
                               date_to=datetime.date.today(),
                               hours_weekly=self.current_hours, full_week=18)
            periods = list(self.workingperiod_set.all()) + [wp]
            periods.pop(0)
            
            total_experience = self.total_experience(periods)
        dli = reduce(operator.add,
                     [DateInterval(l.recognised_experience)
                      for l in self.leavewithoutpay_set.all()],
                     DateInterval("000000"))
        #import pdb; pdb.set_trace() 
        return total_experience - DateInterval(self.not_service_days) + dli
    total_service_today.short_description = u'Συνολική υπηρεσία μέχρι σήμερα'


    def total_service_311215(self):
        if not self.current_placement_date:
            total_experience = self.total_experience()
        else:
            if self.current_placement_date < datetime.date(2015, 12, 31):
                wp = WorkingPeriod(teacher=self, date_from=self.current_placement_date,
                                   date_to=datetime.date(2015, 12, 31),
                                   hours_weekly=self.current_hours, full_week=18)
                periods = list(self.workingperiod_set.all()) + [wp]
                periods.pop(0)
                total_experience = self.total_experience(periods)
            else:
                periods = list(self.workingperiod_set.all())
                if len(periods) > 0:
                    periods.pop(0)
                if periods == []:
                    total_experience = DateInterval("000000")
                else:
                    total_experience = self.total_experience(periods)
            
        
        dli = reduce(operator.add,
                     [DateInterval(l.recognised_experience)
                      for l in self.leavewithoutpay_set.all()],
                     DateInterval("000000"))
        return total_experience - DateInterval(self.not_service_days) + dli
    total_service_311215.short_description = u'Υπηρεσία μέχρι 31/12/2015'
# --

    def rank(self):
        r, mk = RANKS[min(
                self.total_service().years + self.postgrad_extra().years, 40)]
        return u"%s%s" % (r, mk)
    rank.short_description = u'Βαθμός (εκτίμηση)'

    def postgrad_extra(self):
        degrees = self.employeedegree_set.all().select_related('degree')
        has_msc = degrees.filter(degree__id=1).exists()
        has_phd = degrees.filter(degree__id=2).exists()
        return DateInterval(years=min(int(has_msc) * 2 + int(has_phd) * 6, 7))

    def next_rank_date(self):
        total_service = self.total_service() + self.postgrad_extra()
        r, mk = RANKS[min(total_service.years, 40)]
        year = next_index((r, mk))
        when = DateInterval(years=year)
        interval = when - total_service
        if self.current_hours:
            if self.current_hours >= 18:
                di = datetime.date.today() + datetime.timedelta(days=interval.total)
                return di.strftime("%d-%m-%Y")
            else:
                x360, x300 = self._total_days()
                days =  (when - DateInterval(x360) - self.postgrad_extra()).total300() - x300
                if self.current_placement_date:
                    di = self.current_placement_date + datetime.timedelta(days=int(days * (18 / self.current_hours) * (365/300)))
                else:
                    di = datetime.timedelta(days=int(days * (18 / self.current_hours) * (365/300)))
                return di.strftime("%d-%m-%Y")
        else:
            return "-"
    next_rank_date.short_description = u'Ημερομηνία αλλαγής Μ.Κ. (εκτίμηση)'

    def save(self, *args, **kwargs):
        self.currently_serves = False
        super(PrivateTeacher, self).save(*args, **kwargs)

    def employee_type_text(self):
        if self.sex == "Άνδρας":
            return "ιδιωτικός"
        else:
            return "ιδιωτική"


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
        try:
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
        except:
            return 0

    def date_range(self):
        return DateRange(Date(self.date_from), Date(self.date_to))

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "<WorkingPeriod %s - %s>" % (self.date_from, self.date_to)


class LeaveWithoutPay(models.Model):

    class Meta:
        verbose_name = u'Άδεια άνευ αποδοχών'
        verbose_name_plural = u'Άδειες άνευ αποδοχών'

    teacher = models.ForeignKey(dide.Employee)
    date_from = models.DateField(u'Από')
    date_to = models.DateField(u'Μέχρι')
    recognised_experience = models.CharField(u'Αναγνωρίσιμη Προϋπηρεσία (ΕΕΜΜΗΜΗΜ)', null=True, blank=True, default='000000', max_length=8)

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "<Leave %s - %s>" % (self.date_from, self.date_to)



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
