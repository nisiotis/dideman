# -*- coding: utf-8 -*-
from __future__ import division
import datetime
import math

now = datetime.datetime.now()


def current_year_date_from():
    if now.month < 9:
        return datetime.date(now.year - 1, 9, 1)
    else:
        return datetime.date(now.year, 9, 1)


def current_year_date_to():
    if now.month < 9:
        return datetime.date(now.year, 8, 31)
    else:
        return datetime.date(now.year + 1, 8, 31)


def current_year_date_to_half():
    if now.month < 9:
        return datetime.date(now.year, 6, 30)
    else:
        return datetime.date(now.year + 1, 6, 30)


def current_year():
    """ returns current school year e.g. 2011-2012"""
    return '%s-%s' % (str(current_year_date_from().year),
                      str(current_year_date_to().year))


def get_class(name):
    arr = name.split('.')
    m = __import__('.'.join(arr[:-1]), fromlist=['none'])
    return getattr(m, arr[-1:][0])


class Date360(object):
    """
    a class for handling 360 dates and periods
    """

    @classmethod
    def from_string(cls, d):
        """
        parses a date string yyyymmdd or yymmdd and returns a Date360 object
        """
        yl = 4 if len(d) == 8 else 2
        return cls(*[int(d) for d in [d[:yl], d[yl:yl + 2], d[yl + 2:yl + 4]]])

    @classmethod
    def from_python(cls, d):
        """
        takes a python datetime.date object and returns a Date360 object
        """
        return cls(d.year, d.month, d.day)

    @classmethod
    def from_day_count(cls, daycount):
        """
        takes a number which represents a daycount
        and returns a Date360 object
        """
        y = int(daycount / 360)
        m = int((daycount % 360) / 30)
        d = daycount - (y * 360 + m * 30)
        return cls(y, m, d)

    def __init__(self, y, m, d):
        self.y = y
        self.m = m
        self.d = d

    def to_period(self):
        """
        takes a date in the form of a tuple (y, m, d)
        and returns a period of time in the same form
        (30 days becomes a month, 12 months becomes a year)
        """
        y, m, d = self.to_tuple()
        if d == 30:
            m += 1
            d = 0
        if m >= 12:
            y += 1
            m -= 12
        return self.__class__(y, m, d)

    def to_day_count(self):
        """
        returns the daycount of the current object
        """
        return self.y * 360 + self.m * 30 + self.d

    def to_tuple(self):
        return self.y, self.m, self.d

    def format(self):
        return "%s-%s-%s" % (self.d, self.m, self.y)

    def format_period(self):
        return u"%s χρόνια, %s μήνες, %s ημέρες" % self.to_period().to_tuple()

    def __add__(self, other):
        """
        adds two Date360's returning a new one
        """
        d1y, d1m, d1d = self.to_tuple()
        d2y, d2m, d2d = other.to_tuple()
        days = d1d + d2d
        months = d1m + d2m
        years = d1y + d2y
        if days > 30:
            days -= 30
            months += 1
        if months > 12:
            months -= 12
            years += 1
        return self.__class__(years, months, days)

    def __sub__(self, other):
        """
        subtracts two Date360's returning a new one
        """
        d1y, d1m, d1d = self.to_tuple()
        d2y, d2m, d2d = other.to_tuple()
        days = d1d - d2d
        months = d1m - d2m
        years = d1y - d2y
        if days <= 0:
            days += 30
            months -= 1
        if months <= 0:
            months += 12
            years -= 1
        return self.__class__(years, months, days)

    def __unicode__(self):
        return self.format()
