# Create your views here.
import collections
from itertools import groupby
from django.http import HttpResponse
from dideman.dide.models import Permanent, School, Profession
from dideman.dide.util.settings import SETTINGS
import json
import datetime

def permanent(request):
    try:
        if 'key' in request.GET and request.GET['key'] == SETTINGS['api_key']:
            qs = Permanent.objects.filter(currently_serves=True)
            data = {"data":
                    [{"registration_number": r.registration_number,
                      "lastname": r.lastname,
                      "firstname": r.firstname,
                      "fathername": r.fathername,
                      "payment_start_date": str(r.payment_start_date_auto()),
                      "total_service": str(r.total_service()),
                      "fek": r.order_hired} for r in qs],
                    "error": ""}
            return HttpResponse(json.dumps(data), mimetype='application/json')
        else:
            return HttpResponse(json.dumps({"data":[], "error": "invalid api key"}))
    except Exception as e:
        return HttpResponse(json.dumps({"data":[], "error": e.message}))

def schools(request):
    try:
        if 'key' in request.GET and request.GET['key'] == SETTINGS['api_key']:
            sch = School.objects.all().exclude(email__exact='')
            data = {"data":
                    [{"name": str(k.name),
                      "area": str(k.transfer_area),
                      "email": k.email,
                      "code": k.code} for k in sch],
                    "error": "" }

            return HttpResponse(json.dumps(data), content_type='application/json')
        else:
            return HttpResponse(json.dumps({"data":[], "error": "parameters error"}))
    except Exception as e:
        return HttpResponse(json.dumps({"data":[], "error": e.message}))

def schoolposts(request):
    try:
        if 'key' in request.GET and request.GET['key'] == SETTINGS['api_key']:
            sch_sector = []
            school_found = []
            pos = set(u.unique_identity for u in Profession.objects\
                      .exclude(unique_identity__isnull=True).exclude(unique_identity__exact=''))
            if request.GET['email'] != '':
                sch = School.objects.filter(email=request.GET['email'])
                if len(sch) > 0:
                    school_found = int(sch[0].id)
                    sch_sector = sch[0].transfer_area.name
                    
                else:
                    sch = None
            else:
                sch = None
            if request.GET['service'] == "organizational" and sch is not None:
                l = []
                prm = Permanent.objects.permanent_post_in_organization_api(school_found)\
                                   .filter(currently_serves=True)#, has_permanent_post=True)
                for o in prm:
                    try:
                        if o.permanent_post().date_to is not None:
                            if o.permanent_post().date_to < datetime.date(datetime.date.today().year, 9, 1):
                                l.append(o.id)
                    except Exception as err:
                        print(o)
                        print((type(err)))    # the exception type
                        print((err.args))     # arguments stored in .args
                        print(err) 
                prm = Permanent.objects.permanent_post_in_organization_api(school_found)\
                                   .filter(currently_serves=True).exclude(pk__in=l)
                
            elif request.GET['service'] == "operational" and sch is not None:
                prm = Permanent.objects.serving_in_organization_api(school_found)\
                                   .filter(currently_serves=True)
                                           #, has_permanent_post=True)
            else:
                prm = None
            if sch is not None and prm is not None:
                prm_prof = [p.parent.profession.unique_identity for p in prm]
                grp = collections.Counter(prm_prof) 
                prm_hrs = [(p.parent.profession.unique_identity, p.hours()) for p in prm] 
                prm_hrs.sort(key=lambda tup: tup[0])
                tot_hrs = {}
                total_hrs_sch = 0
                for key, group in groupby(prm_hrs, lambda x: x[0]):
                    tot = 0
                    for t in group:
                        tot += t[1]
                    tot_hrs[key] = tot
                    total_hrs_sch += tot
                
                json_grp = []
                total_prof_w_hrs = 0
                for item in pos:
                    if item in grp:
                        json_grp.append({"profession": item, "hours": tot_hrs[item], "count": grp.get(item)})
                        total_prof_w_hrs += 1
                    else:
                        json_grp.append({"profession": item, "hours": 0, "count": 0})

                data = {"data":
                    [{"profession": str(k['profession']),
                      "hours": k['hours'],
                      "count": k['count']} for k in json_grp],

                    "total-professions-with-hours": total_prof_w_hrs, 
                    "total-hours": total_hrs_sch,
                    "total-teachers": len(prm),
                    "year": datetime.datetime.today().year,
                    "sector": sch_sector,
                    "error": "" }

                return HttpResponse(json.dumps(data), content_type='application/json')
            else:
                return HttpResponse(json.dumps({"data":[], "error": "parameters error"}))

        else:
            return HttpResponse(json.dumps({"data":[], "error": "invalid api key"}))
    except Exception as e:
        return HttpResponse(json.dumps({"data":[], "error": e.message}))
