# -*- coding: utf-8 -*-
# import permanents with non permanents deactivation.
# usage
# xls_mass_import <xls file>
# assumes 1st xls column as registration_number
from datetime import datetime

import xlrd

from dideman.dide.models import NonPermanent, Permanent, Profession, TransferArea
from ._import_common import XlsFileCommand, cell_unicode


class Command(XlsFileCommand):
    help = 'XLS database import.'
    start_row = 1

    def on_file_start(self, workbook, worksheet, options):
        self.found_nonpermanent = 0
        self.success = 0
        self.failed = 0

    def process_row(self, workbook, worksheet, row, options):
        try:
            nonp = NonPermanent.objects.filter(vat_number=cell_unicode(worksheet, row, 12)[:9])
            if nonp:
                print "FOUND ", nonp
                self.found_nonpermanent += 1
                vat_to_in = None
                id_no = None
            else:
                vat_to_in = cell_unicode(worksheet, row, 12)[:9]
                id_no = cell_unicode(worksheet, row, 10).replace(" ", "")

            t_area = 0
            if cell_unicode(worksheet, row, 11)[:1] == u"Α":
                t_area = 1
            if cell_unicode(worksheet, row, 11)[:1] == u"Β":
                t_area = 2
            if cell_unicode(worksheet, row, 11)[:1] == u"Γ":
                t_area = 3
            if cell_unicode(worksheet, row, 11)[:1] == u"Δ":
                t_area = 4

            sex_t = "Άνδρας"
            if cell_unicode(worksheet, row, 6)[:1] == u"Γ":
                sex_t = "Γυναίκα"

            mar_s = 0
            if cell_unicode(worksheet, row, 17)[:1] == u"Δ":
                mar_s = 2
            if cell_unicode(worksheet, row, 17)[:1] == u"Ε":
                mar_s = 1

            dob = None
            try:
                dob = datetime(*xlrd.xldate_as_tuple(worksheet.cell_value(row, 20), 0))
            except Exception:
                pass

            d_h = None
            try:
                d_h = datetime(*xlrd.xldate_as_tuple(worksheet.cell_value(row, 22), 0))
            except Exception:
                pass

            b93 = 0
            try:
                b93 = int(cell_unicode(worksheet, row, 19)[:1])
            except Exception:
                pass

            tn1 = ""
            try:
                tn1 = int(cell_unicode(worksheet, row, 16)[:10])
            except Exception:
                pass

            iban_in = ""
            if worksheet.cell_value(row, 15) != "":
                iban_in = cell_unicode(worksheet, row, 15).replace(" ", "")

            p = Permanent(
                vat_number=vat_to_in,
                registration_number=cell_unicode(worksheet, row, 0)[:6],
                lastname=cell_unicode(worksheet, row, 1),
                firstname=cell_unicode(worksheet, row, 2),
                fathername=cell_unicode(worksheet, row, 3),
                mothername=cell_unicode(worksheet, row, 4),
                profession=Profession.objects.get(pk=cell_unicode(worksheet, row, 5)),
                sex=sex_t,
                transfer_area=TransferArea.objects.get(pk=t_area),
                telephone_number1=tn1,
                email=cell_unicode(worksheet, row, 14),
                order_hired=cell_unicode(worksheet, row, 23),
                address=cell_unicode(worksheet, row, 7),
                address_postcode=cell_unicode(worksheet, row, 9)[:5],
                address_city=cell_unicode(worksheet, row, 8),
                tax_office=cell_unicode(worksheet, row, 13),
                iban=iban_in,
                marital_status=mar_s,
                before_93=b93,
                date_hired=d_h,
                identity_number=id_no,
                social_security_registration_number=str(worksheet.cell_value(row, 18)).replace(".0", ""),
                birth_date=dob)
            p.save()
            self.success += 1
            print p
        except Exception as ex:
            print(ex)
            self.failed += 1

    def on_file_end(self, workbook, worksheet, total_rows, options):
        print "TOTAL IN EXCEL", total_rows - 1
        if self.found_nonpermanent > 0:
            print "FOUND NONPERMANENT", self.found_nonpermanent
        print "Success ", self.success
        print "Failed", self.failed
