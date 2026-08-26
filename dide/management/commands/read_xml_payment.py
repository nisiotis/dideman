# -*- coding: utf-8 -*-
import os

from django.core.management.base import BaseCommand, CommandError
from dideman import settings
from dideman.dide.models import PaymentFileName
from dideman.dide.util import xml


class Command(BaseCommand):
    args = '<file ...>'
    help = 'XML database import.'

    def handle(self, *args, **options):
        for rec in args:
            try:
                pf = PaymentFileName.objects.get(pk=rec)
            except PaymentFileName.DoesNotExist:
                raise CommandError('Record %s not found.' % rec)
            path = '%s' % pf.xml_file
            folder, filename = path.split('/', 1)
            success, recs_affected, elapsed, recs_missed = xml.read(
                os.path.join(settings.MEDIA_ROOT, folder, filename), rec)
            pf.status = success
            pf.imported_records = recs_affected
            pf.save()
