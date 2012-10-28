# -*- coding: utf-8 -*-
from dide.models import Permanent, PaymentReport
from django.db import connection, transaction
from lxml import etree
from time import time
import datetime


def rmv_nsp(node):  # function to remove the namespace from node
    return node.tag.rsplit('}', 1)[-1]

def read(file):
        payment_category_fields = ['type', 'startDate', 'endDate', 'month', 'year']

        def query_value(field, value):
            if field in ['startDate', 'endDate']:
                return "'%s'" % str(value)[:10]
            else:
                return value
    #try:
        print 'XML Reading started...'
        start = time()
        element = etree.parse(file)
        sql = ''
        el = element.getroot()
        ns = el.tag.rsplit('}')[0].replace('{', '')
        cntr1 = 0
        cntr2 = 0
        month = 0
        year = 0
        paytype = 0
        e = element.xpath('//xs:psp/xs:header/xs:transaction',
                          namespaces={'xs': ns})
        for i in e:
            el = i.xpath('./xs:period', namespaces={'xs': ns})
            month = el[0].get('month')
            year = el[0].get('year').rsplit('+', 1)[0]
            el = i.xpath('./xs:periodType', namespaces={'xs': ns})
            paytype = el[0].get('value')

        e = element.xpath('//xs:psp/xs:body/xs:organizations' +
                          '/xs:organization/xs:employees/xs:employee',
                          namespaces={'xs': ns})

        reports = PaymentReport.objects.filter(pay_type=paytype,
                                               type=month, year=year).count()

        print 'Found %s records from a previous XML file.' % reports

        if reports > 0:
            pr = PaymentReport.objects.filter(pay_type=paytype,
                                              type_id=month, year=year)
            pr.delete()
            reports = ''

        cursor = connection.cursor()
        objects = Permanent.objects.all()
        dic = {o.registration_number: o for o in objects}
        for i in e:
            iban = ''
            netAmount1 = ''
            netAmount2 = ''
            rank = 0
            cntr1 += 1
            el = i.xpath('./xs:identification/xs:amm', namespaces={'xs': ns})
            payemp = dic.get(el[0].text)
            if payemp:
                cntr2 += 1
                el = i.xpath('./xs:identification/xs:bankAccount',
                             namespaces={'xs': ns})
                iban = el[0].get('iban')
                el = i.xpath('./xs:identification/xs:scale/xs:rank',
                             namespaces={'xs': ns})
                if el:
                    rank = el[0].text
                if not rank:

                    rank = payemp.rank_id()
                el = i.xpath('./xs:payment/xs:netAmount1',
                             namespaces={'xs': ns})
                netAmount1 = el[0].get('value')
                el = i.xpath('./xs:payment/xs:netAmount2',
                             namespaces={'xs': ns})
                netAmount2 = el[0].get('value')
                sql += "insert into dide_paymentreport (id, employee_id, "
                sql += "type_id, year, pay_type, rank_id, iban, "
                sql += "net_amount1, net_amount2) values (NULL, "
                sql += "%s, %s, %s, %s, %s, " % (payemp.parent.id,
                                                 month,
                                                 year,
                                                 paytype,
                                                 rank)
                sql += "'%s', '%s', '%s');" % (iban,
                                               netAmount1,
                                               netAmount2)
                sql += '\n'
                sql += 'set @lastrep = last_insert_id();' + '\n'
                el = i.xpath('./xs:payment/xs:income', namespaces={'xs': ns})
                for p in el:
                    sql += "insert into dide_paymentcategory "
                    sql += "(id, paymentreport_id, title_id, start_date, "
                    sql += "end_date, month, year) "
                    values = dict(p.items())
                    str_values = ",".join(
                        [query_value(f, values.get(f, 'NULL'))
                         for f in payment_category_fields])
                    sql += " values (NULL, @lastrep"
                    sql += "," + str_values + ");\n"
                    sql += 'set @lastcat = last_insert_id();' + '\n'

                    chld = p.getchildren()
                    if chld:
                        sql += "insert into dide_payment "
                        sql += "(id, category_id, type, "
                        sql += "code_id, amount, info) "
                        sql += "values "
                        c = 0
                        for elm in chld:
                            if c > 0:
                                sql += ', '
                            sql += "(NULL,"
                            sql += " @lastcat, '" + rmv_nsp(elm) + "',"
                            sql += elm.get('code') + ","
                            sql += "'" + elm.get('amount') + "',"
                            if elm.get('loanNumber'):
                                sql += "'" + elm.get('loanNumber') + "')"
                            else:
                                sql += "NULL)"
                            c = c + 1
                        sql += ';\n'

                sql_strings = sql.split('\n')
                for s_s in sql_strings:
                    if s_s:
                        cursor.execute(s_s)
                sql = ''
            else:
                print el[0].text + " not found in database."

        transaction.commit_unless_managed()
        cursor.close()

        print 'The XML file contained %s records.' % cntr1
        print '%s records found in database. Difference %d' % (cntr2,
                                                               (cntr1 - cntr2))

        elapsed = (time() - start)
        print 'Time reading file %.2f seconds.' % elapsed
        success = 1
#    except Exception, e:
#        print e
#        success = 0

        return success, cntr2
