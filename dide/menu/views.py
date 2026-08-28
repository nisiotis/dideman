# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.contrib import messages

from dideman.dide.models import (ApplicationSet)
import datetime
import os


_template_path = 'menu' + os.path.sep


def menu(request):
    today = datetime.date.today()
    set = ApplicationSet.objects.filter(end_date__gte=today, start_date__lte=today)
    if 'logout' in request.GET:
        request.session.clear()
        messages.info(request, 'Αποσυνδεθήκατε με επιτυχία. Σε περίπτωση που χρησιμοποιήσατε έναν δημόσιο ηλεκτρονικό υπολογιστή, παρακαλούμε κλείστε το πρόγραμμα περιήγησης (browser).')
    # Το 'messages' έρχεται από τον context processor. Στο παλιό Django ο
    # RequestContext έβαζε τους processors *πάνω* από το λεξικό του view,
    # οπότε το module εδώ σκιαζόταν· τώρα ισχύει το αντίστροφο.
    return render(request, _template_path + 'menu.html', {'app': set})
