# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from dide.models import (TransferArea, Profession, Permanent)
from dideman import settings
from dideman.dide.util.settings import SETTINGS
from django.utils.encoding import force_unicode
from datetime import datetime
import os
import xlrd

class Command(BaseCommand):
    args = '<file ...>'
    help = 'XLS database import.'

    def handle(self, *args, **options):
        for item in args:
            workbook = xlrd.open_workbook(item)
            worksheet = workbook.sheet_by_index(0)
            curr_row = 0
            while curr_row < worksheet.nrows:
                p = Permanent(registration_number=unicode(worksheet.cell_value(curr_row,0))[:6], 
                            lastname=unicode(worksheet.cell_value(curr_row,1)),
                            firstname=unicode(worksheet.cell_value(curr_row,2)),
                            fathername=unicode(worksheet.cell_value(curr_row,3)),
                            profession=Profession.objects.get(pk=unicode(worksheet.cell_value(curr_row,4))),
                            transfer_area=TransferArea.objects.get(pk=int(worksheet.cell_value(curr_row,5))),
                            #telephone_number1=int(worksheet.cell_value(curr_row,6)),
                            #telephone_number2=int(worksheet.cell_value(curr_row,7)),
                            #email=unicode(worksheet.cell_value(curr_row,8)),
                            #date_hired=unicode(worksheet.cell_value(curr_row,9)),
                            order_hired=unicode(worksheet.cell_value(curr_row,6)))
                print p
                try:
                    
                    p.save()
                except Exception as ex:
                    print(ex)
                curr_row += 1
            print curr_row

        if args == ():
            print "No arguments found"
