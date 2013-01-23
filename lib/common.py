# -*- coding: utf-8 -*-

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


def get_class(name):
    arr = name.split('.')
    m = __import__('.'.join(arr[:-1]), fromlist=['none'])
    return getattr(m, arr[-1:][0])
