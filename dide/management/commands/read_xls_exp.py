# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from dideman.dide.models import (RankCode, Permanent, PromotionNew)
from dideman import settings
from dideman.dide.util.settings import SETTINGS
from django.utils.encoding import force_unicode
from datetime import datetime
import os
import xlrd

class Command(BaseCommand):
    args = '<file ...>'
    help = 'XML database import.'

    def handle(self, *args, **options):
        for item in args:
            
            workbook = xlrd.open_workbook(item)
            worksheet = workbook.sheet_by_index(0)
            curr_row = 1
            ins_row = 0
            #cursor = connection.cursor()
            while curr_row < worksheet.nrows:
                # Cell Types: 0=Empty, 1=Text, 2=Number, 3=Date, 4=Boolean, 5=Error, 6=Blank

                try:
                    o = Permanent.objects.filter(registration_number=unicode(worksheet.cell_value(curr_row,0)))
                    p = Permanent.objects.get(id=o[0].id)

                    p.non_educational_experience = unicode(worksheet.cell_value(curr_row, 7))
                    p.save()
                    print "Inserted %s %s (%s)" % (p.firstname, p.lastname, p.non_educational_experience)
                    ins_row += 1

                except Exception as ex:
                    print(ex)
                #except:
                #    print p

                curr_row += 1

        print "Rows inserted: %s" % ins_row        

        if args == ():
            print "No arguments found"
