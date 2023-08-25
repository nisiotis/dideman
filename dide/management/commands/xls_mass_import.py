# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from dideman.dide.models import (TransferArea, Profession, Permanent, NonPermanent)
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
            #permanents = Permanent.objects.all()
            workbook = xlrd.open_workbook(item)
            worksheet = workbook.sheet_by_index(0)
            curr_row = 1
            np = 0
            while curr_row < worksheet.nrows:
                #curr_row += 1
                #print worksheet.cell_value(curr_row,6), worksheet.cell_value(curr_row,7), worksheet.cell_value(curr_row,10), worksheet.cell_value(curr_row,13)
                nonp = NonPermanent.objects.filter(vat_number = unicode(worksheet.cell_value(curr_row,0))[:9])
                if nonp:
                    print "FOUND ", nonp
                    np += 1
                    vat_to_in = None
                    id_no = None
                else:
                    vat_to_in = unicode(worksheet.cell_value(curr_row,0))[:9]
                    id_no = unicode(worksheet.cell_value(curr_row,12))
                p = Permanent(vat_number=vat_to_in,
                              registration_number=unicode(worksheet.cell_value(curr_row,1))[:6],
                              lastname=unicode(worksheet.cell_value(curr_row,2)),
                              firstname=unicode(worksheet.cell_value(curr_row,3)),
                              fathername=unicode(worksheet.cell_value(curr_row,4)),
                              mothername=unicode(worksheet.cell_value(curr_row,5)),
                              profession=Profession.objects.get(pk=unicode(worksheet.cell_value(curr_row,6))), #fix
                              transfer_area=TransferArea.objects.get(pk=int(worksheet.cell_value(curr_row,7))), #fix
                              telephone_number1=int(worksheet.cell_value(curr_row,8)),
                              email=unicode(worksheet.cell_value(curr_row,9)),
                              date_hired=datetime(*xlrd.xldate_as_tuple(worksheet.cell_value(curr_row,10),0)), #fix
                              order_hired=unicode(worksheet.cell_value(curr_row,11)),
                              identity_number=id_no,
                              birth_date=datetime(*xlrd.xldate_as_tuple(worksheet.cell_value(curr_row,13),0))) #fix
                
                try:
                    print p.registration_number, p.lastname
                    p.save()
                except Exception as ex:
                    print(ex)

                curr_row += 1
                
            print "TOTAL IN EXCEL", curr_row - 1
            if np > 0:
                print "FOUND NONPERMANENT", np
        if args == ():
            print "No arguments found"
