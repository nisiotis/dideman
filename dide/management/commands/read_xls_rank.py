# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from dide.models import (RankCode, Permanent, PromotionNew)
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
            permanents = Permanent.objects.all()
            workbook = xlrd.open_workbook(item)
            worksheet = workbook.sheet_by_index(0)
            curr_row = 0
            ins_row = 0
            cursor = connection.cursor()
            while curr_row < worksheet.nrows:
                # Cell Types: 0=Empty, 1=Text, 2=Number, 3=Date, 4=Boolean, 5=Error, 6=Blank
                firstname = unicode(worksheet.cell_value(curr_row, 1))
                lastname = unicode(worksheet.cell_value(curr_row, 0))
                fathername = unicode(worksheet.cell_value(curr_row, 2))
                
                rank = unicode(worksheet.cell_value(curr_row, 4))
                ee = int(worksheet.cell_value(curr_row, 5))
                mm = int(worksheet.cell_value(curr_row, 6))
                hh = int(worksheet.cell_value(curr_row, 7))
                time_left = "%02d%02d%02d" % (ee,mm,hh)

                try:
                    emps = permanents.filter(parent__firstname=firstname,
                                             parent__lastname=lastname,parent__fathername=fathername)
                except:
                    print "Error: %s %s %s\n" % (firstname, lastname, fathername)
                    emps = []
                if emps:
                    if len(emps) == 1:
                        strsql = "insert into dide_promotionnew (Id, employee_id, rank, value_id, date, time_left, `order`,order_pysde) values (NULL, %s, '%s', %s, '2016-01-01', '%s', '%s', '');" % (emps[0].parent_id, unicode(rank), unicode(emps[0].ranknew()).split(" ")[1], time_left, u'από μεταφορά')
                        cursor.execute(strsql)
                        ins_row +=1
                    else:
                        print "Not sole:"
                        for item in emps:
                           print "%s %s %s" % (item.parent.lastname, item.parent.firstname, item.parent.fathername) 
                else:
                    print "%s %s %s Not found" % (firstname, lastname, fathername)

                curr_row += 1
        
            print "Total %s" % curr_row
            print "Inserted %s" % ins_row
            transaction.commit_unless_managed()
            cursor.close()
                
        
        
        if args == ():
            print "No arguments found"
