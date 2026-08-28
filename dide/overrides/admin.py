# -*- coding: utf-8 -*-
"""Φίλτρα admin με πολλαπλή επιλογή και τελεστή AND/OR.

Το στάνταρ admin δέχεται μία τιμή ανά φίλτρο και τις συνδυάζει πάντα με
AND. Εδώ κάθε φίλτρο αποκτά πολλαπλές τιμές για την ίδια παράμετρο και
μια συνοδό παράμετρο ``_m_<param>`` με τιμή ``AND`` ή ``OR`` που ελέγχει
πώς συνδυάζονται.

Η προηγούμενη υλοποίηση το πετύχαινε με έξι monkey patches πάνω σε
ιδιωτικά εσωτερικά του Django: ανάθεση ``__bases__`` στις built-in
κλάσεις φίλτρων, αντικατάσταση του ``choices()``, patch στον constructor
και στο ``get_query_string`` του ``ChangeList``, και μετάλλαξη του
module-level ``IGNORED_PARAMS``. Κανένα δεν χρειάζεται πλέον:

* ``ChangeList.filter_params`` είναι ήδη ``dict(request.GET.lists())`` και
  το ``get_query_string`` κάνει ``urlencode(..., doseq=True)``, οπότε οι
  πολλαπλές τιμές υποστηρίζονται από το ίδιο το Django.
* Το ``expected_parameters()`` είναι ο επίσημος τρόπος να δηλώσει ένα
  φίλτρο ποιες παραμέτρους καταναλώνει — αντικαθιστά το ``IGNORED_PARAMS``.
* Το ``FieldListFilter.register(..., take_priority=True)`` είναι ο
  επίσημος τρόπος να αντικατασταθεί το φίλτρο ενός τύπου πεδίου —
  αντικαθιστά την ανάθεση ``__bases__``.
"""
from django.contrib import admin
from django.contrib.admin.filters import (AllValuesFieldListFilter,
                                          BooleanFieldListFilter,
                                          ChoicesFieldListFilter,
                                          FieldListFilter,
                                          RelatedFieldListFilter,
                                          SimpleListFilter)
from django.contrib.admin.utils import get_deleted_objects, unquote
from django.core.exceptions import PermissionDenied
from django.db import models
from django.http import Http404
from django.urls import path
from django.utils.encoding import force_str
from django.utils.html import escape
from django.utils.translation import gettext as _

from dideman.dide.util.settings import SETTINGS
from dideman.lib.common import parse_deletable_list

AND = 'AND'
OR = 'OR'


class DideAdmin(admin.ModelAdmin):

    class Media:
        css = {'all': ('css/dide-admin.css', )}

    filter_parameters = []
    all_filters = tuple()

    def delete_view(self, request, object_id, extra_context=None):
        opts = self.model._meta
        obj = self.get_object(request, unquote(object_id))
        if not self.has_delete_permission(request, obj):
            raise PermissionDenied
        if obj is None:
            raise Http404(
                _('%(name)s object with primary key %(key)r does not exist.')
                % {'name': force_str(opts.verbose_name),
                   'key': escape(object_id)})

        # Από το Django 2.1 η get_deleted_objects παίρνει (objs, request,
        # admin_site) και επιστρέφει τέσσερις τιμές αντί για τρεις.
        deleted_objects, model_count, perms_needed, protected = \
            get_deleted_objects([obj], request, self.admin_site)
        extra_context = dict(extra_context or {})
        extra_context['deleted_objects'] = [parse_deletable_list(deleted_objects)]

        return super().delete_view(request, object_id, extra_context)

    def get_extra_context(self, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update({'dide_place': SETTINGS['dide_place']})
        return extra_context

    def lookup_allowed(self, lookup, value, request=None):
        # Το request προστέθηκε στην υπογραφή στο Django 5.0.
        if lookup in DideAdmin.filter_parameters:
            return True
        return super().lookup_allowed(lookup, value, request)

    def get_urls(self):
        """Προσθέτει το popup «Αναλυτικά» όπου υπάρχει αντίστοιχη view."""
        opts = self.model._meta
        try:
            module = __import__('dideman.%s.views.filters' % opts.app_label,
                                fromlist=['filters'])
            view = getattr(module, opts.model_name)
        except (ImportError, AttributeError):
            return super().get_urls()
        return [path('filters/', view)] + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        return super().changelist_view(request,
                                       self.get_extra_context(extra_context))

    @classmethod
    def add_filter_parameter(cls, filter_name):
        if filter_name not in DideAdmin.filter_parameters:
            DideAdmin.filter_parameters.append(filter_name)


class BaseModifierFilter:
    """Πολλαπλή επιλογή και τελεστής AND/OR για ένα φίλτρο.

    Χρησιμοποιείται ως mixin *πριν* από την κλάση φίλτρου του Django,
    ώστε τα ``queryset()`` και ``choices()`` του να υπερισχύουν.
    """

    template = 'admin/filter.html'
    # Το custom_admin.is_free_date_filter διακρίνει τα φίλτρα από αυτό.
    template_name = 'filter'
    list_view = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        DideAdmin.add_filter_parameter(self.lookup_param)

    # Υπολογίζονται κατ' απαίτηση και όχι στον constructor: το
    # FieldListFilter.__init__ καλεί expected_parameters() πριν επιστρέψει
    # η super(), οπότε τότε δεν θα υπήρχαν ακόμη ως attributes.
    @property
    def lookup_param(self):
        """Το SimpleListFilter δηλώνει parameter_name, το FieldListFilter
        lookup_kwarg."""
        return getattr(self, 'parameter_name', None) or self.lookup_kwarg

    @property
    def modifier_name(self):
        return '_m_' + self.lookup_param

    @property
    def modifier_value(self):
        return self.request.GET.get(self.modifier_name, AND)

    def expected_parameters(self):
        # Δηλώνει στο ChangeList ότι το _m_… ανήκει σε αυτό το φίλτρο,
        # χωρίς να πειραχθεί το IGNORED_PARAMS.
        return list(super().expected_parameters()) + [self.modifier_name]

    def consume_modifier_param(self, params):
        """Αφαιρεί το «_m_…» από τα params που θα φτάσουν στο ORM.

        Χρειάζεται μόνο όπου η βάση δεν το κάνει ήδη (SimpleListFilter).
        """
        name = self.modifier_name
        if name in params:
            self.used_parameters[name] = params.pop(name)

    def selected_values(self):
        return self.request.GET.getlist(self.lookup_param)

    def get_filter_choices(self):
        """Οι διαθέσιμες επιλογές, όπως τις ονομάζει κάθε κλάση βάσης.

        Τα Related/AllValues/Boolean φίλτρα εκθέτουν lookup_choices· το
        ChoicesFieldListFilter αντλεί από το flatchoices του πεδίου.
        """
        choices = getattr(self, 'lookup_choices', None)
        if choices is None:
            choices = self.field.flatchoices
        return choices

    # -- φιλτράρισμα ----------------------------------------------------

    def filter_param(self, queryset, query_dict):
        """Εφαρμόζει μία επιλογή· οι υποκλάσεις το αντικαθιστούν."""
        return queryset.filter(**query_dict)

    def queryset(self, request, queryset):
        values = self.selected_values()
        if not values:
            return self.filter_param(queryset, {})

        if self.modifier_value != OR:
            # AND: όπως και πριν, μετράει η τελευταία τιμή.
            return self.filter_param(queryset, {self.lookup_param: values[-1]})

        result = None
        for value in values:
            qs = self.filter_param(queryset, {self.lookup_param: value})
            result = qs if result is None else (result | qs)
        return result

    # -- εμφάνιση -------------------------------------------------------

    def modifiers(self, changelist):
        return [
            {'selected': self.modifier_value == AND,
             'query_string': changelist.get_query_string({self.modifier_name: AND}),
             'display': 'Αποκλεισμός'},
            {'selected': self.modifier_value == OR,
             'query_string': changelist.get_query_string({self.modifier_name: OR}),
             'display': 'Σύνθεση'},
        ]

    def list_filter_context(self, changelist):
        return {'title': self.title,
                'choices': list(self.choices(changelist)),
                'modifiers': self.modifiers(changelist)}

    def choices(self, changelist):
        """Με τελεστή OR κάθε επιλογή λειτουργεί ως toggle."""
        selected = self.selected_values()
        yield {
            'selected': not selected,
            'query_string': changelist.get_query_string(remove=[self.lookup_param]),
            'display': _('All'),
        }
        for lookup, title in self.get_filter_choices():
            lookup = str(lookup)
            is_selected = lookup in selected
            if self.modifier_value == OR:
                values = ([v for v in selected if v != lookup] if is_selected
                          else selected + [lookup])
            else:
                values = [] if is_selected else [lookup]
            yield {
                'selected': is_selected,
                'query_string': changelist.get_query_string(
                    {self.lookup_param: values or None}),
                'display': title,
            }


class ModifierSimpleListFilter(BaseModifierFilter, SimpleListFilter):

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)
        # Το FieldListFilter του Django αφαιρεί από τα params όλα τα
        # expected_parameters()· το SimpleListFilter αφαιρεί μόνο το
        # parameter_name. Χωρίς αυτό το «_m_…» έμενε στα
        # remaining_lookup_params, το ChangeList το περνούσε στο ORM ως όνομα
        # πεδίου και το φιλτράρισμα έσκαγε με FieldError -> ανακατεύθυνση σε
        # «?e=1». Δηλαδή ο τελεστής «Σύνθεση» δεν δούλευε ποτέ σε αυτά τα
        # φίλτρα — ούτε από την πλαϊνή στήλη ούτε από το popup «Αναλυτικά».
        self.consume_modifier_param(params)

    def has_output(self):
        return True


class ModifierFieldListFilter(BaseModifierFilter, FieldListFilter):
    """Βάση για τα φίλτρα πεδίων."""


class ModifierRelatedFieldListFilter(BaseModifierFilter, RelatedFieldListFilter):
    pass


class ModifierBooleanFieldListFilter(BaseModifierFilter, BooleanFieldListFilter):
    lookup_choices = (('1', 'Ναι'), ('0', 'Όχι'))


class ModifierChoicesFieldListFilter(BaseModifierFilter, ChoicesFieldListFilter):
    pass


class ModifierAllValuesFieldListFilter(BaseModifierFilter, AllValuesFieldListFilter):

    def get_filter_choices(self):
        # Εδώ το lookup_choices είναι επίπεδη λίστα τιμών του πεδίου και
        # όχι ζεύγη (τιμή, ετικέτα) όπως στα υπόλοιπα φίλτρα.
        return [(value, value) for value in self.lookup_choices
                if value is not None and value != '']


def _plain_field(field):
    """Πεδίο που, χωρίς δική μας δήλωση, θα κατέληγε στο AllValues.

    Τα υπόλοιπα (σχέσεις, boolean, choices, ημερομηνίες) έχουν ήδη δικό
    τους φίλτρο, οπότε δεν πρέπει να τα αρπάξει ο γενικός κανόνας.
    """
    return not (field.choices
                or field.remote_field is not None
                or isinstance(field, (models.BooleanField, models.DateField)))


# Αντί για ανάθεση __bases__ στις κλάσεις του Django, δηλώνονται κανονικά ως
# προτιμώμενα φίλτρα για τους αντίστοιχους τύπους πεδίων. Η σειρά έχει
# σημασία: με take_priority=True μπαίνουν στην αρχή της λίστας *με τη σειρά
# δήλωσης* και ελέγχεται ο πρώτος που ταιριάζει, οπότε ο γενικός κανόνας
# (AllValues) δηλώνεται τελευταίος.
FieldListFilter.register(lambda f: bool(f.choices),
                         ModifierChoicesFieldListFilter, take_priority=True)
FieldListFilter.register(lambda f: isinstance(f, models.BooleanField),
                         ModifierBooleanFieldListFilter, take_priority=True)
FieldListFilter.register(lambda f: f.remote_field is not None,
                         ModifierRelatedFieldListFilter, take_priority=True)
FieldListFilter.register(_plain_field,
                         ModifierAllValuesFieldListFilter, take_priority=True)
