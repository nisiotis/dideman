# -*- coding: utf-8 -*-
from dideman.dide.actions import DocxReport
from dideman.dide.util.common import current_year, current_year_date_to_half
from dideman.dide.util.settings import SETTINGS
import datetime
import os


class NonPermanentDocxReport(DocxReport):
    def __init__(self, short_description, body_template_path, fields,
                 custom_context=None, model_fields=None, include_header=True,
                 include_footer=True):
        context = {'telephone_number':
                       SETTINGS['substitutes_contact_telephone_number'],
                   'contact_person': SETTINGS['substitutes_contact_person']
                   }
        context.update(custom_context)
        model_fields = model_fields or {}
        super(NonPermanentDocxReport, self).__init__(
            short_description, os.path.join('nonpermanent',
                                            body_template_path),
            fields, context, model_fields, include_header, include_footer)

nonpermanent_docx_reports = [
    NonPermanentDocxReport(u'Ανακοίνωση Τοποθέτησης', 'temporary_post.xml',
               ['firstname', 'lastname', 'profession',
                'fathername', 'organization_serving',
                'current_order__order_end_manager'],
               {'subject': u'Ανακοίνωση Αυτοδίκαιης Απόλυσης'},
               {'recipient': '{{lastname}} {{firstname}}',
                'cc': ['{{organization_serving}}']}),
    NonPermanentDocxReport(u'Αυτοδίκαιη Απόλυση', 'apolisi.xml',
               ['firstname', 'lastname', 'profession',
                'fathername', 'organization_serving',
                'current_order__order_end_manager'],
               {'subject': u'Αυτοδίκαιη Απόλυση',
                'end_date': current_year_date_to_half().strftime('%d-%m-%Y')},
               {'recipient': '{{lastname}} {{firstname}}'}),
   NonPermanentDocxReport(u'Βεβαίωση Προϋπηρεσίας', 'proypiresia.xml',
               ['firstname', 'lastname', 'profession', 'type',
                'profession__description', 'fathername', 'organization_serving',
                'current_order__order_start_manager',
                'current_order__order_end_manager',
                'current_order__order',
                'current_order__date',
                'current_order__order_pysde'],
               {'subject': u'Βεβαίωση Προϋπηρεσίας',
                'end_date': current_year_date_to_half().strftime('%d-%m-%Y')},
               {'recipient': '{{lastname}} {{firstname}}'})
]
