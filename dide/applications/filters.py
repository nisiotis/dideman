# -*- coding: utf-8 -*-
from dideman.dide.models import Application
from dideman.dide.overrides.admin import DideAdmin
from dideman.dide.overrides.admin import ModifierSimpleListFilter


class FinalisedFilter(ModifierSimpleListFilter):
    title = 'Οριστικοποιήθηκε'
    parameter_name = 'finalised'
    # Το modifier_name, το lookup_param και η καταχώρηση της παραμέτρου
    # γίνονται πλέον από το BaseModifierFilter.__init__.

    def lookups(self, request, model_admin):
        return  (('0', 'Όχι'),
                 ('1', 'Ναι'))

    def filter_param(self, queryset, query_dict):
        val = int(query_dict.get(self.parameter_name, 2))
        if val == 1:
            return queryset & queryset.model.objects.filter(
                datetime_finalised__isnull=False)
        elif val == 0:
            return queryset & queryset.model.objects.filter(
                datetime_finalised__isnull=True)
        else:
            return queryset

    def has_output(self):
        return True

    def used_params(self):
        return [self.parameter_name]
