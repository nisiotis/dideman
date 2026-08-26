# -*- coding: utf-8 -*-
from dideman.dide.models import Permanent
from ._import_common import XlsFileCommand, cell_unicode


class Command(XlsFileCommand):
    help = 'Update non_educational_experience on Permanent employees from an xls file.'
    start_row = 1

    def on_file_start(self, workbook, worksheet, options):
        self.inserted = 0

    def process_row(self, workbook, worksheet, row, options):
        registration_number = cell_unicode(worksheet, row, 0)
        try:
            permanent = Permanent.objects.get(registration_number=registration_number)
            permanent.non_educational_experience = cell_unicode(worksheet, row, 7)
            permanent.save()
            print "Inserted %s %s (%s)" % (permanent.firstname, permanent.lastname,
                                           permanent.non_educational_experience)
            self.inserted += 1
        except Exception as ex:
            print(ex)

    def on_file_end(self, workbook, worksheet, total_rows, options):
        print "Rows inserted: %s" % self.inserted
