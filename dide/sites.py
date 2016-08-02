from django.contrib.admin.sites import AdminSite
from dideman.dide.util.settings import SETTINGS

class DideAdminSite(AdminSite):
    
    @never_cache
    def index(self, request, extra_context=None):
        context = {

            'title': _('Site administration'),
            'app_list': super.app_list,
            'search_form': 'Search Form',

        }
        print "test"
        context.update(extra_context or {})
        #if request.POST:
        #    pass
        return TemplateResponse(request, [
            self.index_template or 'admin/index.html',
        ], context, current_app=self.name)


#dideadmin_site = DideAdminSite()


site = DideAdminSite()

