# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from models import (RankCode, PaymentFileName, PaymentCategoryTitle,
                    PaymentReportType, PaymentCode)


class Command(BaseCommand):
    args = '<file ...>'

    def handle(self, *args, **options):
        for f in args:
            try:
                pf = PaymentFileName.objects.get(xml_file=f)
                pf.status = 0
            except PaymentFileName.DoesNotExist:
                raise CommandError(u'. ' % f)
