# -*- coding: utf-8 -*-
from dideman.dide.actions import DocxReport
from dideman.dide.util.common import current_year
from dideman.dide.util.settings import SETTINGS
import datetime
import os


def cc(obj):
    ret = [obj['organization_serving']]
    p = obj['employee__permanent__permanent_post']
    s = obj['organization_serving']
    if obj['employee__permanent__permanent_post'] != \
            obj['organization_serving']:
        ret.append(obj['employee__permanent__permanent_post'])
    ret.append(u'Α.Φ.')
    return ret


class LeaveDocxReport(DocxReport):
    def __init__(self, short_description, body_template_path,
                 fields=None, custom_context=None, model_fields=None,
                 include_header=True, include_footer=True):

        fields = fields or ['employee__firstname', 'employee__lastname',
                            'profession', 'organization_serving',
                            'employee__permanent__permanent_post',
                            'employee__fathername', 'order',
                            'date_from', 'date_to',
                            'protocol_number', 'duration', 'date_issued']

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
    LeaveDocxReport(u'Αιμοδοσίας', 'adeia_aimodosias.xml',
                    custom_context={'subject': u'Χορήγηση άδειας αιμοδοσίας'}),

    LeaveDocxReport(u'Συνδικαλιστική',
                    'adeia_syndikalistiki.xml',
                    custom_context={'subject':
                                        u'Χορήγηση Συνδικαλιστικής Άδειας '}),

    LeaveDocxReport(u'Τοκετού (πατέρα)', 'adeia_goniki_patera_toketou.xml',
                    custom_context={'subject':
                                        u'Χορήγηση ειδικής άδειας'
                                    u' λόγω τοκετού'}),

    LeaveDocxReport(u'Ειδική Άδεια 22 ημερών', 'adeia_22.xml',
                    custom_context={'subject': u'Χορήγηση ειδικής άδειας'}),

    LeaveDocxReport(u'Διευκόλυνσης', 'adeia_diefkolinsis.xml',
                    custom_context={'subject':
                                        u'Χορήγηση άδειας διευκόλυνσης'}),

    LeaveDocxReport(u'Κανονική', 'adeia_kanoniki.xml',
                    custom_context={'subject':
                                        u'Χορήγηση κανονικής άδειας '
                                    u'απουσίας'}),

    LeaveDocxReport(u'Ειδική Άδειας Εκλογών', 'adeia_eklogon.xml',
                    custom_context={'subject':
                                        u'Χορήγηση ειδικής άδειας λόγω'
                                    u' εκλογών'}),

    LeaveDocxReport(u'Ανατροφής (άνευ αποδοχών)', 'adeia_anatrofis_no_pay.xml',
                    custom_context={'subject':
                                    u'Χορήγηση άδειας χωρίς αποδοχές'
                                    u' για ανατροφή'
                     u' παιδιού'}),

    LeaveDocxReport(u'Ειδική Άδεια αιρετών μελών Ο.Τ.Α. άνευ αποδοχών',
                    'adeia_eidiki_airetoi_no_pay.xml',
                    custom_context={'subject':
                         u'Χορήγηση άδειας άνευ αποδοχών σε αιρετό εκπρόσωπο'
                     u' Ο.Τ.Α'}),

    LeaveDocxReport(u'Άδεια άνευ αποδοχών', 'adeia_eidiki_no_pay.xml',
                    custom_context={'subject':
                                        u'Χορήγηση άδειας άνευ αποδοχών'}),

    LeaveDocxReport(u'Αναρρωτική Άδεια (από Α\'Βάθμια Υγειονομική Επιτροπή',
                    'adeia_anarrotiki_yg_ep.xml',
                    custom_context={'subject':
                                        u'Χορήγηση αναρρωτικής άδειας'}),

    LeaveDocxReport(u'Αναρρωτική Άδεια (Βραχυχρόνια)',
                    'adeia_anarrotiki_short.xml',
                    custom_context={'subject':
                                        u'Χορήγηση αναρρωτικής άδειας'}),

    LeaveDocxReport(u'Ανατροφής (3 μήνες - τρίτου τέκνου)',
                    'adeia_anatrofis_3months.xml',
                    custom_context={'subject':
                                        u'Χορήγηση άδειας τριών μηνών για '
                                    u'ανατροφή τρίτου τέκνου και άνω.'}),

    LeaveDocxReport(u'Ανατροφής (9 μήνες)', 'adeia_anatrofis_9months.xml',
                    custom_context={'subject':
                                        u'Χορήγηση άδειας ανατροφής τέκνου'}),

    LeaveDocxReport(u'Γονική', 'adeia_goniki.xml',
                    custom_context={'subject':
                                        u'Χορήγηση γονικής άδειας απουσίας'}),

    LeaveDocxReport(u'Εξετάσεων', 'adeia_eidiki_eksetaseon.xml',
                    custom_context={'subject':
                                        u'Χορήγηση ειδικής άδειας εξετάσεων'}),

    LeaveDocxReport(u'Κύησης', 'adeia_pregnancy.xml',
                    custom_context={'subject':
                                        u'Χορήγηση άδειας κύησης'}),

    LeaveDocxReport(u'Άδεια Λοχείας', 'adeia_maternity.xml',
                    custom_context={'subject':
                                        u'Χορήγηση άδειας λοχείας'}),

    LeaveDocxReport(u'Κυοφορίας',
                    'adeia_pregnancy_normal.xml',
                    custom_context={'subject':
                         u'Χορήγηση κανονικής άδειας κυοφορίας με αποδοχές'})
    ]
