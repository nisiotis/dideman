# -*- coding: utf-8 -*-
from django.db import connection
from dideman.dide.models import School
from ._import_common import XlsFileCommand, cell_unicode


class Command(XlsFileCommand):
    help = 'Update School map coordinates (google_maps_x/y) from an xls file.'

    def on_file_start(self, workbook, worksheet, options):
        self.updated = 0

    def process_row(self, workbook, worksheet, row, options):
        email = cell_unicode(worksheet, row, 1)
        x = cell_unicode(worksheet, row, 2)
        y = cell_unicode(worksheet, row, 3)

        schools = School.objects.filter(email=email)
        if len(schools) == 1:
            cursor = connection.cursor()
            cursor.execute(
                "update dide_school set google_maps_x = %s, google_maps_y = %s "
                "where parent_organization_id = %s", [x, y, schools[0].id])
            self.updated += 1
        elif schools:
            print "Not sole:"
            for sch in schools:
                print "%s" % sch.email
        else:
            print "%s Not found" % email

    def on_file_end(self, workbook, worksheet, total_rows, options):
        print "Total %s" % total_rows
        print "Inserted %s" % self.updated
