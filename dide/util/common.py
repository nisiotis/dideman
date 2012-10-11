# -*- coding: utf-8 -*-
import datetime


now = datetime.datetime.now()

_accent_map = {u'Ά': u'Α', u'Έ': u'Ε', u'Ή': u'Η', u'Ό': u'Ο',
               u'Ί': u'Ι', u'Ύ': u'Υ', u'Ώ': u'Ω'}


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
    return '%s-%s' % (str(current_year_date_from().year),
                      str(current_year_date_to().year))


def parse_date_period(d):
    return d[:2], d[2:4], d[4:6]


def date_add(d1, d2):
    """ adds two periods of time (in the string form 'yymmdd')
    , the greek way, yey..."""
    d1y, d1m, d1d = parse_date_period(d1)
    d2y, d2m, d2d = parse_date_period(d2)
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
    """ adds two periods of time (in the string form 'yymmdd')
    , the greek way, yey..."""
    d1y, d1m, d1d = parse_date_period(d1)
    d2y, d2m, d2d = parse_date_period(d2)
    days = d1d - d2d
    months = d1m - d2m
    years = d1y - d2y
    if days < 0:
        days += 30
        months -= 1
    if months < 0:
        months += 12
        years -= 1
    return years, months, days


def get_class(name):
    arr = name.split('.')
    m = __import__('.'.join(arr[:-1]), fromlist=['none'])
    return getattr(m, arr[-1:][0])
