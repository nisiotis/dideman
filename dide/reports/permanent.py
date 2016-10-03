# -*- coding: utf-8 -*-
from dideman.dide.actions import DocxReport
from dideman.lib.date import current_year
from dideman.dide.util.settings import SETTINGS
import datetime
import os


class ProagDocxReport(DocxReport):
    def __init__(self, short_description, body_template_path, fields,
                 custom_context=None, model_fields=None, include_header=True,
                 include_footer=True):
        context = {'telephone_number': SETTINGS['proagogon_contact_telephone_number'],
                   'contact_person': SETTINGS['proagogon_contact_person'],
                   'email': SETTINGS['proagogon_email_staff']}
        context.update(custom_context)
        model_fields = model_fields or {}
        super(ProagDocxReport, self).__init__(
            short_description, os.path.join('permanent',
                                            body_template_path),
            fields, context, model_fields, include_header, include_footer)


class PermanentDocxReport(DocxReport):
    def __init__(self, short_description, body_template_path, fields,
                 custom_context=None, model_fields=None, include_header=True,
                 include_footer=True):
        context = {'telephone_number':
                       SETTINGS['transfers_contact_telephone_number'],
                   'contact_person': SETTINGS['transfers_contact_person'],
                   'email': SETTINGS['email_staff']
                   }
        context.update(custom_context)
        model_fields = model_fields or {}
        super(PermanentDocxReport, self).__init__(
            short_description, os.path.join('permanent',
                                            body_template_path),
            fields, context, model_fields, include_header, include_footer)

proag_docx_reports = [
    ProagDocxReport(u'Βεβαίωση ελέγχου γνησιότητας δικαιολογητικών', 'permanent_docs_authenticity.xml',
                    ['firstname', 'lastname', 'profession', 'profession__description',
                     'fathername', 'registration_number', 'checked_qualifications'],
                    {'subject': u'Βεβαίωση ελέγχου γνησιότητας δικαιολογητικών προσωπικού μητρώου εκπαιδευτικού Δ.Ε.'},
                    {'recipient': 'Υπουργείο Παιδείας, Έρευνας και Θρησκευμάτων, Γενική Διεύθυνση Προσωπικού Π.Ε. & Δ.Ε., Διεύθυνση Διοίκησης Προσωπικού Δ.Ε., Τμήμα Β΄, Α. Παπανδρέου 37, 151 80 Μαρούσι Αττικής',
                     'cc': ['{{ lastname }} {{ firstname }}']}),
]


permanent_docx_reports = [

    PermanentDocxReport(u'Προσωρινή τοποθέτηση', 'temporary_post.xml',
               ['firstname', 'lastname', 'profession',
                'fathername', 'organization_serving',
                'organization_serving__order',
                'organization_serving__order_pysde'],
               {'subject': u'Ανακοίνωση προσωρινής τοποθέτησης'},
               {'recipient': '{{ lastname }} {{ firstname }}',
                'order': '{{ organization_serving__order }}',
                'order_pysde': '{{ organization_serving__order_pysde }}',
                'cc': ['{{ organization_serving  }}']}),

    PermanentDocxReport(u'Απόσπαση προς το συμφέρον της υπηρεσίας',
                        'apospasi_symferon.xml',
               ['firstname', 'lastname', 'profession',
                'fathername', 'permanent_post', 'organization_serving',
                'organization_serving__order',
                'organization_serving__order_pysde'],
               {'subject': u'Ανακοίνωση απόσπασης',
                'current_year': current_year()},
               {'recipient': '{{ lastname }} {{ firstname }}',
                'order': '{{ organization_serving__order }}',
                'order_pysde': '{{ organization_serving__order_pysde }}',
                'cc': ['{{ permanent_post }}', '{{ organization_serving  }}',
                       u'Π.Μ. Υπαλλήλου']}),

    PermanentDocxReport(u'Απόσπαση μετά από αίτηση',
                        'apospasi_meta_apo_aitisi.xml',
               ['firstname', 'lastname', 'profession',
                'fathername', 'permanent_post', 'organization_serving',
                'organization_serving__order',
                'organization_serving__order_pysde'],
               {'subject': u'Ανακοίνωση απόσπασης',
                'current_year': current_year()},
               {'recipient': '{{ lastname }} {{ firstname }}',
                'order': '{{ organization_serving__order }}',
                'order_pysde': '{{ organization_serving__order_pysde }}',
                'cc': ['{{ permanent_post }}', '{{ organization_serving  }}',
                       u'Π.Μ. Υπαλλήλου']}),

    PermanentDocxReport(u'Απόσπαση σε Α.Ε.Ι.', 'apospasi_aei.xml',
               ['firstname', 'lastname', 'profession',
                'fathername', 'permanent_post', 'organization_serving',
                'organization_serving__order',
                'organization_serving__order_pysde'],
               {'subject': u'Απόσπαση σε Α.Ε.Ι.',
                'current_year': current_year()},
               {'recipient': '{{ lastname }} {{ firstname }}',
                'order': '{{ organization_serving__order }}',
                'order_pysde': '{{ organization_serving__order_pysde }}',
                'cc': ['{{ permanent_post }}', '{{ organization_serving  }}',
                       u'Π.Μ. Υπαλλήλου']}),

    PermanentDocxReport(u'Απόσπαση λόγω υπεραριθμίας',
                        'apospasi_yperarithmias.xml',
               ['firstname', 'lastname', 'profession',
                'fathername', 'permanent_post', 'organization_serving',
                'organization_serving__order',
                'organization_serving__order_pysde'],
               {'subject': u'Ανακοίνωση απόσπασης λόγω υπεραριθμίας',
                'current_year': current_year()},
               {'recipient': '{{ lastname }} {{ firstname }}',
                'order': '{{ organization_serving__order }}',
                'order_pysde': '{{ organization_serving__order_pysde }}',
                'cc': ['{{ permanent_post }}', '{{ organization_serving  }}',
                       u'Π.Μ. Υπαλλήλου']}),

    PermanentDocxReport(u'Ανάκληση απόσπασης εκτός Π.Υ.Σ.Δ.Ε.',
                        'anaklisi_ektos_pysde.xml',
               ['firstname', 'lastname', 'profession',
                'fathername', 'permanent_post', 'organization_serving',
                'organization_serving__order',
                'organization_serving__order_pysde'],
               {'subject': u'Ανάκληση απόσπασης',
                'current_year': current_year()},
               {'recipient': '{{ lastname }} {{ firstname }}',
                'order': '{{ organization_serving__order }}',
                'order_pysde': '{{ organization_serving__order_pysde }}',
                'cc': ['{{ permanent_post }}', '{{ organization_serving  }}',
                       u'Π.Μ. Υπαλλήλου']}),

    PermanentDocxReport(u'Ανάκληση απόσπασης εντός Π.Υ.Σ.Δ.Ε.',
                        'anaklisi_entos_pysde.xml',
               ['firstname', 'lastname', 'profession',
                'fathername', 'permanent_post', 'organization_serving',
                'organization_serving__order',
                'organization_serving__order_pysde'],
               {'subject': u'Ανάκληση απόσπασης',
                'current_year': current_year()},
               {'recipient': '{{ lastname }} {{ firstname }}',
                'order': '{{ organization_serving__order }}',
                'order_pysde': '{{ organization_serving__order_pysde }}',
                'cc': ['{{ permanent_post }}', '{{ organization_serving  }}',
                       u'Π.Μ. Υπαλλήλου']}),

    PermanentDocxReport(u'Απόσπαση σε άλλο Π.Υ.Σ.Δ.Ε.',
                        'apospasi_allo_pysde.xml',
               ['firstname', 'lastname', 'profession',
                'fathername', 'permanent_post', 'organization_serving',
                'organization_serving__order',
                'organization_serving__order_pysde'],
               {'subject': u'Ανακοίνωση απόσπασης σε άλλο Π.Υ.Σ.Δ.Ε.',
                'current_year': current_year()},
               {'recipient': '{{ lastname }} {{ firstname }}',
                'order': '{{ organization_serving__order }}',
                'order_pysde': '{{ organization_serving__order_pysde }}',
                'cc': ['{{ permanent_post }}', '{{ organization_serving  }}',
                       u'Π.Μ. Υπαλλήλου']}),

    PermanentDocxReport(u'Απόσπαση σε Διεύθυνση ή Γραφείο',
                        'apospasi_diefthinseis_grafeia.xml',
               ['firstname', 'lastname', 'profession',
                'fathername', 'permanent_post', 'organization_serving',
                'organization_serving__order',
                'organization_serving__order_pysde'],
               {'subject': u'Ανακοίνωση απόσπασης σε Διεύθυνση ή Γραφείο.',
                'current_year': current_year()},
               {'recipient': '{{ lastname }} {{ firstname }}',
                'order': '{{ organization_serving__order }}',
                'order_pysde': '{{ organization_serving__order_pysde }}',
                'cc': ['{{ permanent_post }}', '{{ organization_serving  }}',
                       u'Π.Μ. Υπαλλήλου']}),

    PermanentDocxReport(u'Απόσπαση σε Μουσικό Σχολείο', 'apospasi_mousiko.xml',
               ['firstname', 'lastname', 'profession',
                'fathername', 'permanent_post', 'organization_serving',
                'organization_serving__order',
                'organization_serving__order_pysde'],
               {'subject': u'Ανακοίνωση απόσπασης σε Μουσικό Σχολείο.',
                'current_year': current_year()},
               {'recipient': '{{ lastname }} {{ firstname }}',
                'order': '{{ organization_serving__order }}',
                'order_pysde': '{{ organization_serving__order_pysde }}',
                'cc': ['{{ permanent_post }}', '{{ organization_serving  }}',
                       u'Π.Μ. Υπαλλήλου']}),

    PermanentDocxReport(u'Απόσπαση σε Τ.Ε.Ι.', 'apospasi_tei.xml',
               ['firstname', 'lastname', 'profession',
                'fathername', 'permanent_post', 'organization_serving',
                'organization_serving__order',
                'organization_serving__order_pysde'],
               {'subject': u'Απόσπαση σε Τ.Ε.Ι.',
                'current_year': current_year()},
               {'recipient': '{{ lastname }} {{ firstname }}',
                'order': '{{ organization_serving__order }}',
                'order_pysde': '{{ organization_serving__order_pysde }}',
                'cc': ['{{ permanent_post }}', '{{ organization_serving  }}',
                       u'Π.Μ. Υπαλλήλου']}),

    PermanentDocxReport(u'Ανακοίνωση αριθμού μητρώου', 'am.xml',
               ['firstname', 'lastname', 'profession',
                'fathername', 'registration_number'],
               {'subject': u'Ανακοίνωση αριθμού μητρώου'},
               {'recipient': '{{ lastname }} {{ firstname }}'}),

    PermanentDocxReport(u'Άσκηση Ιδιωτικού Έργου με Αμοιβή',
                        'askisi_idiotikou_ergou.xml',
               ['firstname', 'lastname', 'profession',
                'fathername'],
               {'subject': u'Άσκηση Ιδιωτικού Έργου με Αμοιβή',
                'current_year': current_year()},
               {'recipient': '{{ lastname }} {{ firstname }}',
                'cc': [u'Δ.Δ.Ε. Δωδεκανήσου', u'Π.Μ. Υπαλλήλου']}),

    PermanentDocxReport(u'Βεβαίωση Μόνιμου Υπαλλήλου', 'monimos.xml',
               ['firstname', 'lastname', 'profession', 
                'profession__description',
                'fathername', 'registration_number', 'permanent_post'],
               {'subject': u'Βεβαίωση Μόνιμου Υπαλλήλου'},
               {'recipient': '{{ lastname }} {{ firstname }}'}),

    PermanentDocxReport(u'Διάθεση Καθηγητή', 'diathesi.xml',
               ['firstname', 'lastname', 'profession',
                'fathername', 'registration_number', 'organization_serving',
                'current_year_services'],
               {'subject': u'Ανακοίνωση Διάθεσης',
                'current_year': current_year()},
               {'recipient': '{{ lastname }} {{ firstname }}',
                'services':
                    lambda d: [s.organization.name for s in d['current_year_services']]}),

    PermanentDocxReport(u'Βεβαίωση προϋπηρεσίας', 'proypiresia.xml',
               ['firstname', 'lastname', 'profession', 'date_hired',
                'fathername', 'registration_number',
                'permanent_post', 'order_hired', 'profession__description',
                'formatted_recognised_experience', 'total_service', 'total_not_service'],
               {'subject': u'Βεβαίωση προϋπηρεσίας'},
               {'recipient': '{{lastname}} {{firstname}}',
                'date_hired': lambda d: d['date_hired'].strftime('%d-%m-%Y')}),

    PermanentDocxReport(u'Πρωτόκολλο ορκωμοσίας', 'protokolo.xml',
               ['firstname', 'lastname', 'profession', 'order_hired',
                'profession__description', 'fathername'],
               {'weekday': datetime.datetime.now().strftime('%A')},
               include_header=False, include_footer=False),
]
