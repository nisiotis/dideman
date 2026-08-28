# -*- coding: utf-8 -*-
# import by field.
# usage
# read_xls_perm_byfield --f <xls file> --ci <column_no> --df <field_name> --ws <sheet index>
# assumes 1st xls column as registration_number
from optparse import make_option

from django.core.management.base import BaseCommand
from dideman.dide.models import Employee, Permanent
from ._import_common import (COLUMN_OPTION, FILE_OPTION, SHEET_OPTION, confirm,
                             find_model_field, open_worksheet_or_exit, vat_to_text)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        FILE_OPTION,
        COLUMN_OPTION,
        make_option('--df', type=str, help='The field'),
        SHEET_OPTION,
    )

    help = 'XLS database import.'

    def handle(self, *args, **options):
        fld = find_model_field(Permanent, options['df'])
        if not fld:
            print("--df <datafield> not found")
            exit()

        workbook, worksheet = open_worksheet_or_exit(options['f'], options['ws'])
        idx = options['ci'] if options['ci'] else 1
        print("Field to inport: %s" % fld.name)
        print("Worksheet name %s, Rows %s" % (worksheet.name, worksheet.nrows))
        if not confirm():
            exit()

        curr_row = 0
        upd_rows = 0
        perm_rows = 0
        while curr_row < worksheet.nrows:
            driver_cell = worksheet.cell(curr_row, 0)
            cell = worksheet.cell(curr_row, idx)
            p = Permanent.objects.filter(registration_number=str(driver_cell.value)[:6]).first()
            if p:
                if fld.name == 'vat_number':
                    e = Employee.objects.filter(vat_number=vat_to_text(cell.value)).first()
                    if e:
                        print(e)
                        perm_rows += 1
                    else:
                        try:
                            setattr(p, fld.name, vat_to_text(cell.value))
                            p.save()
                            upd_rows += 1
                        except Exception as ex:
                            print(ex)
                else:
                    if getattr(p, fld.name) == '' or getattr(p, fld.name) is None:
                        setattr(p, fld.name, cell.value)
                        p.save()
                        upd_rows += 1
                    else:
                        print(str(driver_cell.value)[:6], getattr(p, fld.name), cell.value)
            else:
                print(str(driver_cell.value)[:6], cell.value)
            curr_row += 1

        print(curr_row, "rows found ")
        if upd_rows > 0:
            print(upd_rows, " updated")
        if perm_rows > 0:
            print(perm_rows, " exist in Employee")
