# -*- coding: utf-8 -*-
# find dublicates.
# usage
# find_dbls --f <xls file> --y <year of active personnel> --ci <column_index> --ws <sheet index>
# assumes 1st xls column as registration_number
from optparse import make_option

from django.core.management.base import BaseCommand
from dideman.dide.models import NonPermanent, Permanent
from ._import_common import (COLUMN_OPTION, FILE_OPTION, SHEET_OPTION, confirm,
                             open_worksheet_or_exit, vat_to_text)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        FILE_OPTION,
        COLUMN_OPTION,
        make_option('--y', type=int, help='The year of work'),
        SHEET_OPTION,
    )

    help = 'XLS Find Dublicates.'

    def find_matches(self, worksheet, idx):
        matches = []
        curr_row = 0
        while curr_row < worksheet.nrows:
            driver_cell = worksheet.cell(curr_row, 0)
            cell = worksheet.cell(curr_row, idx)
            try:
                perm = Permanent.objects.filter(registration_number=unicode(driver_cell.value)[:6]).first()
                nonp = NonPermanent.objects.filter(vat_number=vat_to_text(cell.value)).first()
            except Exception:
                perm = None
                nonp = None
            if perm and nonp:
                matches.append((perm, nonp))
            curr_row += 1
        return matches

    def handle(self, *args, **options):
        workbook, worksheet = open_worksheet_or_exit(options['f'], options['ws'])
        idx = options['ci'] if options['ci'] else 1
        print "Worksheet name %s, Rows %s" % (worksheet.name, worksheet.nrows)

        matches = self.find_matches(worksheet, idx)
        print "Found records to update %s" % len(matches)
        if not confirm():
            exit()

        upd_rows = 0
        # re-fetch fresh rows for the update pass, since the confirm prompt
        # above may have paused for a while
        for perm, nonp in self.find_matches(worksheet, idx):
            try:
                perm.vat_number = nonp.vat_number
                nonp.vat_number = None
                nonp.save()
                perm.save()
                upd_rows += 1
            except Exception as ex:
                print(ex)
        if upd_rows > 0:
            print upd_rows, " updated"
