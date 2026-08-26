# -*- coding: utf-8 -*-
"""Shared helpers for the dide xls/xml import management commands.

The leading underscore keeps Django's command autodiscovery from
treating this module as a command of its own (`find_commands` skips
any module in the `commands` package whose name starts with `_`).
"""
from datetime import datetime
from optparse import make_option

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
        print "--f <file>: xls file required / not found"
        exit()
    worksheet = workbook.sheet_by_index(sheet_index) if sheet_index else workbook.sheet_by_index(0)
    return workbook, worksheet


def cell_unicode(worksheet, row, col):
    return unicode(worksheet.cell_value(row, col))


def vat_to_text(value):
    """Normalise an Α.Φ.Μ. (VAT number) cell value to a 9-digit,
    zero-padded string."""
    try:
        v = int(value)
        text = str(v).zfill(9)
    except (TypeError, ValueError):
        text = unicode(value).zfill(9)
    return text[:9]


def find_model_field(model, field_name):
    """Return the model field named field_name, or None if not found."""
    for f in model._meta.fields:
        if f.name == field_name:
            return f
    return None


def confirm(prompt='Continue? '):
    print prompt
    answer = str(raw_input())
    return answer in ('y', 'yes')


# Common optparse options shared by the option-driven (--f/--ci/--ws) commands.
FILE_OPTION = make_option('--f', type=str, help='The xls file')
COLUMN_OPTION = make_option('--ci', type=int, help='The column index')
SHEET_OPTION = make_option('--ws', type=int, help='The sheet index of xls book')


class XlsFileCommand(BaseCommand):
    """Base command for reading one or more xls files, row by row.

    Subclasses implement `process_row` and typically set `start_row`
    (to skip a header row) and override the `on_file_start`/`on_file_end`
    hooks to report progress the way the original single-purpose
    commands did.
    """

    args = '<file ...>'
    sheet_index = 0
    start_row = 0

    def handle(self, *args, **options):
        if not args:
            print "No arguments found"
            return
        for path in args:
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
