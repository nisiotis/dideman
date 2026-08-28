# -*- coding: utf-8 -*-
"""Τιμές που χρειάζονται σε κάθε σελίδα του dideman."""
import django

from dideman.dide.util.settings import SETTINGS


def dide(request):
    """Το υποσέλιδο εμφανίζεται παντού, οπότε η έκδοση του Django και η έδρα
    πρέπει να υπάρχουν σε κάθε context — και στο admin και στις σελίδες των
    υπαλλήλων. Μέχρι τώρα το django_version το έβαζε μόνο η index view."""
    return {
        'django_version': django.get_version(),
        'dide_place': SETTINGS['dide_place'],
    }
