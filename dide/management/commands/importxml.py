# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from dide.models import (RankCode, PaymentFileName, PaymentCategoryTitle,
                         PaymentReportType, PaymentCode)
from dideman import settings
from dide.util import xml
import os


class Command(BaseCommand):
    args = '<file ...>'
    help = 'XML database import.'

    def handle(self, *args, **options):
        for rec in args:
            try:
                pf = PaymentFileName.objects.get(pk=rec)
                xml.read(os.path.join(settings.MEDIA_ROOT, '%s' % pf.xml_file)
                         .replace('/', '\\'), 'http://www.gsis.gr/psp/2.3',
                         pf.id)
            except PaymentFileName.DoesNotExist:
                raise CommandError('Record %s not found.' % rec)
