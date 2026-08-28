# -*- coding: utf-8 -*-
from dideman.dide.models import Permanent
from ._import_common import XlsFileCommand, cell_unicode


class Command(XlsFileCommand):
    help = 'Update Permanent.registration_number by matching vat_number from an xls file.'

    def process_row(self, workbook, worksheet, row, options):
        vat_number = cell_unicode(worksheet, row, 1)
        print(vat_number)
        try:
            p = Permanent.objects.get(vat_number=vat_number)
            p.registration_number = cell_unicode(worksheet, row, 2)
            print(p.registration_number)
            p.save()
        except Exception as ex:
            print(ex)

    def on_file_end(self, workbook, worksheet, total_rows, options):
        print(total_rows)
