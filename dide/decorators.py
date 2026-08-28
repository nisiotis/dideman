# -*- coding: utf-8 -*-
import functools
from django.http import HttpResponseRedirect


def shorted(length):
    def dec(fn):
        @functools.wraps(fn)
        def _dec(*args, **kwargs):
            s = str(fn(*args, **kwargs))
            if len(s) <= length:
                return s
            else:
                return s[:length] + '...'
        return _dec
    return dec


def match_required(view_func):
    @functools.wraps(view_func)
    def decorated(request, *args, **kwargs):
        if 'matched_employee_id' in request.session:
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseRedirect('/employee/match')
    return decorated
