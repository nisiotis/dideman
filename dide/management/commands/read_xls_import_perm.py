# -*- coding: utf-8 -*-
from dideman.dide.models import Permanent, Profession, TransferArea
from ._import_common import XlsFileCommand, cell_unicode


class Command(XlsFileCommand):
    help = 'Create Permanent employees from an xls file.'

    def process_row(self, workbook, worksheet, row, options):
        p = Permanent(
            registration_number=cell_unicode(worksheet, row, 0)[:6],
            lastname=cell_unicode(worksheet, row, 1),
            firstname=cell_unicode(worksheet, row, 2),
            fathername=cell_unicode(worksheet, row, 3),
            profession=Profession.objects.get(pk=cell_unicode(worksheet, row, 4)),
            transfer_area=TransferArea.objects.get(pk=int(worksheet.cell_value(row, 5))),
            order_hired=cell_unicode(worksheet, row, 6))
        print(p)
        try:
            p.save()
        except Exception as ex:
            print(ex)

    def on_file_end(self, workbook, worksheet, total_rows, options):
        print(total_rows)
