# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from dide.models import School
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
            schools = School.objects.all()
            workbook = xlrd.open_workbook(item)
            worksheet = workbook.sheet_by_index(0)
            curr_row = 0
            ins_row = 0
            cursor = connection.cursor()
            while curr_row < worksheet.nrows:
                # Cell Types: 0=Empty, 1=Text, 2=Number, 3=Date, 4=Boolean, 5=Error, 6=Blank
                email = unicode(worksheet.cell_value(curr_row, 1))
                x = unicode(worksheet.cell_value(curr_row, 2))
                y = unicode(worksheet.cell_value(curr_row, 3))

                try:
                    sch = schools.filter(email=email)
                except:
                    print "Error: %s %s %s\n" % (firstname, lastname, fathername)
                    sch = []
                if sch:
                    if len(sch) == 1:
                        strsql = "update dide_school set google_maps_x = '%s', google_maps_y = '%s' where parent_organization_id=%s" % (x, y, sch[0].id)
                        #print strsql 
                        cursor.execute(strsql)
                        ins_row +=1
                    else:
                        print "Not sole:"
                        for item in sch:
                           print "%s" % item.email 
                else:
                    print "%s Not found" % email

                curr_row += 1
        
            print "Total %s" % curr_row
            print "Inserted %s" % ins_row
            transaction.commit_unless_managed()
            cursor.close()
                
        
        
        if args == ():
            print "No arguments found"
