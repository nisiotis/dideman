# -*- coding: utf-8 -*- 
import datetime
import os
import xlrd

from dideman import settings

from cStringIO import StringIO
from django.db import connection, transaction
from dideman.dide.util.settings import SETTINGS


def xlsread(xlsfile, year_earned):
    l = 0
    sqlstr = ""

    workbook = xlrd.open_workbook(pdffile.name)
    worksheet = workbook.sheet_by_index(1)
    num_rows = worksheet.nrows - 1
    num_cells = worksheet.ncols - 1
    curr_row = -1

    cursor = connection.cursor()
    while curr_row < num_rows:
        curr_row += 1
        row = worksheet.row(curr_row)
        print 'Row:', curr_row
        curr_cell = -1
        while curr_cell < num_cells:
            curr_cell += 1
            # Cell Types: 0=Empty, 1=Text, 2=Number, 3=Date, 4=Boolean, 5=Error, 6=Blank
            cell_type = worksheet.cell_type(curr_row, curr_cell)
            cell_value = worksheet.cell_value(curr_row, curr_cell)
            if cell_type != 0 and cell_type != 6:		
                strsql = "insert into nonpermanenttimeserved (id, employee_id, year_earned, years, months, days) values (NULL,%s,%s,%s,%s,%s);" % (l[8:], obj_id, new_file, pdffiletype)

            cursor.execute(strsql)
    
            l += 1
    
    transaction.commit_unless_managed()
    cursor.close()

    return 1, l
