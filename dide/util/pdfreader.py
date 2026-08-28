# -*- coding: utf-8 -*-
"""Διαχωρισμός ενός συγκεντρωτικού PDF μισθοδοσίας ανά υπάλληλο.

Το pyPdf ήταν βιβλιοθήκη μόνο για Python 2· τη διαδέχθηκε το ``pypdf``,
με νέα ονόματα API (``PdfReader``/``PdfWriter``, ``.pages``,
``.add_page``).
"""
import datetime
import os
from io import BytesIO, StringIO

from pypdf import PdfReader, PdfWriter

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

from django.db import connection

from dideman import settings
from dideman.dide.util.settings import SETTINGS


def read(pdffile, pdffiletype, obj_id):
    nl = []
    # Το `file()` δεν υπάρχει στην Python 3.
    with open(pdffile.name, "rb") as f:
        pdf_in = PdfReader(f)
        pages = len(pdf_in.pages)
        cursor = connection.cursor()
        # Διατηρείται το αρχικό εύρος: η τελευταία σελίδα δεν επεξεργάζεται.
        for p in range(0, pages - 1):
            mem_page = pdf_in.pages[p]
            pdf_out = PdfWriter()
            pdf_out.add_page(mem_page)
            # Το PDF γράφεται σε bytes· με StringIO η εγγραφή αποτυγχάνει
            # στην Python 3.
            out_stream = BytesIO()
            pdf_out.write(out_stream)
            out_stream.seek(0)

            parser = PDFParser(out_stream)
            doc = PDFDocument(parser)
            rsrcmgr = PDFResourceManager()
            retstr = StringIO()
            device = TextConverter(rsrcmgr, retstr, laparams=LAParams())
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            lines = ""
            for page in PDFPage.create_pages(doc):
                interpreter.process_page(page)
                rstr = retstr.getvalue()
                if len(rstr.strip()) > 0:
                    lines += "".join(rstr)

            for li in lines.split('\n'):
                if li[:6] != 'ΑΦΜ':
                    continue
                if li[8:] == SETTINGS['afm_dide']:
                    continue
                vat = li[7:].strip()
                new_file = '%s.%s.%s.pdf' % (
                    pdffile.name.replace(
                        os.path.join(settings.MEDIA_ROOT, 'pdffiles'), '')[1:-4],
                    vat,
                    datetime.datetime.now().strftime('%H%M%S%f'))
                out_path = os.path.join(settings.MEDIA_ROOT, 'pdffiles',
                                        'extracted', new_file)
                with open(out_path, 'wb') as out_file:
                    pdf_out.write(out_file)
                # Παραμετροποιημένο ερώτημα: το ΑΦΜ προέρχεται από το
                # περιεχόμενο του PDF και δεν πρέπει να μπαίνει στο SQL.
                cursor.execute(
                    "insert into dide_paymentemployeepdf "
                    "(id, employee_vat, paymentfilepdf_id, employeefile, "
                    "pdf_file_type) values (NULL, %s, %s, %s, %s)",
                    [vat, obj_id, new_file, pdffiletype])
                nl.append(li[8:])

        cursor.close()
    return 1, len(nl)
