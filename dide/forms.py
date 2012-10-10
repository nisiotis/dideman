# -*- coding: utf-8 -*-
from django.forms.models import ModelForm
from dideman.dide.models import SubstitutePlacement, NonPermanent, PlacementType
from dideman.dide.util.common import current_year_date_to


class SubstitutePlacementForm(ModelForm):

    class Meta:
        model = SubstitutePlacement

    pltype = PlacementType.objects.get(pk=3)

    def _post_clean(self):
        super(SubstitutePlacementForm, self)._post_clean()
        self.instance.date_from = self.instance.ministry_order.date
        self.instance.date_to = current_year_date_to()
        self.instance.type = SubstitutePlacementForm.pltype
