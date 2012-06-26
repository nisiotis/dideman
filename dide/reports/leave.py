# -*- coding: utf-8 -*-
from dideman.dide.actions import DocxReport
from dideman.dide.util.common import current_year
from dideman.dide.util.settings import SETTINGS
import datetime
import os


class LeaveDocxReport(DocxReport):
    def __init__(self, short_description, body_template_path,
                 fields, custom_context=None, model_fields=None,
                 include_header=True, include_footer=True):
        context = {'telephone_number':
                       SETTINGS['leaves_contact_telephone_number'],
                   'contact_person': SETTINGS['leaves_contact_person']}
        context.update(custom_context)
        model_fields = model_fields or {}
        model_fields['header_date'] = '{{ date_issued }}'
        super(LeaveDocxReport, self).__init__(
            short_description, os.path.join('leave', body_template_path),
            fields, context, model_fields, include_header, include_footer)

leave_docx_reports = [
    LeaveDocxReport(u'Αναρρωτική Άδεια', 'adeia_aimodosias.xml', ['employee__firstname', 'employee__lastname',
'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration' ],
               {'subject': u'Αναρρωτική Άδεια'},
               {'recipient': '{{ employee__firstname }} {{ employee__lastname }}',
                'cc': [u'1. Ενδιαφερόμενο/η','2. Σχολείο {{ employee__organization_serving  }}',u'3. Α.Φ.']}),

    LeaveDocxReport(u'Ειδική Άδεια αιρετών μελών Ο.Τ.Α.', 'adeia_eidiki_airetoi.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση ειδικής άδειας αιρετών μελών Ο.Τ.Α.'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η','2. Σχολείο {{ employee__organization_serving  }}',u'3. Α.Φ.']}),

    LeaveDocxReport(u'Αναρρωτική Άδεια Αναπληρωτών', 'adeia_anarrotiki_anapliroti.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση αναρρωτικής άδειας αναπληρωτών'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η','2. Σχολείο {{ employee__organization_serving  }}',u'3. Α.Φ.', u'4. Εκκαθαριστή αποδοχών']}),

    LeaveDocxReport(u'Αναρρωτική Άδεια Αναπληρωτών άνευ αποδοχών', 'adeia_anarrotiki_anapliroti_no_pay.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση αναρρωτικής άδειας αναπληρωτή/ωρομισθίου  καθηγητή χωρίς αποδοχές'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η','2. Σχολείο {{ employee__organization_serving  }}',u'3. Α.Φ.', u'4. Εκκαθαριστή αποδοχών']}),                            

    LeaveDocxReport(u'Ειδική Άδεια Τοκετού', 'adeia_anarrotiki_anapliroti.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση ειδικής άδειας λόγω τοκετού'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η','2. Σχολείο {{ employee__organization_serving  }}',u'3. Α.Φ.']}),

    LeaveDocxReport(u'Άδεια Διευκόλυνσης', 'adeia_diefkolinsis.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση άδειας διευκόλυνσης'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η','2. Σχολείο {{ employee__organization_serving  }}',u'3. Α.Φ.']}),

    LeaveDocxReport(u'Κανονική Άδεια Απουσίας', 'adeia_kanoniki.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση κανονικής άδειας απουσίας σε εκπαιδευτικό λειτουργό'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η', '2. Σχολείο {{ employee__organization_serving  }}', u'3. Α.Φ.']}),

    LeaveDocxReport(u'Ειδική Άδειας Εκλογών', 'adeia_eklogon.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση ειδικής άδειας λόγω εκλογών'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η','2. Σχολείο {{ employee__organization_serving  }}',u'3. Α.Φ.']}),

    LeaveDocxReport(u'Άδεια Κύησης - Λοχείας Αναπληρωτών', 'adeia_maternity_anapliroti.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση άδειας Κύησης - Λοχείας αναπληρωτών'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η', '2. Σχολείο {{ employee__organization_serving  }}', u'3. Α.Φ.', u'4. Εκκαθαριστή αποδοχών']}),  

    LeaveDocxReport(u'Ειδική Άδεια Μετεκπαιδεύσεως Εφεδρείας', 'adeia_stratou.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση ειδικής άδειας λόγω μετεκπαιδεύσεως εφεδρείας'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η', '2. Σχολείο {{ employee__organization_serving  }}', u'3. Α.Φ.']}),  

    LeaveDocxReport(u'Άδεια Ανατροφής Παιδιού άνευ αποδοχών', 'adeia_anatrofis_no_pay.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση άδειας χωρίς αποδοχές για ανατροφή παιδιού'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η', '2. Σχολείο {{ employee__organization_serving  }}', u'3. Α.Φ.', u'4. Εκκαθαριστή αποδοχών']}),

    LeaveDocxReport(u'Ειδική Άδεια αιρετών μελών Ο.Τ.Α. άνευ αποδοχών', 'adeia_eidiki_airetoi_no_pay.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση άδειας άνευ αποδοχών σε αιρετό εκπρόσωπο Ο.Τ.Α'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η', '2. Σχολείο {{ employee__organization_serving  }}', u'3. Α.Φ.', u'4. Εκκαθαριστή αποδοχών']}),

    LeaveDocxReport(u'Άδεια άνευ αποδοχών', 'adeia_eidiki_no_pay.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση άδειας άνευ αποδοχών'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η', '2. Σχολείο {{ employee__organization_serving  }}', u'3. Α.Φ.', u'4. Εκκαθαριστή αποδοχών']}),

    LeaveDocxReport(u'Αναρρωτική Άδεια από Πρωτοβάθμια Υγειονομική Επιτροπή', 'adeia_anarrotiki_yg_ep.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση αναρρωτικής άδειας'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η', '2. Σχολείο {{ employee__organization_serving  }}', u'3. Α.Φ.']}),                

    LeaveDocxReport(u'Αναρρωτική Άδεια με Ιατρική Βεβαίωση', 'adeia_anarrotiki_itr_vev.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση αναρρωτικής άδειας '},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η', '2. Σχολείο {{ employee__organization_serving  }}', u'3. Α.Φ.']}),

    LeaveDocxReport(u'Αναρρωτική Άδεια με Υπεύθυνη Δήλωση', 'adeia_anarrotiki_yp_dil.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση αναρρωτικής άδειας '},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η', '2. Σχολείο {{ employee__organization_serving  }}', u'3. Α.Φ.']}),

    LeaveDocxReport(u'Αναρρωτική Άδεια με γνωμάτευση του νοσοκομείου', 'adeia_anarrotiki_gn_nos.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση αναρρωτικής άδειας '},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η', '2. Σχολείο {{ employee__organization_serving  }}', u'3. Α.Φ.']}),

    LeaveDocxReport(u'Αναρρωτική Άδεια με γνωμάτευση του νοσοκομείου', 'adeia_anarrotiki_gn_nos.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση αναρρωτικής άδειας '},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η', '2. Σχολείο {{ employee__organization_serving  }}', u'3. Α.Φ.']}),

    LeaveDocxReport(u'Άδεια ανατροφής τέκνου', 'adeia_anatrofis.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση άδειας ανατροφής τέκνου'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η', '2. Σχολείο {{ employee__organization_serving  }}', u'3. Α.Φ.']}),

    LeaveDocxReport(u'Άδεια ανατροφής τέκνου (Δίδυμα)', 'adeia_anatrofis_didima.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση άδειας ανατροφής τέκνου'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η', '2. Σχολείο {{ employee__organization_serving  }}', u'3. Α.Φ.']}),

    LeaveDocxReport(u'Άδεια ανατροφής τέκνου 3μηνη', 'adeia_anatrofis_3month.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση άδειας ανατροφής τέκνου'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η', '2. Σχολείο {{ employee__organization_serving  }}', u'3. Α.Φ.']}),                

    LeaveDocxReport(u'Άδεια ανατροφής τέκνου 10μηνη', 'adeia_anatrofis_10month.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση άδειας ανατροφής τέκνου'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η', '2. Σχολείο {{ employee__organization_serving  }}', u'3. Α.Φ.']}), 

    LeaveDocxReport(u'Άδεια ανατροφής τέκνου στον Σύζυγο', 'adeia_anatrofis_suzugou.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση άδειας ανατροφής τέκνου'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η', '2. Σχολείο {{ employee__organization_serving  }}', u'3. Α.Φ.']}), 

    LeaveDocxReport(u'Άδεια ανατροφής τέκνου μισή - μισή', 'adeia_anatrofis_half.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση άδειας ανατροφής τέκνου'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η', '2. Σχολείο {{ employee__organization_serving  }}', u'3. Α.Φ.']}), 

    LeaveDocxReport(u'Άδεια Γονική', 'adeia_goniki.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση γονικής άδειας απουσίας'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η', '2. Σχολείο {{ employee__organization_serving  }}', u'3. Α.Φ.']}), 

    LeaveDocxReport(u'Ειδική Άδεια Εξετάσεων - Ορκωμοσίας', 'adeia_eidiki_eksetaseon.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση ειδικής άδειας εξετάσεων - ορκωμοσίας'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'cc': [u'1. Ενδιαφερόμενο/η', '2. Σχολείο {{ employee__organization_serving  }}', u'3. Α.Φ.']}),                 

    LeaveDocxReport(u'Ειδική Άδεια Εξετάσεων Αναπληρωτών', 'adeia_eidiki_eksetaseon_anapliroti.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση ειδικής άδειας εξετάσεων σε αναπληρωτή καθηγητή'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'protocol_number': '{{protocol_number}}',
                'cc': [u'1. Ενδιαφερόμενο/η', '2. Σχολείο {{ employee__organization_serving  }}', u'3. Α.Φ.']}),  

    LeaveDocxReport(u'Άδεια Κύησης', 'adeia_pregnancy.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση άδειας κύησης'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'protocol_number': '{{protocol_number}}',
                'cc': [u'1. Ενδιαφερόμενο/η', '2. Σχολείο {{ employee__organization_serving  }}', u'3. Α.Φ.']}),

    LeaveDocxReport(u'Άδεια Λοχείας', 'adeia_maternity.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση άδειας λοχείας'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'protocol_number': '{{protocol_number}}',
                'cc': [u'1. Ενδιαφερόμενο/η', '2. Σχολείο {{ employee__organization_serving  }}', u'3. Α.Φ.']}),

    LeaveDocxReport(u'Άδεια Κανονική Κυοφορίας με Αποδοχές', 'adeia_pregnancy_normal.xml', 
               ['employee__firstname', 'employee__lastname', 'profession', 'employee__organization_serving', 
                'employee__fathername', 'order', 'date_from', 'date_to', 'protocol_number', 'duration', 'date_issued'],
               {'subject': u'Χορήγηση κανονικής άδειας κυοφορίας με αποδοχές'},
               {'recipient': '{{ employee__lastname }} {{ employee__firstname }}',
                'protocol_number': '{{protocol_number}}',
                'cc': [u'1. Ενδιαφερόμενο/η', '2. Σχολείο {{ employee__organization_serving  }}', u'3. Α.Φ.']}),
                ]
