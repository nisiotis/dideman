# -*- coding: utf-8 -*-
# find dublicates.
# usage
# find_dbls --f <xls file> --y <year of active personnel> --ci <column_index> --ws <sheet index>
# assumes 1st xls column as registration_number

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from dideman.dide.util.settings import SETTINGS
from dideman.dide.models import (TransferArea, Profession, Permanent, Employee, NonPermanent)
from dideman import settings
from django.utils.encoding import force_unicode
from datetime import datetime
import os
import xlrd
from optparse import make_option

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--f', type=str, help='The xls file'),
        make_option('--ci', type=int, help='The column index'),
        make_option('--y', type=int, help='The year of work'),
        make_option('--ws', type=int, help='The sheet index of xls book')
    )
    
    help = 'XLS Find Dublicates.'
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
         if options['f'] != '' and options['y'] != '':
            try:
                workbook = xlrd.open_workbook(options['f'])
            except:
                print "--f <file>: xls file required / not found"
                exit()
            worksheet = workbook.sheet_by_index(options['ws']) if options['ws'] else workbook.sheet_by_index(0)
            curr_row = 0
            upd_rows = 0
            perm_rows = 0
            row = 0
            idx = options['ci'] if options['ci'] else 1
            print "Worksheet name %s, Rows %s" %(worksheet.name, worksheet.nrows)
            while curr_row < worksheet.nrows:
	        driver_cell = worksheet.cell(curr_row,0)
                cell = worksheet.cell(curr_row,idx)
                try:
                    perm = Permanent.objects.filter(registration_number=unicode(driver_cell.value)[:6]).first()
                    nonp = NonPermanent.objects.filter(vat_number=self.vat_to_text(cell.value)).first()
                except:
                    perm = []
                    nonp = []
                if perm and nonp:
                    row += 1
                curr_row += 1
            print "Found records to update %s" % row
            print "Continue? "
            iv = str(raw_input())
            if iv != 'y' and iv != 'yes':
                exit()
            curr_row = 0
            upd_rows = 0
            perm_rows = 0
            row = 0
            while curr_row < worksheet.nrows:
	        driver_cell = worksheet.cell(curr_row,0)
                cell = worksheet.cell(curr_row,idx)
                try:
                    perm = Permanent.objects.filter(registration_number=unicode(driver_cell.value)[:6]).first()
                    nonp = NonPermanent.objects.filter(vat_number=self.vat_to_text(cell.value)).first()
                except:
                    perm = []
                    nonp = []
                if perm and nonp:
                    try:
                        perm.vat_number = nonp.vat_number
                        nonp.vat_number = None
                        nonp.save()
                        perm.save()
                        upd_rows += 1
                    except Exception as ex:
                        print ex
                curr_row += 1
            if upd_rows > 0: print upd_rows, " updated"
                        

