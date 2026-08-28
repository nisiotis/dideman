# -*- coding: utf-8 -*-
"""Στήνει το χρωματικό θέμα του admin (django-admin-interface).

Το θέμα είναι εγγραφή στη βάση, όχι ρύθμιση στον κώδικα, οπότε μια καθαρή
εγκατάσταση παίρνει το προεπιλεγμένο πράσινο του Django. Η εντολή δημιουργεί
(ή ενημερώνει) το θέμα της υπηρεσίας και το ενεργοποιεί. Είναι idempotent —
τρέχει όσες φορές θέλει κανείς.

    python manage.py set_admin_theme

Μετά από αυτό, τα χρώματα ρυθμίζονται και από το ίδιο το admin:
Αρχική → Admin Interface → Θέματα.
"""
from django.core.management.base import BaseCommand, CommandError

THEME_NAME = 'Δ.Δ.Ε.'

# Μπλε παλέτα, στη λογική του προεπιλεγμένου admin του Django αλλά πιο σκούρα.
COLORS = {
    'title': 'Δ.Δ.Ε.',
    'title_visible': False,
    'logo_visible': False,
    'css_header_background_color': '#1b4965',
    'css_header_text_color': '#ffffff',
    'css_header_link_color': '#cfe6f5',
    'css_header_link_hover_color': '#ffffff',
    'css_module_background_color': '#1b4965',
    'css_module_background_selected_color': '#15384e',
    'css_module_text_color': '#ffffff',
    'css_module_link_color': '#ffffff',
    'css_module_link_selected_color': '#cfe6f5',
    'css_module_link_hover_color': '#cfe6f5',
    'css_module_rounded_corners': True,
    'css_generic_link_color': '#1b4965',
    'css_generic_link_hover_color': '#15384e',
    'css_save_button_background_color': '#1b4965',
    'css_save_button_background_hover_color': '#15384e',
    'css_save_button_text_color': '#ffffff',
    'css_delete_button_background_color': '#a3372b',
    'css_delete_button_background_hover_color': '#872d23',
    'css_delete_button_text_color': '#ffffff',
    # Τα φίλτρα μας είναι δικά μας (AND/OR), οπότε δεν τα κάνουμε dropdown.
    'list_filter_dropdown': False,
    'list_filter_sticky': True,
    'form_pagination_sticky': True,
    'recent_actions_visible': True,
    'related_modal_active': True,
}


class Command(BaseCommand):
    help = 'Δημιουργεί και ενεργοποιεί το χρωματικό θέμα του admin.'

    def add_arguments(self, parser):
        parser.add_argument('--name', default=THEME_NAME,
                            help='Όνομα θέματος (προεπιλογή: %s)' % THEME_NAME)

    def handle(self, *args, **options):
        try:
            from admin_interface.models import Theme
        except ImportError:
            raise CommandError(
                'Το django-admin-interface δεν είναι εγκατεστημένο. '
                'Εγκαταστήστε το με «pip install django-admin-interface» '
                'και ξανατρέξτε την εντολή.')

        name = options['name']
        theme, created = Theme.objects.get_or_create(name=name)
        for field, value in COLORS.items():
            setattr(theme, field, value)
        theme.active = True          # απενεργοποιεί μόνο του τα υπόλοιπα
        theme.save()
        self.stdout.write(self.style.SUCCESS(
            '%s το θέμα «%s» και ενεργοποιήθηκε.'
            % ('Δημιουργήθηκε' if created else 'Ενημερώθηκε', name)))
