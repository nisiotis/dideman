# -*- coding: utf-8 -*-
from dideman.dide.actions import DocxReport
from dideman.dide.util.settings import SETTINGS
import os

def cc(obj):
    ret = []
    if hasattr(obj['non_permanent__organization_serving'], 'organization'):
        ret.append(obj['non_permanent__organization_serving'].organization.name)       
    if obj['affects_payment']:
        ret.append(u'Εκκαθαριστής')
    ret.append(u'Α.Φ.')
    return ret


class LeaveDocxReport(DocxReport):
    def __init__(self, short_description, body_template_path,
                 fields=None, custom_context=None, model_fields=None,
                 include_header=True, include_footer=True):

        fields = fields or ['non_permanent__firstname', 'non_permanent__lastname',
                            'non_permanent__profession', 'non_permanent__organization_serving',
                            'non_permanent__fathername', 'order', 'period_description',
                            'date_from', 'date_to', 'protocol_number', 'affects_payment',
                            'duration', 'date_issued', 'leave__affects_payment', 'non_permanent__to_text', 
                            'non_permanent__employment_type_text']

        context = {'telephone_number':
                       SETTINGS['leaves_contact_telephone_number'],
                   'contact_person': SETTINGS['leaves_contact_person'],
                   'email': SETTINGS['email_leaves']}
        if custom_context:
            context.update(custom_context)

        if not model_fields:
            model_fields = {'header_date': '{{date_issued}}',
                            'recipient':
                                '{{non_permanent__firstname}}'
                            ' {{non_permanent__lastname}}'}

            model_fields['cc'] = cc

        super(LeaveDocxReport, self).__init__(
            short_description, os.path.join('nonpermanentleave', body_template_path),
            fields, context, model_fields, include_header, include_footer)


non_permanent_leave_docx_reports = [
    LeaveDocxReport(u'Αιμοδοτική', 'aimodotiki.xml', custom_context={'subject': u'Χορήγηση άδειας αιμοδοσίας'}),
    LeaveDocxReport(u'Αναρρωτική', 'anarrotiki.xml', custom_context={'subject': u'Χορήγηση αναρρωτικής άδειας'}),
    LeaveDocxReport(u'Αναρρωτική χωρίς αποδοχές', 'anarrotiki_xoris.xml', custom_context={'subject': u'Χορήγηση αναρρωτικής άδειας'}),    
    LeaveDocxReport(u'Ανατροφής 4 μήνες χωρίς αποδοχές', 'anatrofis_4_xoris.xml', custom_context={'subject': u'Χορήγηση άδειας ανατροφής (4 μηνών χωρίς αποδοχές'}),
    LeaveDocxReport(u'Γονική', 'goniki.xml', custom_context={'subject': u'Χορήγηση γονικής άδειας'}), 
    LeaveDocxReport(u'Διευκόλυνσης', 'diefkolinsis.xml', custom_context={'subject': u'Χορήγηση άδειας διευκόλυνσης'}), 
    LeaveDocxReport(u'Ειδική 22 ημερών', 'adeia_22.xml', custom_context={'subject': u'Χορήγηση ειδικής άδειας'}),
    LeaveDocxReport(u'Εκλογική', 'eklogiki.xml', custom_context={'subject': u'Χορήγηση ειδικής άδειας λόγω εκλογών'}),
    LeaveDocxReport(u'Εξετάσεων', 'eksetaseon.xml', custom_context={'subject': u'Χορήγηση ειδικής άδειας εξετάσεων'}),
    LeaveDocxReport(u'Κανονική', 'kanoniki.xml', custom_context={'subject': u'Χορήγηση κανονικής άδειας απουσίας'}),
    LeaveDocxReport(u'Κύησης-Λοχείας', 'kyisisloxeias.xml', custom_context={'subject': u'Χορήγηση άδειας Κύησης-Λοχείας'}),
    LeaveDocxReport(u'Κύησης', 'kyisis.xml', custom_context={'subject': u'Χορήγηση άδειας Κύησης'}),
    LeaveDocxReport(u'Λοχείας', 'loxeias.xml', custom_context={'subject': u'Χορήγηση άδειας λοχείας'}),
    LeaveDocxReport(u'Τοκετού Πατέρα', 'toketou.xml', custom_context={'subject': u'Χορήγηση άδειας τοκετού πατέρα'})
    ]
