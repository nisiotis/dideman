# -*- coding: utf-8 -*-
"Decorators for caching methods and functions"

import inspect
import functools
import re

__all__ = ['memo_core_cache', 'memo_dict']

CACHE_ARGS = ['TIMEOUT', 'OPTIONS', 'MAX_ENTRIES', 'CULL_FREQUENCY',
              'KEY_PREFIX', 'VERSION', 'KEY_FUNCTION']


def create_decorator(klass):
    def dec(*args, **kwargs):
        if len(args) == 1 and len(kwargs.keys()) == 0:
            if callable(args[0]):
                return klass()(args[0])
        return klass(*args, **kwargs)
    return dec


class DjangoCoreCache(object):
    def __init__(self, *args, **kwargs):
        from django.core.cache import cache
        self.cache = cache
        self.params = {}
        self.params['version'] = 0
        self.params['timeout'] = None

        for k, v in kwargs.items():
            setattr(self, k, v)
            if k in CACHE_ARGS:
                self.params[k.lower()] = v

    def set(self, key, value):
        self.cache.set(key, value, timeout=self.params['timeout'],
                       version=self.params['version'])
        return self

    def get(self, key):
        return self.cache.get(key, version=self.params['version'])

    def clear(self):
        self.params['version'] += 1
        return self


class DictCache(object):

    def __init__(self):
        self.d = {}

    def get(self, key):
        return self.d.get(key, None)

    def set(self, key, value):
        self.d[key] = value
        return self

    def clear(self):
        self.d = {}
        return self


class MemoBase(object):

    def __init__(self, for_method=True, key_params=None, *args, **kwargs):
        key_params = key_params or []
        self.for_method = for_method
        self.key_params = key_params
        self.fn = None
        self.prefix = None

        for k, v in kwargs.items():
            setattr(self, k, v)

    def _init_prefix(self, obj=None):
        if self.for_method:
            key_params = [self.fn.__module__, obj.__class__.__name__,
                          self.fn.__name__]
        else:
            key_params = [self.fn.__module__, self.fn.__name__]
        self.prefix = ".".join(key_params)

    def __call__(self, fn):
        self.fn = fn
        fn.clear_cache = self.clear

        @functools.wraps(fn)
        def _dec(*args, **kwargs):
            calldict = inspect.getcallargs(fn, *args, **kwargs)
            values = map(calldict.get, self.key_params)
            if not self.prefix:
                self._init_prefix(args[0] if self.for_method else None)
            key = self.prefix + ".".join([str(hash(x)) for x in values])
            val = self.cache.get(key)
            if val is None:
                val = fn(*args, **kwargs)
                self.cache.set(key, val)
            return val
        return _dec

    def clear(self):
        self.cache.clear()
        return self


class MemoDict(MemoBase):

    def __init__(self, *args, **kwargs):
        self.cache = DictCache()
        super(MemoDict, self).__init__(*args, **kwargs)


class MemoDjangoCore(MemoBase):

    def __init__(self, *args, **kwargs):
        cache_kwds = {arg: kwargs[arg] for arg in CACHE_ARGS if arg in kwargs}
        self.cache = DjangoCoreCache(**cache_kwds)
        super(MemoDjangoCore, self).__init__(*args, **kwargs)

memo_core_cache = create_decorator(MemoDjangoCore)
memo_dict = create_decorator(MemoDict)


def test():
    import django
    import sys
    import os
    import time
    sys.path.append('/home/sstergou/project/')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'dideman.settings'

    dcc = DjangoCoreCache(TIMEOUT=60 * 60 * 24)
    assert dcc.set("key", 111).get("key") == 111

    dcc = DjangoCoreCache(TIMEOUT=1)
    dcc.set("key", 1)
    time.sleep(1)
    assert dcc.get("key") is None
    assert dcc.set("key", 1).clear().get("key") is None

    dc = DictCache()
    assert dc.get("key") == None
    assert dc.set("key", 1).get("key") == 1
    assert dc.clear().d == {}

    class A(object):

        @MemoDict(for_method=True, key_params=['a', 'b'])
        def method(self, a, b, c):
            return a + b + c

    a = A()
    assert a.method(1, 2, 3) == 6
    assert a.method(1, 2, 4) == 6
    a.method.clear_cache()
    assert a.method(1, 2, 4) == 7

    class B(object):

        @MemoDjangoCore(for_method=True, key_params=['a', 'b'],
                        KEY_PREFIX='ab', TIMEOUT=1)
        def method(self, a, b, c):
            return a + b + c

    b = B()
    assert b.method(1, 2, 3) == 6
    assert b.method(1, 2, 4) == 6
    b.method.clear_cache()
    assert b.method(1, 2, 4) == 7
    time.sleep(1)
    assert b.method(1, 2, 5) == 8

    @MemoDict(for_method=False, key_params=['a', 'b'])
    def f(a, b, c):
        return a + b + c

    assert f(1, 2, 3) == 6
    assert f(1, 2, 4) == 6
    f.clear_cache()
    assert f(1, 2, 4) == 7

    @MemoDict(for_method=False)
    def g():
        print "computing"
        return 1

    assert g() == 1

    # this call should not print anything!
    assert g() == 1

    print "success!"
