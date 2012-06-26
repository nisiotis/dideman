from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from dideman.dide.applications.decorators import match_required
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^applications/match/(?P<set_id>\d+)/$',
        'dideman.dide.applications.views.match'),
    url(r'^applications/edit/(?P<set_id>\d+)/$',
        'dideman.dide.applications.views.edit'),
)
