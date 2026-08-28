"""URL configuration.

Το ``patterns()`` και οι views δηλωμένες ως συμβολοσειρές αφαιρέθηκαν στο
Django 1.10: το urlpatterns είναι πλέον απλή λίστα και κάθε view δίνεται
ως callable, οπότε ένα λάθος όνομα φαίνεται στο import και όχι στο πρώτο
request.
"""
from django.contrib import admin
from django.urls import include, re_path

from dideman.api import views as api_views
from dideman.dide.applications import views as application_views
from dideman.dide.employee import match as employee_match
from dideman.dide.menu import views as menu_views
from dideman.dide.myinfo import views as myinfo_views
from dideman.dide.salary import views as salary_views
from dideman.dide.views import views as dide_views

admin.autodiscover()

# Δηλώνονται ως callables· ως συμβολοσειρές δεν υποστηρίζονται πια, και
# έδειχναν σε dideman.dide.views.handler404 που δεν υπάρχει — οι
# συναρτήσεις βρίσκονται στο views/views.py.
handler404 = dide_views.handler404
handler500 = dide_views.handler500

urlpatterns = [
    re_path(r'^admin/dide/photo/(?P<emp_id>\d+)/$', dide_views.photo),
    re_path(r'^admin/dide/photo_edit/(?P<emp_id>\d+)/$', dide_views.photo_update),
    re_path(r'^admin/dide/nonpermanent/list/$', dide_views.nonpermanent_list),
    re_path(r'^admin/dide/importexport/$', dide_views.import_export_view),
    re_path(r'^admin/dide/importexport/export/$', dide_views.export_view),
    re_path(r'^admin/dide/duplicates/$', dide_views.duplicate_employees_view),
    re_path(r'^admin/dide/geoschool/$', dide_views.school_geo_view),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^api/permanent/', api_views.permanent),
    re_path(r'^api/schoolposts/', api_views.schoolposts),
    re_path(r'^api/schools/', api_views.schools),
    re_path(r'^employee/help/', employee_match.help),
    re_path(r'^salary/help/', salary_views.help),
    re_path(r'^employee/match/$', employee_match.match),
    re_path(r'^applications/edit/(?P<set_id>\d+)/$', application_views.edit),
    re_path(r'^salary/view/$', salary_views.view),
    re_path(r'^myinfo/edit/$', myinfo_views.edit),
    re_path(r'^myinfo/edit/photo/(?P<emp_id>\d+)/$', myinfo_views.myphoto),
    re_path(r'^myinfo/edit/photo_edit/(?P<emp_id>\d+)/$', myinfo_views.myphoto_update),
    re_path(r'^$', menu_views.menu),
    re_path(r'^salary/view/showpdf/$', salary_views.showpdf),
]
