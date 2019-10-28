from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from dideman.dide.employee.decorators import match_required
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/dide/nonpermanent/list/$', 'dideman.dide.views.views.nonpermanent_list'),
    url(r'^admin/dide/geoschool/$', 'dideman.dide.views.views.school_geo_view'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/permanent/', 'dideman.api.views.permanent'),
    url(r'^api/schoolposts/', 'dideman.api.views.schoolposts'),

    url(r'^employee/help/',
        'dideman.dide.employee.match.help'),
    url(r'^salary/help/',
        'dideman.dide.salary.views.help'),
    url(r'^employee/match/$',
        'dideman.dide.employee.match.match'),
    url(r'^applications/edit/(?P<set_id>\d+)/$',
        'dideman.dide.applications.views.edit'),
    url(r'^salary/view/$',
        'dideman.dide.salary.views.view'),
    url(r'^myinfo/edit/$',
        'dideman.dide.myinfo.views.edit'),
    url(r'^$',
        'dideman.dide.menu.views.menu'),
    url(r'^salary/view/showpdf/$',
        'dideman.dide.salary.views.showpdf'),
)
