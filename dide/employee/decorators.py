# -*- coding: utf-8 -*-
import functools
from django.http import HttpResponseRedirect
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils.http import urlencode


def match_required(view_func):
    @functools.wraps(view_func)
    def decorated(request, *args, **kwargs):
        if 'matched_employee_id' in request.session:
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(
                '/employee/match/?next=%s' % request.get_full_path())
    return decorated
