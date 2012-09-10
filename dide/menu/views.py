# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response, render
from django.http import HttpResponse, HttpResponseRedirect
from dideman.dide.models import (ApplicationSet) 
from dideman.dide.util.settings import SETTINGS                                 
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect
from django.db.models.loading import get_model

from dideman import settings

import datetime
import os


_template_path = 'menu' + os.path.sep

def menu(request):
    today = datetime.date.today()
    set = ApplicationSet.objects.filter(end_date__gte=today)
    return render_to_response(_template_path + 'menu.html', 
                              RequestContext(request, {'app': set}))
