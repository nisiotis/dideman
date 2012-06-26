# -*- coding: utf-8 -*-
from dideman.dide.models import Application
from dideman.dide.overrides.admin import DideAdmin
from dideman.dide.overrides.admin import ModifierSimpleListFilter
import django.contrib.admin.views.main as views


class FinalisedFilter(ModifierSimpleListFilter):
    title = u'Οριστικοποιήθηκε'
    parameter_name = 'finalised'
    modifier_name = '_m_' + parameter_name
    lookup_param = parameter_name
    views.__dict__['IGNORED_PARAMS'] += [modifier_name]
    DideAdmin.add_filter_parameter(parameter_name)

    def __init__(self, request, params, model, model_admin, *args, **kwargs):
        self.modifier_value = request.GET.get(self.modifier_name, u'AND')
        super(FinalisedFilter, self).__init__(request, params, model,
                                                    model_admin)

    def lookups(self, request, model_admin):
        return  (('0', u'Όχι'),
                 ('1', u'Ναι'))

    def filter_param(self, queryset, query_dict):
        val = int(query_dict.get(self.parameter_name, 2))
        if val == 1:
            return queryset & Application.objects.filter(
                datetime_finalised__isnull=False)
        elif val == 0:
            return queryset & Application.objects.filter(
                datetime_finalised__isnull=True)
        else:
            return queryset

    def has_output(self):
        return True

    def used_params(self):
        return [self.parameter_name]
