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


def try_many(*exps, **kwargs):
    """
    Takes a series of lambda expressions and tries to evaluate them in a try-
    except context. If one of them succeeds then it returns its value.
    If all of them raise exceptions then it returns a default value, if
    provided, else it raises the last exception.
    """
    for e in exps:
        try:
            return e()
        except Exception, error:
            continue
    if 'default' in kwargs:
        return kwargs['default']
    else:
        raise error

callable = callable or (lambda o: hasattr(o, '__call__'))


def _compose(f, g, unpack=False):
    assert callable(f)
    assert callable(g)

    if unpack:
        def composition(*args, **kwargs):
            return f(*g(*args, **kwargs))
    else:
        def composition(*args, **kwargs):
            return f(g(*args, **kwargs))
    return composition


def compose(*args):
    return functools.reduce(_compose, args)
