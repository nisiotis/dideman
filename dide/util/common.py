# -*- coding: utf-8 -*-
import datetime
import math

now = datetime.datetime.now()

_accent_map = {u'Ά': u'Α', u'Έ': u'Ε', u'Ή': u'Η', u'Ό': u'Ο',
               u'Ί': u'Ι', u'Ύ': u'Υ', u'Ώ': u'Ω'}


def filter_nested(l, pred):
    if isinstance(l, list):
        return [r for r in [parse_deletable_list(i) for i in l] if r]
    else:
        return l if pred(l) else None


def parse_deletable_list(l):
    return filter_nested(l,
                         lambda x: x not in ['Payment: Payment object',
                                             'Payment category: PaymentCategory object'])


def without_accented(string):
    new = ''
    for i in string:
        if i in _accent_map:
            new += _accent_map[i]
        else:
            new += i
    return new


def first_or_none(iterable):
    if iterable:
        return iterable[0]
    else:
        return None


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


def parse_date(d):
    """parses a date string yyyymmdd or yymmdd and returns a (y, m, d) tuple"""
    yl = 4 if len(d) == 8 else 2
    return tuple([int(d) for d in [d[:yl], d[yl:yl + 2], d[yl + 2:yl + 4]]])


def date_from_python(d):
    """takes a python datetime.date object and returns a  (y, m, d) tuple"""
    return d.year, d.month, d.day


def to_days(d):
    """takes a (y, m, d) date and return the number of days of it"""
    return d[0] * 360 + d[1] * 30 + d[2]


def from_days(days):
    """takes a number which represents days and returns a (y, m, d) date"""
    y = int(days / 360)
    m = int((days % 360) / 30)
    d = days - (y * 360 + m * 30)
    print y, m, d
    return y, m, d


def date_add(d1, d2):
    """ takes two dates (dates or periods), both
    in the form of a tuple (y, m, d), sums them and returns
    the new date
    """
    d1y, d1m, d1d = d1
    d2y, d2m, d2d = d2
    days = d1d + d2d
    months = d1m + d2m
    years = d1y + d2y
    if days > 30:
        days -= 30
        months += 1
    if months > 12:
        months -= 12
        years += 1
    return years, months, days


def date_subtract(d1, d2):
    """ takes two dates (dates or periods), both
    in the form of a tuple (y, m, d), subtracts them and returns
    the new date
    """
    d1y, d1m, d1d = d1
    d2y, d2m, d2d = d2
    days = d1d - d2d
    months = d1m - d2m
    years = d1y - d2y
    if days <= 0:
        days += 30
        months -= 1
    if months <= 0:
        months += 12
        years -= 1
    return years, months, days


def date_to_period(date):
    """ takes a date in the form of a tuple (y, m, d)
    and returns a period of time in the same form
    (30 days becomes a month, 12 months becomes a year)
    """
    y, m, d = date
    if d == 30:
        m += 1
        d = 0
    if m >= 12:
        y += 1
        m -= 12
    return y, m, d


def get_class(name):
    arr = name.split('.')
    m = __import__('.'.join(arr[:-1]), fromlist=['none'])
    return getattr(m, arr[-1:][0])
