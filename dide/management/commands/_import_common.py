# -*- coding: utf-8 -*-
"""Shared helpers for the dide xls/xml import management commands.

The leading underscore keeps Django's command autodiscovery from
treating this module as a command of its own (`find_commands` skips
any module in the `commands` package whose name starts with `_`).
"""
from datetime import datetime
import xlrd
from django.core.management.base import BaseCommand


def open_worksheet(path, sheet_index=0):
    """Open an xls file and return (workbook, worksheet)."""
    workbook = xlrd.open_workbook(path)
    worksheet = workbook.sheet_by_index(sheet_index)
    return workbook, worksheet


def open_worksheet_or_exit(path, sheet_index=None):
    """Like open_worksheet, but for the option-driven commands: prints
    the same error message they used to and exits the process rather
    than raising, instead of leaving every caller to repeat the try/except.
    """
    try:
        workbook = xlrd.open_workbook(path)
    except Exception:
        print("--f <file>: xls file required / not found")
        exit()
    worksheet = workbook.sheet_by_index(sheet_index) if sheet_index else workbook.sheet_by_index(0)
    return workbook, worksheet


def cell_unicode(worksheet, row, col):
    return str(worksheet.cell_value(row, col))


def vat_to_text(value):
    """Normalise an Α.Φ.Μ. (VAT number) cell value to a 9-digit,
    zero-padded string."""
    try:
        v = int(value)
        text = str(v).zfill(9)
    except (TypeError, ValueError):
        text = str(value).zfill(9)
    return text[:9]


def find_model_field(model, field_name):
    """Return the model field named field_name, or None if not found."""
    for f in model._meta.fields:
        if f.name == field_name:
            return f
    return None


def confirm(prompt='Continue? '):
    print(prompt)
    answer = str(input())
    return answer in ('y', 'yes')


# Το option_list/optparse αντικαταστάθηκε από argparse στο Django 1.10.
def add_file_options(parser, extra=()):
    """Οι κοινές επιλογές --f/--ci/--ws των εντολών εισαγωγής."""
    parser.add_argument('--f', type=str, help='The xls file')
    parser.add_argument('--ci', type=int, help='The column index')
    parser.add_argument('--ws', type=int, help='The sheet index of xls book')
    for args, kwargs in extra:
        parser.add_argument(*args, **kwargs)


class XlsFileCommand(BaseCommand):
    """Base command for reading one or more xls files, row by row.

    Subclasses implement `process_row` and typically set `start_row`
    (to skip a header row) and override the `on_file_start`/`on_file_end`
    hooks to report progress the way the original single-purpose
    commands did.
    """

    sheet_index = 0
    start_row = 0

    def add_arguments(self, parser):
        # Από το Django 1.10 τα ορίσματα θέσης δηλώνονται ρητά στο argparse·
        # το παλιό `args = '<file ...>'` δεν έχει καμία επίδραση πλέον και
        # χωρίς αυτό η εντολή απορρίπτει τα αρχεία ως «unrecognized».
        parser.add_argument('files', nargs='*', help='Τα αρχεία xls')

    def handle(self, *args, **options):
        paths = list(args) or options.get('files') or []
        if not paths:
            print("No arguments found")
            return
        for path in paths:
            self.process_file(path, options)

    def process_file(self, path, options):
        workbook, worksheet = open_worksheet(path, self.sheet_index)
        self.on_file_start(workbook, worksheet, options)
        curr_row = self.start_row
        while curr_row < worksheet.nrows:
            self.process_row(workbook, worksheet, curr_row, options)
            curr_row += 1
        self.on_file_end(workbook, worksheet, curr_row, options)

    def on_file_start(self, workbook, worksheet, options):
        pass

    def process_row(self, workbook, worksheet, row, options):
        raise NotImplementedError

    def on_file_end(self, workbook, worksheet, total_rows, options):
        pass
