# -*- coding: utf-8 -*-
import functools
from django.http import HttpResponseRedirect


def match_required(view_func):
    @functools.wraps(view_func)
    def decorated(request, *args, **kwargs):
        if 'matched_employee_id' in request.session:
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseRedirect('/employee/match')
    return decorated
