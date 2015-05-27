# -*- coding: utf-8 -*- 
import pyPdf
import datetime
import os
from dideman import settings

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.layout import LAParams
from cStringIO import StringIO
from django.db import connection, transaction
from dideman.dide.util.settings import SETTINGS

def read(pdffile, pdffiletype, obj_id):
    nl = []
    sqlstr = ""
    f = file(pdffile.name, "rb") 
    pdf_in = pyPdf.PdfFileReader(f)
    pages = pdf_in.numPages
    cursor = connection.cursor()
    for p in range(0,pages-1):
        mem_page = pdf_in.getPage(p)
        pdf_out = pyPdf.PdfFileWriter()
        pdf_out.addPage(mem_page)
        out_stream = StringIO()
        pdf_out.write(out_stream)
        parser = PDFParser(out_stream)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        retstr = StringIO()
        device = TextConverter(rsrcmgr, retstr, codec='utf-8', laparams=LAParams())
        interpreter = PDFPageInterpreter(rsrcmgr,device)
        lines = ""
        for page in PDFPage.create_pages(doc):
            interpreter.process_page(page)
            rstr = retstr.getvalue()
            if len(rstr.strip()) > 0:
                lines+="".join(rstr)
        lst = lines.split('\n')
        for l in lst:
            if l[:6] == 'ΑΦΜ':
                if l[8:] != SETTINGS['afm_dide']:
                    new_file = '%s.%s.%s.pdf' % (pdffile.name.replace(os.path.join(settings.MEDIA_ROOT,'pdffiles'),'')[1:-4],l[8:],datetime.datetime.now().strftime('%H%M%S%f'))

                
                    out_file = open(os.path.join(settings.MEDIA_ROOT,'pdffiles', 'extracted', new_file), 'wb')
                    pdf_out.write(out_file)
                    out_file.close()
                    strsql = "insert into dide_paymentemployeepdf (id, employee_vat, paymentfilepdf_id, employeefile, pdf_file_type) values (NULL,'%s',%s,'%s', %s);" % (l[8:], obj_id, new_file, pdffiletype)
                    cursor.execute(strsql)

                    nl.append(l[8:])
    
    transaction.commit_unless_managed()
    cursor.close()

    f.close()
    return 1, len(nl)
