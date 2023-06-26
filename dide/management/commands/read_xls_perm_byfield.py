# -*- coding: utf-8 -*-
# import by field.
# usage
# read_xls_perm_byfield --f <xls file> --ci <column_no> --df <field_name> --ws <sheet index>
# assumes 1st xls column as registration_number

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from dideman.dide.util.settings import SETTINGS
from dideman.dide.models import (TransferArea, Profession, Permanent, Employee)
from dideman import settings
from django.utils.encoding import force_unicode
from datetime import datetime
import os
import xlrd
from optparse import make_option

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--f', type=str, help='The xls file'),
        make_option('--ci', type=int, help='The column field'),
        make_option('--df', type=str, help='The field'),
        make_option('--ws', type=int, help='The sheet index of xls book')
    )
    
    help = 'XLS database import.'
    def find_model_field(self, model, df):
        field_name = ""
        for f in model._meta.fields:
            if f.name == df:
                field_name = f
        return field_name

    def vat_to_text(self, df):
        try:
            v = int(df)
            v = str(v).zfill(9)
        except:
            v = str(df).zfill(9)
        return v[:9]


    def handle(self, *args, **options):
         if options['f'] != '':
            try:
                workbook = xlrd.open_workbook(options['f'])
            except:
                print "--f <file>: xls file required / not found"
                exit()
            if options['df'] != '':
                if self.find_model_field(Permanent, options['df']) != "":
                    worksheet = workbook.sheet_by_index(options['ws']) if options['ws'] else workbook.sheet_by_index(0)
                    curr_row = 0
                    upd_rows = 0
                    perm_rows = 0
                    idx = options['ci'] if options['ci'] else 1
                    fld = self.find_model_field(Permanent, options['df'])
                    print "Field to inport: %s" % fld.name
                    print "Worksheet name %s, Rows %s" %(worksheet.name, worksheet.nrows)

                    print "Continue? "
                    iv = str(raw_input())
                    if iv != 'y' and iv != 'yes':
                        exit()
                    while curr_row < worksheet.nrows:   
                        driver_cell = worksheet.cell(curr_row,0)
                        cell = worksheet.cell(curr_row,idx)
                        p = Permanent.objects.filter(registration_number=unicode(driver_cell.value)[:6]).first()
                        if p:
                            if fld.name == 'vat_number':
                                e = Employee.objects.filter(vat_number=self.vat_to_text(cell.value)).first()
                                if e:
                                    print e
                                    perm_rows += 1
                                else:
                                    try:
                                        setattr(p, fld.name, self.vat_to_text(cell.value))
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
                                    print unicode(driver_cell.value)[:6], getattr(p, fld.name), cell.value
                        else:
                            print unicode(driver_cell.value)[:6], cell.value
                        curr_row += 1
                    print curr_row, "rows found "
                    if upd_rows > 0: print upd_rows, " updated"
                    if perm_rows > 0: print perm_rows, " exist in Employee"  
                    
                else:
                    print "--df <datafield> not found"
                    exit()
            else:
                print "--df <field>: field to import required / not found"
                exit()

