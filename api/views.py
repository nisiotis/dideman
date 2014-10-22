# Create your views here.
from django.http import HttpResponse
from dideman.dide.models import Permanent
from dideman.dide.util.settings import SETTINGS
import json

def permanent(request):
    try:
        if 'key' in request.GET and request.GET['key'] == SETTINGS['api_key']:
            qs = Permanent.objects.filter(currently_serves=True)
            data = {"data":
                    [{"registration_number": r.registration_number,
                      "lastname": r.lastname,
                      "firstname": r.firstname,
                      "fathername": r.fathername,
                      "payment_start_date": unicode(r.payment_start_date_auto()),
                      "fek": r.order_hired} for r in qs],
                    "error": ""}
            return HttpResponse(json.dumps(data), mimetype='application/json')
        else:
            return HttpResponse(json.dumps({"data":[], "error": "invalid api key"}))
    except Exception as e:
        return HttpResponse(json.dumps({"data":[], "error": e.message}))
