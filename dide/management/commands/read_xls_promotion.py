# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from dide.models import (RankCode, Permanent, PromotionNew, NonPermanent)
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
            while curr_row < worksheet.nrows - 1:
                curr_row += 1
                # Cell Types: 0=Empty, 1=Text, 2=Number, 3=Date, 4=Boolean, 5=Error, 6=Blank
                e_reg_num = str(worksheet.cell_value(curr_row, 0))
                e_mk = str(worksheet.cell_value(curr_row, 1))
                if worksheet.cell_value(curr_row, 2) in (u'Δ/Υ',u''):
                    e_date = u''
                else:
                    e_date = datetime(*xlrd.xldate_as_tuple(worksheet.cell_value(curr_row, 2), workbook.datemode))
                    
                try:
                    emp = permanents.get(registration_number=e_reg_num.split('.')[0])
                except:
                    print "Error: %s\n" % e_reg_num
                    emp = []
                if emp:
                    e_date_formated = ''
                    if e_date == u'':
                        e_date_formated = '0000-00-00'
                    else:
                        e_date_formated = e_date.strftime('%Y-%m-%d')
                        
                    strsql = "insert into dide_promotionnew (Id, employee_id,rank,value_id,date,next_promotion_date,`order`,order_pysde) values (NULL, %s, '%s', %s, '2016-01-01', '%s', '%s','');" % (emp.parent_id, 'Δ/Υ', int(e_mk.split('.')[0]), e_date_formated, 'από μεταφορά')
                    ins_row +=1
                    print strsql
                    cursor.execute(strsql)
        
            print "Total %s" % curr_row
            print "Inserted %s" % ins_row
            try:
                transaction.commit_unless_managed()
            except Exception as e:
                print '%s' % e.message

                
            cursor.close()
                
            #except Exception as e:
            #    raise CommandError('Error reading file %s.\n%s' % (item, e.message))
        
        
        if args == ():
            print "No arguments found"


    def handlenp(self, *args, **options):
    for item in args:
        nonpermanents = NonPermanent.objects.all()
        workbook = xlrd.open_workbook(item)
        worksheet = workbook.sheet_by_index(0)
        curr_row = 0
        ins_row = 0
        cursor = connection.cursor()
        while curr_row < worksheet.nrows - 1:
            curr_row += 1
            # Cell Types: 0=Empty, 1=Text, 2=Number, 3=Date, 4=Boolean, 5=Error, 6=Blank
            e_reg_num = str(worksheet.cell_value(curr_row, 0))
            e_mk = str(worksheet.cell_value(curr_row, 1))
            if worksheet.cell_value(curr_row, 2) in (u'Δ/Υ', u''):
                e_date = u''
            else:
                e_date = datetime(*xlrd.xldate_as_tuple(worksheet.cell_value(curr_row, 2), workbook.datemode))

            try:
                emp = nonpermanents.get(registration_number=e_reg_num.split('.')[0])
            except:
                print "Error: %s\n" % e_reg_num
                emp = []
            if emp:
                e_date_formated = ''
                if e_date == u'':
                    e_date_formated = '0000-00-00'
                else:
                    e_date_formated = e_date.strftime('%Y-%m-%d')

                strsql = "insert into dide_promotionnewnp (Id, employee_id,value_id,date) values (NULL, %s, '%s', %s,  '%s', '%s','');" % (
                emp.parent_id, 'Δ/Υ', int(e_mk.split('.')[0]), e_date_formated, 'από ημερομηνια ανάληψης υπηρεσίας')
                ins_row += 1
                print strsql
                cursor.execute(strsql)

        print "Total %s" % curr_row
        print "Inserted %s" % ins_row
        try:
            transaction.commit_unless_managed()
        except Exception as e:
            print '%s' % e.message

        cursor.close()

        # except Exception as e:
        #    raise CommandError('Error reading file %s.\n%s' % (item, e.message))

    if args == ():
        print "No arguments found"
