# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from dideman.dide.models import (TransferArea, Profession, NonPermanent)
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
            curr_row = 1
            er_r = 0
            while curr_row < worksheet.nrows:
                np = NonPermanent(email=unicode(worksheet.cell_value(curr_row,0)),
                                  telephone_number1=unicode(worksheet.cell_value(curr_row,1)).replace(".0",""),
                                  vat_number=unicode(worksheet.cell_value(curr_row,2))[:9], 
                                  lastname=unicode(worksheet.cell_value(curr_row,3)),
                                  firstname=unicode(worksheet.cell_value(curr_row,4)),
                                  fathername=unicode(worksheet.cell_value(curr_row,5)),
                                  mothername=unicode(worksheet.cell_value(curr_row,6)),
                                  profession_code_oaed=unicode(worksheet.cell_value(curr_row,7)).replace(".0",""),
                                  profession=Profession.objects.get(pk=unicode(worksheet.cell_value(curr_row,8))),
                                  transfer_area=TransferArea.objects.get(pk=int(worksheet.cell_value(curr_row,9))),
                                  identity_number=unicode(worksheet.cell_value(curr_row,10)).replace(" ",""),
                                  birth_date=unicode(worksheet.cell_value(curr_row,11)),
                                  social_security_registration_number=unicode(worksheet.cell_value(curr_row,12))[:11].replace(".", ""),
                                  address=unicode(worksheet.cell_value(curr_row,13)),
                                  address_postcode=unicode(worksheet.cell_value(curr_row,14))[:5],
                                  address_city=unicode(worksheet.cell_value(curr_row,15)),
                                  educational_level=int(unicode(worksheet.cell_value(curr_row,16))[:2]),
                                  tax_office=unicode(worksheet.cell_value(curr_row,17)),
                                  bank=unicode(worksheet.cell_value(curr_row,18)),
                                  iban=unicode(worksheet.cell_value(curr_row,19))[:27],
                                  ama=unicode(worksheet.cell_value(curr_row,20)).replace(".0","")[:10],
                                  marital_status=int(unicode(worksheet.cell_value(curr_row,21))[:1]))
                
                try:
                    print np
                    print np.vat_number, np.profession, np.transfer_area, np.identity_number, np.birth_date, np.ama, np.social_security_registration_number
                    np.clean_fields()
                    np.save()
                except Exception as ex:
                    er_r += 1
                    print(ex)
                curr_row += 1
            print curr_row - 1, " ", er_r

        if args == ():
            print "No arguments found"
