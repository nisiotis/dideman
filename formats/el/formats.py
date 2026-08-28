# -*- coding: utf-8 -*-
"""Ελληνικές μορφές ημερομηνίας, όπως τις είχε το έργο.

Μέχρι το Django 4.x το έργο δούλευε με ``USE_L10N = False``, οπότε ίσχυαν
απευθείας τα ``DATE_FORMAT``/``DATE_INPUT_FORMATS`` των settings. Από το
Django 5.0 το ``USE_L10N`` καταργήθηκε και η τοπικοποίηση είναι πάντα
ενεργή, οπότε θα υπερίσχυαν οι μορφές του locale ``el`` του Django
(``d/m/Y``, χωρίς την παύλα στην εισαγωγή). Το module αυτό, μέσω του
``FORMAT_MODULE_PATH``, επαναφέρει τις μορφές που περιμένουν χρήστες και
πρότυπα.
"""
DATE_FORMAT = 'd-m-Y'
DATETIME_FORMAT = 'd-m-Y H:i'
SHORT_DATE_FORMAT = 'd-m-Y'
SHORT_DATETIME_FORMAT = 'd-m-Y H:i'
TIME_FORMAT = 'H:i'

DATE_INPUT_FORMATS = [
    '%d-%m-%Y',
    '%d/%m/%Y',
    '%Y-%m-%d',
]
DATETIME_INPUT_FORMATS = [
    '%d-%m-%Y %H:%M:%S',
    '%d-%m-%Y %H:%M',
    '%d/%m/%Y %H:%M:%S',
    '%d/%m/%Y %H:%M',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M',
]

DECIMAL_SEPARATOR = ','
THOUSAND_SEPARATOR = '.'
NUMBER_GROUPING = 3
