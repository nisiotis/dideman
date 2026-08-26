# -*- coding: utf-8 -*-
from dideman.dide.models import NonPermanent, Profession, TransferArea
from ._import_common import XlsFileCommand, cell_unicode


class Command(XlsFileCommand):
    help = 'Create NonPermanent employees from an xls file.'
    start_row = 1

    def on_file_start(self, workbook, worksheet, options):
        self.errors = 0

    def process_row(self, workbook, worksheet, row, options):
        np = NonPermanent(
            email=cell_unicode(worksheet, row, 0),
            telephone_number1=cell_unicode(worksheet, row, 1).replace(".0", ""),
            vat_number=cell_unicode(worksheet, row, 2)[:9],
            lastname=cell_unicode(worksheet, row, 3),
            firstname=cell_unicode(worksheet, row, 4),
            fathername=cell_unicode(worksheet, row, 5),
            mothername=cell_unicode(worksheet, row, 6),
            profession_code_oaed=cell_unicode(worksheet, row, 7).replace(".0", ""),
            profession=Profession.objects.get(pk=cell_unicode(worksheet, row, 8)),
            transfer_area=TransferArea.objects.get(pk=int(worksheet.cell_value(row, 9))),
            identity_number=cell_unicode(worksheet, row, 10).replace(" ", ""),
            birth_date=cell_unicode(worksheet, row, 11),
            social_security_registration_number=cell_unicode(worksheet, row, 12)[:11].replace(".", ""),
            address=cell_unicode(worksheet, row, 13),
            address_postcode=cell_unicode(worksheet, row, 14)[:5],
            address_city=cell_unicode(worksheet, row, 15),
            educational_level=int(cell_unicode(worksheet, row, 16)[:2]),
            tax_office=cell_unicode(worksheet, row, 17),
            bank=cell_unicode(worksheet, row, 18),
            iban=cell_unicode(worksheet, row, 19)[:27],
            ama=cell_unicode(worksheet, row, 20).replace(".0", "")[:10],
            marital_status=int(cell_unicode(worksheet, row, 21)[:1]))
        try:
            print np
            print np.vat_number, np.profession, np.transfer_area, np.identity_number, \
                np.birth_date, np.ama, np.social_security_registration_number
            np.clean_fields()
            np.save()
        except Exception as ex:
            self.errors += 1
            print(ex)

    def on_file_end(self, workbook, worksheet, total_rows, options):
        print total_rows - 1, " ", self.errors
