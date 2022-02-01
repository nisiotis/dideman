# -*- coding: utf-8 -*- 
import datetime
import os
import xlrd

from dideman import settings
from dideman.dide.models import NonPermanent
from cStringIO import StringIO
from django.db import connection, transaction
from dideman.dide.util.settings import SETTINGS
from django.utils.encoding import force_unicode


def xlsread(oid, xlsfile):
    xls_name = xlsfile.rsplit('/', 1)[1]
    recs_missed = {}
    sqlstr = ""
    emp = NonPermanent.objects.select_related().exclude(parent__social_security_registration_number__isnull=True).exclude(parent__social_security_registration_number__exact='')
    
    workbook = xlrd.open_workbook(xlsfile)

    worksheet = workbook.sheet_by_index(0)
    curr_row = 0
    cursor = connection.cursor()
    while curr_row < worksheet.nrows - 1:
        curr_row += 1
        row = worksheet.row(curr_row)
        # Cell Types: 0=Empty, 1=Text, 2=Number, 3=Date, 4=Boolean, 5=Error, 6=Blank
        e_lastname = worksheet.cell_value(curr_row, 2)
#        e_social_security_registration_number = str(worksheet.cell_value(curr_row, 4)).rstrip('0').rstrip('.') if '.' in str(worksheet.cell_value(curr_row, 4)) else str(worksheet.cell_value(curr_row, 4))
#        e_pay_type = worksheet.cell_value(curr_row, 5)

        try:
            e = emp.get(social_security_registration_number__contains=e_social_security_registration_number, lastname=e_lastname)
        except:
            recs_missed[str(worksheet.cell_value(curr_row, 0))] = u'Αρχείο %s: %s %s' % (force_unicode(xls_name, 'utf-8', 'ignore'), e_social_security_registration_number, force_unicode(e_lastname, 'utf-8', 'ignore')) 
            e = False

        if e and e_pay_type in (u'ΜΗΝΙΑΙΕΣ', u'ΑΔΕΙΑ ΑΣΘΕΝΕΙΑΣ'):
            e_days_insured = str(worksheet.cell_value(curr_row, 6)).rstrip('0').rstrip('.') if '.' in str(worksheet.cell_value(curr_row, 6)) else str(worksheet.cell_value(curr_row, 6))
            e_month = str(worksheet.cell_value(curr_row, 7)).rstrip('0').rstrip('.') if '.' in str(worksheet.cell_value(curr_row, 7)) else str(worksheet.cell_value(curr_row, 7))
            e_year = str(worksheet.cell_value(curr_row, 8)).rstrip('0').rstrip('.') if '.' in str(worksheet.cell_value(curr_row, 8)) else str(worksheet.cell_value(curr_row, 8))
            e_insured_from = worksheet.cell_value(curr_row, 9)
            e_insured_to = worksheet.cell_value(curr_row, 10)
            e_total_earned = worksheet.cell_value(curr_row, 11)
            e_employee_contributions = worksheet.cell_value(curr_row, 12)
            e_employer_contributions = worksheet.cell_value(curr_row, 13)
            e_total_contributions = worksheet.cell_value(curr_row, 14)
            strsql = "insert into dide_nonpermanentunemploymentmonth (id, insurance_file_id,  employee_id, pay_type, days_insured, month, year, insured_from, insured_to, total_earned, employee_contributions, employer_contributions, total_contributions) values (NULL, %s, %s, '%s', %s, %s, %s, '%s', '%s', '%s', '%s', '%s', '%s');" % (oid, e.parent_id, e_pay_type, e_days_insured, e_month, e_year, e_insured_from, e_insured_to, e_total_earned, e_employee_contributions, e_employer_contributions, e_total_contributions)
            cursor.execute(strsql)

    
        
    
    transaction.commit_unless_managed()
    cursor.close()
    return recs_missed
