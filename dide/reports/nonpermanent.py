# -*- coding: utf-8 -*-
from dideman.dide.actions import DocxReport
from dideman.lib.date import current_year, current_year_date_to_half
from dideman.dide.util.settings import SETTINGS
import datetime
import os


class NonPermanentDocxReport(DocxReport):
    def __init__(self, short_description, body_template_path, fields,
                 custom_context=None, model_fields=None, include_header=True,
                 include_footer=True):
        context = {'telephone_number':
                       SETTINGS['substitutes_contact_telephone_number'],
                   'contact_person': SETTINGS['substitutes_contact_person'],
                   'email': SETTINGS['email_substitutes']}
        context.update(custom_context)
        model_fields = model_fields or {}
        super(NonPermanentDocxReport, self).__init__(
            short_description, os.path.join('nonpermanent',
                                            body_template_path),
            fields, context, model_fields, include_header, include_footer)


def protocol_number(order):
    try:
        return order.split("/")[0]
    except:
        return ''
    

nonpermanent_docx_reports = [
    NonPermanentDocxReport(u'Ανακοίνωση Τοποθέτησης', 'temporary_post.xml',
                           ['firstname', 'lastname', 'profession', 'order',
                            'fathername', 'current_placement', 'current_transfer_area'],
                           {'subject': u'Ανακοίνωση Τοποθέτησης'},
                           {'recipient': '{{lastname}} {{firstname}}',
                            'protocol_number': lambda d: d['order'].order_start_manager,
                            'cc': ['{{current_placement}}']}),

    NonPermanentDocxReport(u'Αυτοδίκαιη Απόλυση', 'apolisi-proypiresia.xml',
                           ['profession__description', 'firstname', 'current_placement', 
                            'current_placement__substituteplacement__date_from_show', 'current_placement__date_to',
                            'current_placement__date_from',
                            'lastname', 'profession', 'current_placement',
                            'order__order_end_manager', 'experience', 'experience_salary', 
                            'current_placement', 'fathername',
                            'order__order_start_manager', 'type', 'order', 'order__order', 'order__date'],
                           {'subject': u'Αυτοδίκαιη Απόλυση'},
                           {'recipient': '{{lastname}} {{firstname}}',
                            'protocol_number': lambda d: protocol_number(d['order'].order_end_manager),
                            'cc': ['{{current_placement}}', 'Α.Φ.']})
]
