# -*- coding: utf-8 -*- 
import datetime
import os
import xlrd

from dideman import settings
from dideman.dide.models import Employee
from cStringIO import StringIO
from django.db import connection, transaction
from dideman.dide.util.settings import SETTINGS


def xlsread(xlsfile, year_earned):
    l = 0
    sqlstr = ""
    emp = NonPermanent.objects.select_related().exclude(parent__social_security_registration_number__isnull=True).exclude(parent__social_security_registration_number__exact='')
    
    workbook = xlrd.open_workbook(xlsfile.name)
    worksheet = workbook.sheet_by_index(1)
    num_rows = worksheet.nrows - 1
    num_cells = worksheet.ncols - 1
    curr_row = 0

    cursor = connection.cursor()
    import pdb; pdb.set_trace()
    while curr_row < num_rows:
        curr_row += 1
        row = worksheet.row(curr_row)
        curr_cell = 5
        while curr_cell < num_cells:
            curr_cell += 1
            # Cell Types: 0=Empty, 1=Text, 2=Number, 3=Date, 4=Boolean, 5=Error, 6=Blank
            cell_type = worksheet.cell_type(curr_row, curr_cell)
            cell_value = worksheet.cell_value(curr_row, curr_cell)
            if cell_type != 0 and cell_type != 6:		
                
                strsql = "insert into dide_nonpermanentunemploymentmonth (id,  employee_id, pay_type, days_insured, month, year, insured_from, insured_to, total_earned, employee_contributions, employer_contributions, total_contributions) values (NULL, %s, '%s', %s, %s, %s, '%s', '%s', '%s', '%s', '%s', '%s');" % ()

            cursor.execute(strsql)
    
            l += 1
    
    transaction.commit_unless_managed()
    cursor.close()

    return 1, l
