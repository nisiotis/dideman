# -*- coding: utf-8 -*-
# import permanents with non permanents deactivation.
# usage
# xls_mass_import <xls file>
# assumes 1st xls column as registration_number

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
            sr = 0
            fr = 0
            while curr_row < worksheet.nrows:
                try:

                    nonp = NonPermanent.objects.filter(vat_number = unicode(worksheet.cell_value(curr_row,12))[:9])
                    if nonp:
                        print "FOUND ", nonp
                        np += 1
                        vat_to_in = None
                        id_no = None
                    else:
                        vat_to_in = unicode(worksheet.cell_value(curr_row,12))[:9]
                        id_no = unicode(worksheet.cell_value(curr_row,10)).replace(" ", "")
                    t_area = 0
                
                    if unicode(worksheet.cell_value(curr_row,11))[:1] == u"Α":
                        t_area = 1
                    if unicode(worksheet.cell_value(curr_row,11))[:1] == u"Β":
                        t_area = 2
                    if unicode(worksheet.cell_value(curr_row,11))[:1] == u"Γ":
                        t_area = 3
                    if unicode(worksheet.cell_value(curr_row,11))[:1] == u"Δ":
                        t_area = 4
                    sex_t = "Άνδρας"
                    if unicode(worksheet.cell_value(curr_row,6))[:1] == u"Γ":
                        sex_t = "Γυναίκα"
                    mar_s = 0
                    if unicode(worksheet.cell_value(curr_row,17))[:1] == u"Δ":
                        mar_s = 2
                    if unicode(worksheet.cell_value(curr_row,17))[:1] == u"Ε":
                        mar_s = 1
                    dob = None
                    try:
                        dob = datetime(*xlrd.xldate_as_tuple(worksheet.cell_value(curr_row,20),0))
                    except:
                        pass
                    d_h = None
                    try:
                        d_h = datetime(*xlrd.xldate_as_tuple(worksheet.cell_value(curr_row,22),0))
                    except:
                        pass
                    b93 = 0
                    try:
                        b93 = int(unicode(worksheet.cell_value(curr_row,19))[:1])
                    except:
                        pass
                    tn1 = ""
                    try:
                        tn1 = int(unicode(worksheet.cell_value(curr_row,16))[:10])
                    except:
                        pass
                    
                    iban_in = ""
                    if worksheet.cell_value(curr_row,15) != "":
                        iban_in = unicode(worksheet.cell_value(curr_row,15)).replace(" ","")
                    p = Permanent(vat_number=vat_to_in,
                                      registration_number=unicode(worksheet.cell_value(curr_row,0))[:6],
                                      lastname=unicode(worksheet.cell_value(curr_row,1)),
                                      firstname=unicode(worksheet.cell_value(curr_row,2)),
                                      fathername=unicode(worksheet.cell_value(curr_row,3)),
                                      mothername=unicode(worksheet.cell_value(curr_row,4)),
                                      profession=Profession.objects.get(pk=unicode(worksheet.cell_value(curr_row,5))), #fix
                                      sex=sex_t,
                                      transfer_area=TransferArea.objects.get(pk=t_area), #fix
                                      telephone_number1=tn1,
                                      email=unicode(worksheet.cell_value(curr_row,14)),
                                      order_hired=unicode(worksheet.cell_value(curr_row,23)),
                                      address=unicode(worksheet.cell_value(curr_row,7)),
                                      address_postcode=unicode(worksheet.cell_value(curr_row,9))[:5],
                                      address_city=unicode(worksheet.cell_value(curr_row,8)),
                                      tax_office=unicode(worksheet.cell_value(curr_row,13)),
                                      iban=iban_in,
                                      marital_status=mar_s,
                                      before_93=b93, 
                                      date_hired=d_h, #fix
                                      identity_number=id_no,
                                      social_security_registration_number=str(worksheet.cell_value(curr_row,18)).replace(".0",""),
                                      birth_date=dob)                        
                    p.save()
                    sr+=1
                    print p
                except Exception as ex:
                    print(ex)
                    fr+=1
                curr_row += 1
                
            print "TOTAL IN EXCEL", curr_row - 1
            if np > 0:
                print "FOUND NONPERMANENT", np
            print "Success ", sr
            print "Failed", fr
        if args == ():
            print "No arguments found"
