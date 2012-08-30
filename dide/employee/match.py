# -*- coding: utf-8 -*-
from dideman.dide.employee.forms import EmployeeMatchForm
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import  HttpResponseRedirect


def match(request):
    if request.method == 'POST':
        form = EmployeeMatchForm(request)
        if form.is_valid():
            id = form.get_employee().id
            request.session['matched_employee_id'] = id
            return HttpResponseRedirect(request.POST.get('next'))
    else:
        form = EmployeeMatchForm()
    request.session.set_test_cookie()
    return render_to_response('employee/match.html',
                              RequestContext(request,
                                             {'form': form,
                                              'next':
                                                  request.GET.get('next')}))
