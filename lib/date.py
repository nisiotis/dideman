# -*- coding: utf-8 -*-
from __future__ import division
import datetime

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


class Date(object):
    """
    a class for handling 360 day year dates
    """
    def __init__(self, *args, **kwargs):
        """
        construct a Date object when given one of the following:
        python datetime | "YYYYMMDD" string | (year, month, day)
        """
        param = args[0]
        if isinstance(param, str):
            year, month, day = [int(d)
                                for d in [param[:4], param[4:6], param[6:]]]
        elif isinstance(param, datetime.date):
            year, month, day = param.year, param.month, param.day
        else:
            year, month, day = args

        self.year = year
        self.month = month
        self.day = day

    @property
    def days(self):
        """
        date converted to number of days
        """
        return self.year * 360 + self.month * 30 + self.day

    def tuple(self):
        return self.year, self.month, self.day

    def format(self, formatter=None):
        """
        format the tuple (self.day, self.month, self.year) as a string
        when given a formatter. If no formatter is given the default
        formatter ("%s/%s/%s") is applied
        """
        formatter = formatter or "%s/%s/%s"
        return formatter % (self.day, self.month, self.year)

    def add_interval(self, interval):
        new_interval = DateInterval(self.days + interval.total)
        y, m, d = new_interval.tuple()
        return self.__class__(y, m, d)

    def sub_interval(self, interval):
        y, m, d = [a - b for a, b in zip(self.tuple(), interval.tuple())]
        if d <= 0:
            d += 30
            m -= 1
        if m <= 0:
            m += 12
            y -= 1
        return self.__class__(y, m, d)

    def sub_date(self, other):
        return DateInterval(days=self.days - other.days)

    def __add__(self, interval):
        return self.add_interval(interval)

    def __sub__(self, other):
        if isinstance(other, self.__class__):
            return self.sub_date(other)
        else:
            return self.sub_interval(other)

    def __cmp__(self, other):
        return self.days - other.days

    def __repr__(self):
        return "<%s '%s'>" % (self.__class__.__name__, self.format())

    def __str__(self):
        return self.format()

    def __unicode__(self):
        return self.format()


class DateInterval(object):
    """
    a class for handling 360 day year date intervals
    """
    def __init__(self, *args, **kwargs):
        """
        construct a DateInterval object when given one or all :
        one or all of days, months, years as kwargs |
        a string formatted as "YYYYMMDD" or "YYMMDD" |
        days as first argument |
        years, months, days as 1st, 2nd 3rd argument
        """
        if args and isinstance(args[0], (str, unicode)):
            param = args[0]
            yl = 4 if len(param) == 8 else 2
            years, months, days = [int(d)
                                   for d in [param[:yl], param[yl:yl + 2],
                                             param[yl + 2:yl + 4]]]
        else:
            if args and isinstance(args[0], (int, long, float)):
                if len(args) == 3:
                    years = args[0]
                    months = args[1]
                    days = args[2]
                else:
                    days = args[0]
                    years = 0
                    months = 0
            else:
                years = kwargs.get('years', 0)
                months = kwargs.get('months', 0)
                days = kwargs.get('days', 0)
        self.total = years * 360 + months * 30 + days

    @property
    def years(self):
        return self.total // 360

    @property
    def months(self):
        return (self.total % 360) // 30

    @property
    def days(self):
        return (self.total % 360) % 30

    def tuple(self):
        return self.years, self.months, self.days

    def format(self, formatter=None):
        """
        format the tuple (self.years, self.months, self.days) as a string
        when given a formatter. If no formatter is given the default
        formatter (u"%s έτη, %s μήνες, %s ημέρες") is applied
        """
        formatter = formatter or u"%s έτη, %s μήνες, %s ημέρες"
        return formatter % (self.years, self.months, self.days)

    def __add__(self, other):
        return self.__class__(days=self.total + other.total)

    def __sub__(self, other):
        return self.__class__(days=self.total - other.total)

    def __cmp__(self, other):
        return self.total - other.total

    def __repr__(self):
        return "<%s '%s-%s-%s'>" % (self.__class__.__name__,
                                  self.years, self.months, self.days)

    def __str__(self):
        return "%s-%s-%s" % self.tuple()

    def __unicode__(self):
        return self.format()


class DateRange(object):
    """
    class for handling date ranges of 360 day years
    """
    def __init__(self, start, end):
        """
        start, end are Date objects
        """
        self.start, self.end = sorted([start, end])

    @property
    def total(self):
        return (self.end - self.start).total + 1

    def intersects(self, other):
        """
        True if self has common days with other
        """
        return not (self.end < other.start or self.start > other.end)

    def intersection(self, other):
        """
        returns a new DateRange which consists of the intersection of
        self with other DateRage. If the two ranges do not intersect
        it returns None
        """
        if not self.intersects(other):
            return None
        else:
            return DateRange(max(self.start, other.start),
                             min(max(self.start, self.end),
                                 max(other.start, other.end)))

    def split_intersection(self, other):
        """
        split a DateRange by injecting another DateRange into it.
        The return value is a list of 2 or 3 elements if the ranges intersect
        or 2 if not
        """
        if self == other:
            return [self]
        else:
            if self.start < other.start:
                r1, r2 = self, other
            else:
                r1, r2 = other, self
            inter = r1.intersection(r2)
            if inter:
                max_end = max(r1.end, r2.end)
                start = DateRange(r1.start, inter.start - DateInterval(1))
                end = DateRange(inter.end + DateInterval(1), max_end)
                valid = lambda r: r1.start <= r.start <= max_end and r1.start <= r.end <= max_end
                return [r for r in [start, inter, end] if valid(r)]
            else:
                return [r1, r2]

    def __repr__(self):
        return "[%s - %s]" % (self.start, self.end)

    def __eq__(self, other):
        """
        equal if same start and same end
        """
        return self.start == other.start and self.end == other.end

    def __ne__(self, other):
        """
        start or end differs
        """
        return self.start != other.start or self.end != other.end


def test():
    d01_03 = Date(2012, 3, 1)
    d30_03 = Date(2012, 3, 30)
    d20_03 = Date(2012, 3, 20)
    d20_04 = Date(2012, 4, 20)
    d01_02 = Date(2012, 2, 1)
    d10_03 = Date(2012, 3, 10)
    d01_01 = Date(2012, 1, 1)
    d01_05 = Date(2012, 5, 1)
    d10_03 = Date(2012, 3, 10)
    d20_03 = Date(2012, 3, 20)
    d20_04 = Date(2012, 4, 20)
    d30_05 = Date(2012, 5, 30)
    d20_01 = Date(2012, 1, 20)
    d20_02 = Date(2012, 2, 20)
    d01_03 = Date(2012, 3, 1)
    d20_04 = Date(2012, 4, 20)
    d10_03 = Date(2012, 3, 10)
    d30_03 = Date(2012, 3, 30)

    r0103_3003 = DateRange(d01_03, d30_03)
    r2003_2004 = DateRange(d20_03, d20_04)
    r0102_1003 = DateRange(d01_02, d10_03)
    r0101_0105 = DateRange(d01_01, d01_05)
    r1003_2003 = DateRange(d10_03, d20_03)
    r2003 = DateRange(d20_03, d20_03)
    r2004_3005 = DateRange(d20_04, d30_05)
    r2001_2002 = DateRange(d20_01, d20_02)

    r0103_2004 = DateRange(d01_03, d20_04)
    r1003_3003 = DateRange(d10_03, d30_03)

    assert str(r0103_3003.intersection(r2003_2004)) == "[20/3/2012 - 30/3/2012]"
    assert str(r0103_3003.intersection(r0102_1003)) == "[1/3/2012 - 10/3/2012]"
    assert str(r0103_3003.intersection(r0101_0105)) == "[1/3/2012 - 30/3/2012]"
    assert str(r0103_3003.intersection(r1003_2003)) == "[10/3/2012 - 20/3/2012]"
    assert not r0103_3003.intersects(r2004_3005)
    assert not r0103_3003.intersects(r2001_2002)
    assert str(r0103_3003.split_intersection(r0103_3003)) == "[[1/3/2012 - 30/3/2012]]"
    assert str(r0103_3003.split_intersection(r2003_2004)) == "[[1/3/2012 - 19/3/2012], [20/3/2012 - 30/3/2012], [1/4/2012 - 20/4/2012]]"
    assert str(r0103_3003.split_intersection(r0102_1003)) == "[[1/2/2012 - 30/2/2012], [1/3/2012 - 10/3/2012], [11/3/2012 - 30/3/2012]]"
    assert str(r0103_3003.split_intersection(r0101_0105)) == "[[1/1/2012 - 30/2/2012], [1/3/2012 - 30/3/2012], [1/4/2012 - 1/5/2012]]"
    assert str(r0103_3003.split_intersection(r1003_2003)) == "[[1/3/2012 - 9/3/2012], [10/3/2012 - 20/3/2012], [21/3/2012 - 30/3/2012]]"
    assert str(r0103_3003.split_intersection(r2004_3005)) == "[[1/3/2012 - 30/3/2012], [20/4/2012 - 30/5/2012]]"
    assert str(r0103_3003.split_intersection(r2001_2002)) == "[[20/1/2012 - 20/2/2012], [1/3/2012 - 30/3/2012]]"
    assert str(r0103_3003.split_intersection(r0103_2004)) == "[[1/3/2012 - 30/3/2012], [1/4/2012 - 20/4/2012]]"
    assert str(r0103_3003.split_intersection(r1003_3003)) == "[[1/3/2012 - 9/3/2012], [10/3/2012 - 30/3/2012]]"
    assert r2003.total == 1
    assert str(r2003.split_intersection(r2003_2004)) == "[[20/3/2012 - 20/3/2012], [21/3/2012 - 20/4/2012]]"

    print "tests pass"
