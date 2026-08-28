# -*- coding: utf-8 -*-
from dideman.dide.actions import DocxReport
from dideman.dide.util.settings import SETTINGS
import os

def cc(obj):
    ret = []
    if hasattr(obj['employee__subclass__organization_serving'], 'organization'):
        ret.append(obj['employee__subclass__organization_serving'].organization.name)
    if hasattr(obj['employee__subclass__permanent_post'], 'organization'):
        if obj['employee__subclass__permanent_post'].organization.name not in [obj['employee__subclass__organization_serving'].organization.name, '-']:
            ret.append(obj['employee__subclass__permanent_post'].organization.name)
    elif hasattr(obj['employee__subclass__temporary_position'], 'organization'):
        if obj['employee__subclass__temporary_position'] != obj['employee__subclass__organization_serving']:
            ret.append(obj['employee__subclass__temporary_position'].organization.name)
    if obj['employee__subclass__serving_type__id'] != 1:
        ret.append('ΑΛΛΟ Π.Υ.Σ.Δ.Ε.')
    if obj['leave__not_paying']:
        ret.append('Εκκαθαριστής')
    
    if obj['employee__subclass__serving_type__id'] == 1:
        ret.append('Α.Φ. (Δ.Δ.Ε. Δωδεκανήσου)')
    else:
        ret.append('Α.Φ.')
    return ret


class LeaveDocxReport(DocxReport):
    def __init__(self, short_description, body_template_path,
                 fields=None, custom_context=None, model_fields=None,
                 include_header=True, include_footer=True):

        fields = fields or ['employee__firstname', 'employee__lastname',
                            'employee__subclass__serving_type',
                            'profession', 'employee__subclass__organization_serving',
                            'employee__subclass__permanent_post',
                            'employee__subclass__temporary_position',
                            'employee__subclass__serving_type__id',
                            'employee__fathername', 'order',
                            'date_from', 'date_to', 'protocol_number',
                            'duration', 'date_issued', 'leave__not_paying']

        context = {'telephone_number':
                       SETTINGS['leaves_contact_telephone_number'],
                   'contact_person': SETTINGS['leaves_contact_person'],
                   'email': SETTINGS['email_leaves']}
        if custom_context:
            context.update(custom_context)

        if not model_fields:
            model_fields = {'header_date': '{{date_issued}}',
                            'recipient':
                                '{{employee__firstname}}'
                            ' {{employee__lastname}}'}

            model_fields['cc'] = cc
        super(LeaveDocxReport, self).__init__(
            short_description, os.path.join('leave', body_template_path),
            fields, context, model_fields, include_header, include_footer)


leave_docx_reports = [
    LeaveDocxReport('Aιμοδοτική - παροχής αιμοπεταλίων', 'adeia_aimodosias-aimopetalia.xml',
                    custom_context={'subject': 'Χορήγηση άδειας λόγω αιμοληψίας ή λήψης αιμοπεταλίων'}),
    LeaveDocxReport('Aιμοδοτική ', 'adeia_aimodosias.xml',
                    custom_context={'subject': 'Χορήγηση άδειας λόγω αιμοληψίας'}),
    LeaveDocxReport('Συνδικαλιστική',
                    'adeia_syndikalistiki.xml',
                    custom_context={'subject':  'Χορήγηση Συνδικαλιστικής Άδειας '}),

    LeaveDocxReport('Τοκετού Πατέρα', 'adeia_goniki_patera_toketou.xml',
                    custom_context={'subject': 'Χορήγηση ειδικής άδειας λόγω τοκετού'}),

    LeaveDocxReport('Ειδική 22 ημερών', 'adeia_22.xml',
                    custom_context={'subject': 'Χορήγηση ειδικής άδειας'}),
    LeaveDocxReport('Ειδική 22 ημερών για δικαστικο συμπαραστατη', 'adeia_22diksymp.xml',
                    custom_context={'subject': 'Χορήγηση ειδικής άδειας υπαλλήλους που έχουν οριστεί δικαστικοί  '
                                    'συμπαραστάτες και τους έχει ανατεθει δικαστικώς η επιμέλεια..'}),
    LeaveDocxReport('Ειδική 6 ημερών', 'adeia_6.xml',
                    custom_context={'subject': 'Χορήγηση ειδικής άδειας'}),
    LeaveDocxReport('Ειδική 6 ημερών 50%%', 'adeia_6_teknoy.xml',
                    custom_context={'subject': 'Χορήγηση ειδικής άδειας 6 ημερών λόγω αναπηρίας'}),
    LeaveDocxReport('Διευκόλυνσης', 'adeia_diefkolinsis.xml',
                    custom_context={'subject':
                                        'Χορήγηση άδειας διευκόλυνσης'}),
    LeaveDocxReport('Κανονική', 'adeia_kanoniki.xml',
                    custom_context={'subject': 'Χορήγηση κανονικής άδειας '
                                    'απουσίας'}),
    LeaveDocxReport('Εκλογική', 'adeia_eklogon.xml',
                    custom_context={'subject': 'Χορήγηση ειδικής άδειας λόγω'
                                    ' εκλογών'}),
    LeaveDocxReport('Ειδική άδεια αιρετών Ο.Τ.Α.', 'adeia_airetwn_ota.xml',
                    custom_context={'subject': 'Χορήγηση άδειας άσκησης καθηκόντων'
                                    ' αιρετών μελών ΟΤΑ Α\' & Β\' βαθμού.'}),
    LeaveDocxReport('Ανατροφής (Άνευ Αποδοχών)', 'adeia_anatrofis_no_pay.xml',
                    custom_context={'subject':
                                    'Χορήγηση άδειας χωρίς αποδοχές για ανατροφή παιδιού'}),
    LeaveDocxReport('Ανατροφής (4 μηνών - Άνευ Αποδοχών)', 'adeia_anatrofis_no_pay_4_mines.xml',
                    custom_context={'subject':
                                    'Χορήγηση άδειας χωρίς αποδοχές για ανατροφή παιδιού (4 μηνών).'}),
    LeaveDocxReport('Ανατροφής (Άνευ Αποδοχών)', 'adeia_anatrofis_no_pay_4_mines.xml',
                    custom_context={'subject':
                                    'Χορήγηση άδειας χωρίς αποδοχές'
                                    ' για ανατροφή παιδιού', 'cc':  ['ΟΠΑΔ'] }),
    LeaveDocxReport('Ειδική Άδεια αιρετών μελών Ο.Τ.Α. άνευ αποδοχών',
                    'adeia_eidiki_airetoi_no_pay.xml',
                    custom_context={'subject':
                                        'Χορήγηση άδειας άνευ αποδοχών σε '
                                    'αιρετό εκπρόσωπο'
                                    ' Ο.Τ.Α'}),
    LeaveDocxReport('Άνευ Αποδοχών', 'adeia_eidiki_no_pay.xml',
                    custom_context={'subject':
                                        'Χορήγηση άδειας άνευ αποδοχών'}),
    LeaveDocxReport('Αναρρωτική (από Α\'Βάθμια Υγειονομική Επιτροπή)',
                    'adeia_anarrotiki_yg_ep.xml',
                    custom_context={'subject':
                                        'Χορήγηση αναρρωτικής άδειας'}),
    LeaveDocxReport('Αναρρωτική (Βραχυχρόνια)',
                    'adeia_anarrotiki_short.xml',
                    custom_context={'subject':
                                        'Χορήγηση αναρρωτικής άδειας'}),
    LeaveDocxReport('Αναρρωτική ασθένειας τέκνου',
                    'adeia_anarrotiki_teknou.xml',
                    custom_context={'subject':
                                        'Χορήγηση άδειας ασθένειας τέκνου'}),
    LeaveDocxReport('Αναρρωτική (Επέμβαση)',
                'adeia_anarrotiki_epemvasi.xml',
                custom_context={'subject':
                                    'Χορήγηση αναρρωτικής άδειας'}),

    LeaveDocxReport('Ανατροφής (3 μήνες - τρίτου τέκνου)',
                    'adeia_anatrofis_3months.xml',
                    custom_context={'subject':
                                        'Χορήγηση άδειας τριών μηνών για '
                                    'ανατροφή τρίτου τέκνου και άνω.'}),

    LeaveDocxReport('Ανατροφής (9 μήνες)', 'adeia_anatrofis_9months.xml',
                    custom_context={'subject':
                                        'Χορήγηση άδειας ανατροφής τέκνου'}),

    LeaveDocxReport('Ανατροφής (10 μήνες)', 'adeia_anatrofis_10months.xml',
                    custom_context={'subject':
                                        'Χορήγηση άδειας ανατροφής τέκνου (10 μηνών)'}),

    LeaveDocxReport('Γονική', 'adeia_goniki.xml',
                    custom_context={'subject':
                                        'Χορήγηση γονικής άδειας απουσίας'}),

    LeaveDocxReport('Εξετάσεων', 'adeia_eidiki_eksetaseon.xml',
                    custom_context={'subject':
                                        'Χορήγηση ειδικής άδειας εξετάσεων'}),

    LeaveDocxReport('Κύησης', 'adeia_pregnancy.xml',
                    custom_context={'subject':
                                        'Χορήγηση άδειας κύησης'}),

    LeaveDocxReport('Λοχείας', 'adeia_maternity.xml',
                    custom_context={'subject':
                                        'Χορήγηση άδειας λοχείας'}),

    LeaveDocxReport('Κυοφορίας',
                    'adeia_pregnancy_normal.xml',
                    custom_context={'subject':
                                        'Χορήγηση κανονικής άδειας κυοφορίας με αποδοχές'}),

    LeaveDocxReport('Επαπειλούμενης κύησης', 'adeia_epapiloumenis.xml',
                    custom_context={'subject':
                                        'Χορήγηση αναρρωτικής άδειας'}),
    LeaveDocxReport('Υποβοηθουμενης αναπαραγωγής', 'adeia_eksoswmatikhs.xml',
                    custom_context={'subject':
                                        'Χορήγηση άδειας σε περίπτωση ιατρικώς υποβοηθούμενης αναπαραγωγής'}),
    LeaveDocxReport('Εκπαιδευτική Επιμορφώσεων', 'ekpaideftiki_epimorfoseon.xml',
                    custom_context={'subject':
                                        'Χορήγηση ειδικής άδειας απουσίας σε εκπαιδευτικό για επιμορφωτικούς ή επιστημονικούς λόγους.'}),

    LeaveDocxReport('Ανατροφής (__ου πολύδυμου)', 'polidimou.xml',
                    custom_context={'subject':
                                        'Χορήγηση άδειας ανατροφής τέκνου (6άμηνη __ου πολύδυμου)'}),

    LeaveDocxReport('Υιοθεσίας (Τρίμηνη)', 'trimini_yiothesias.xml',
                    custom_context={'subject':
                                        'Χορήγηση τρίμηνης άδειας υιοθεσίας'}),

    LeaveDocxReport('ετήσιου γυναικολογικού ελέγχου', 'ethsioy_gynaikologikoy.xml',
                    custom_context={'subject':
                                        'Χορήγηση άδειας για ετήσιο γυναικολογικό έλεγχο'}),

    LeaveDocxReport('Ανατροφής (Υπόλοιπο)', 'anatrofis_ypoloipo.xml',
                    custom_context={'subject':
                                        'Χορήγηση άδειας ανατροφής τέκνου (υπόλοιπο)'}),

    LeaveDocxReport('Αναρρωτική άνευ αποδοχών', 'anarrotiki_xoris_apodoxes.xml',
                    custom_context={'subject':
                                    'Χορήγηση αναρρωτικής άδειας'}),

    LeaveDocxReport('ανατροφής τέκνου χωρίς αποδοχές Ν4830_2021', 'adeia_anatrofis_no_pay2021.xml',
                    custom_context={'subject':
                                        'Χορήγηση άδειας άνευ αποδοχών για ανατροφή τέκνου ως 8 ετών'}),

    LeaveDocxReport('Ειδικη Ασθένειας συζύγου ή ανήλικου τέκνου', 'adeia_asth_teknou_syzygoy_over22.xml',
                    custom_context={'subject':
                                        'Χορήγηση άδειας λόγω ασθένειας συζύγου ή ανήλικου τέκνου'}),
    LeaveDocxReport('Αναρρωτική Ειδικού σκοπού covid19', 'adeia_covid_anar.xml',
                    custom_context={'subject':
                                        'Χορήγηση αναρρωτικής άδειας ειδικού σκοπού λόγω Covid-19»'}),
    ]
