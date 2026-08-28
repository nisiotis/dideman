# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from dideman.dide.models import (TransferArea, Profession, Permanent)
from dideman import settings
from dideman.dide.util.settings import SETTINGS
from django.utils.encoding import force_str
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
                print(str(worksheet.cell_value(curr_row,1)))
                try:
                    p = Permanent.objects.get(vat_number=str(worksheet.cell_value(curr_row,1)))                
                    p.registration_number = str(worksheet.cell_value(curr_row,2))
                    print(p.registration_number)
                    p.save()
                except Exception as ex:
                    print(ex)
                curr_row += 1
            print(curr_row)

        if args == ():
            print("No arguments found")
