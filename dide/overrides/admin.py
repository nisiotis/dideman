# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.admin.filters import (SimpleListFilter, FieldListFilter,
                                          RelatedFieldListFilter,
                                          BooleanFieldListFilter,
                                          ChoicesFieldListFilter,
                                          AllValuesFieldListFilter)
from django.http import QueryDict
from django.utils.datastructures import MultiValueDict
from django.conf.urls import patterns, url
from dideman.dide.util.settings import SETTINGS
from django.utils.http import urlencode
import django.contrib.admin.views.main as views
from django.contrib.admin.util import unquote, get_deleted_objects
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils.translation import ugettext as _
from django.db import router
from dideman.lib.common import parse_deletable_list
from django.utils.encoding import force_unicode
from django.utils.html import escape


class DideAdmin(admin.ModelAdmin):

    class Media:
        css = {'all': ('css/dide-admin.css', )}

    filter_parameters = []
    all_filters = tuple()

    def delete_view(self, request, object_id, extra_context=None):
        # overrided delete_view method
        opts = self.model._meta
        obj = self.get_object(request, unquote(object_id))
        if not self.has_delete_permission(request, obj):
            raise PermissionDenied
        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})
        using = router.db_for_write(self.model)

        # Populate deleted_objects, a data structure of all related objects that
        # will also be deleted.
        (deleted_objects, perms_needed, protected) = get_deleted_objects(
            [obj], opts, request.user, self.admin_site, using)
        new_deletable_objects = parse_deletable_list(deleted_objects)
        extra_context = {'deleted_objects': [new_deletable_objects]}

        return super(DideAdmin, self).delete_view(request,
                                                  object_id,
                                                  extra_context)

    def get_extra_context(self, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update({'dide_place': SETTINGS['dide_place']})
        return extra_context

    def __init__(self, *args, **kwargs):
        super(DideAdmin, self).__init__(*args, **kwargs)

    def lookup_allowed(self, key, value):
        return key in DideAdmin.filter_parameters or \
            super(DideAdmin, self).lookup_allowed(key, value)

    def get_urls(self):
        url_patterns = patterns('',
                                url('filters/$',
                                    'dideman.%s.views.filters.%s' % (self.model._meta.app_label, self.model._meta.module_name)))
        return url_patterns + super(DideAdmin, self).get_urls()

    def changelist_view(self, request, extra_context=None):
        return super(DideAdmin, self).\
            changelist_view(request, self.get_extra_context(extra_context))

    @classmethod
    def add_filter_parameter(cls, filter_name):
        DideAdmin.filter_parameters.append(filter_name)


OLD_IGNORED_PARAMS = views.__dict__['IGNORED_PARAMS']
views.__dict__['IGNORED_PARAMS'] = \
    list(views.__dict__['IGNORED_PARAMS']) + ['full_filters']


def monkey_patch_method(cls, name, fn):
    #takes a class a name and a function (fn) as parameters
    #fn takes as a parameter the method named name and returns
    #a new function which replaces the old method
    method = fn(getattr(cls, name))
    setattr(cls, name, method)


def alter_get_query_string(fn):
    def get_query_string(self, new_params=None, remove=None, multi=None):
        if new_params is None:
            new_params = {}
        if remove is None:
            remove = []
        p = MultiValueDict(self.param_lists)
        for r in remove:
            for k in p.keys():
                if k.startswith(r):
                    del p[k]
        for k, v in new_params.items():
            if v is None:
                if k in p:
                    del p[k]
            else:
                p[k] = v
        return '?%s' % urlencode(p, 1)
    return get_query_string


def alter_changelist_constructor(fn):
    def __init__(self, request, model, list_display, list_display_links,
                 list_filter, date_hierarchy, search_fields,
                 list_select_related, list_per_page, list_max_show_all,
                 list_editable, model_admin):
        fn(self, request, model, list_display, list_display_links,
           list_filter, date_hierarchy, search_fields, list_select_related,
           list_per_page, list_max_show_all, list_editable, model_admin)
        self.request = request
        self.param_lists = {}
        for l in request.GET.lists():
            key, val = l
            if key not in OLD_IGNORED_PARAMS:
                self.param_lists[key] = val
    return __init__


def alter_choices(fn):
    def choices(self, cl):
        gen = fn(self, cl)
        yield gen.next()
        while 1:
            choice = gen.next()
            GET_qd = cl.request.GET.copy()
            GET_lookup_param_list = GET_qd.getlist(self.lookup_param, [])
            parent_qd = QueryDict(choice['query_string'][1:]).copy()
            parent_qd_value = parent_qd.get(self.lookup_param, None)
            if self.modifier_value == 'OR':
                if parent_qd_value in GET_lookup_param_list:
                    GET_lookup_param_list.remove(parent_qd_value)
                else:
                    GET_lookup_param_list.append(parent_qd_value)
                if not GET_lookup_param_list:
                    del GET_qd[self.lookup_param]
            else:
                if self.lookup_param  in GET_lookup_param_list:
                    del GET_qd[self.lookup_param]
                GET_lookup_param_list = [parent_qd_value]
            GET_qd.setlist(self.lookup_param, GET_lookup_param_list)
            choice['query_string'] = '?%s' % GET_qd.urlencode()
            choice['selected'] = parent_qd_value and \
                parent_qd_value in cl.request.GET. \
                getlist(self.lookup_param, [])
            yield choice
    return choices


def alter_filter_constructor(fn):
    def __init__(self, field, request, params, model, model_admin,
                 field_path, *args, **kwargs):
        fn(self, field, request, params, model, model_admin,
           field_path, *args, **kwargs)
        self.lookup_param = self.lookup_kwarg
        self.modifier_name = '_m_' + self.lookup_param
        self.modifier_value = request.GET.get(self.modifier_name, u'AND')
        views.__dict__['IGNORED_PARAMS'].append(self.modifier_name)
    return __init__


class BaseModifierFilter(object):
    template_name = 'filter'
    registered_filters = []
    list_view = True

    def __init__(self, *args, **kwargs):
        super(BaseModifierFilter, self).__init__(*args, **kwargs)
        BaseModifierFilter.registered_filters.append(self)

    def filter_param(self, queryset, query_dict):
        return queryset.filter(**query_dict)

    def list_filter_context(self, cl):
        return {'title': self.title, 'choices': list(self.choices(cl)),
                'modifiers': self.modifiers(cl)}

    def modifiers(self, cl):
        GET_qd = cl.request.GET.copy()
        GET_qd[self.modifier_name] = 'AND'
        qs_and = '?%s' % GET_qd.urlencode()
        GET_qd[self.modifier_name] = 'OR'
        qs_or = '?%s' % GET_qd.urlencode()
        modifier_and = {
           'selected': self.modifier_value == 'AND',
           'query_string': qs_and,
           'display': u'Αποκλεισμός',
        }
        modifier_or = {
            'selected': self.modifier_value == 'OR',
            'query_string': qs_or,
            'display': u'Σύνθεση',
        }
        return [modifier_and, modifier_or]

    def queryset(self, request, queryset):
        query_dict = {}
        params = dict(request.GET.items())
        for p in self.expected_parameters():
            if p in params:
                query_dict[p] = params[p]
        if self.modifier_value != u'OR':
            return self.filter_param(queryset, query_dict)
        else:
            try:
                for param in self.expected_parameters():
                    del query_dict[param]
            except KeyError:
                pass
            queryset = self.filter_param(queryset, query_dict)
            qs = queryset
            is_first = True
            for param in self.expected_parameters():
                get_values = dict(request.GET.lists()).get(param, [])
                if get_values:
                    for value in get_values:
                        if is_first:
                            is_first = False
                            qs = self.filter_param(queryset,
                                                   {param: get_values[0]})
                        else:
                            qs = qs | self.filter_param(queryset,
                                                        {param: value})
        return qs


class ModifierFieldListFilter(BaseModifierFilter, FieldListFilter):
    def __init__(self, field, request, params, *args, **kwargs):
        super(ModifierFieldListFilter, self).__init__(field,
                                                      request, params,
                                                      *args, **kwargs)
        FieldListFilter.queryset = BaseModifierFilter.queryset


class ModifierSimpleListFilter(BaseModifierFilter, SimpleListFilter):
    def __init__(self, request, params, *args, **kwargs):
        super(ModifierSimpleListFilter, self).__init__(request,
                                                       params, *args, **kwargs)

RelatedFieldListFilter.__bases__ = (ModifierFieldListFilter, )
BooleanFieldListFilter.__bases__ = (ModifierFieldListFilter, )
ChoicesFieldListFilter.__bases__ = (ModifierFieldListFilter, )
AllValuesFieldListFilter.__bases__ = (ModifierFieldListFilter, )

monkey_patch_method(RelatedFieldListFilter, 'choices', alter_choices)
monkey_patch_method(BooleanFieldListFilter, 'choices', alter_choices)
setattr(BooleanFieldListFilter, 'lookup_choices', ((None, u'Όλα'),
                                                   ('1', u'Ναι'),
                                                   ('0', u'Όχι')))
monkey_patch_method(ChoicesFieldListFilter, 'choices', alter_choices)
monkey_patch_method(AllValuesFieldListFilter, 'choices', alter_choices)
monkey_patch_method(SimpleListFilter, 'choices', alter_choices)


monkey_patch_method(RelatedFieldListFilter, '__init__',
                    alter_filter_constructor)
monkey_patch_method(BooleanFieldListFilter, '__init__',
                    alter_filter_constructor)
monkey_patch_method(ChoicesFieldListFilter, '__init__',
                    alter_filter_constructor)
monkey_patch_method(AllValuesFieldListFilter, '__init__',
                    alter_filter_constructor)
monkey_patch_method(views.ChangeList, '__init__', alter_changelist_constructor)
monkey_patch_method(views.ChangeList, 'get_query_string', alter_get_query_string)
