# -*- coding: utf-8 -*-
from dide.models import Permanent, PaymentReport
from django.db import connection, transaction
from lxml import etree
from time import time


def read(file, namespace):

    def rmv_nsp(node):  # function to remove the namespace from node
        return node.tag.rsplit('}', 1)[-1]

    try:
        print 'XML Reading started...'
        start = time()
        ns = namespace
        element = etree.parse(file)
        sql = ''

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
            year = el[0].get('year')
            el = i.xpath('./xs:periodType', namespaces={'xs': ns})
            paytype = el[0].get('value')

        e = element.xpath('//xs:psp/xs:body/xs:organizations' +
                          '/xs:organization/xs:employees/xs:employee',
                          namespaces={'xs': ns})

        reports = PaymentReport.objects.filter(pay_type=paytype,
                                               type=month, year=year).count()

        print 'Found %s records from a previous XML file.' % reports

        if reports > 0:
            cursor = connection.cursor()
            cursor.execute('delete from dide_paymentreport where ' +
                           'pay_type = %s and ' % paytype +
                           'type_id = %s and year = %s;' % (month, year))
            transaction.commit_unless_managed()
            cursor.close()
            reports = ''

        cursor = connection.cursor()
        objects = Permanent.objects.all()
        dic = {o.registration_number: o for o in objects}

        for i in e:
            iban = ''
            netAmount1 = ''
            netAmount2 = ''
            rank = 0
            cntr1 = cntr1 + 1
            el = i.xpath('./xs:identification/xs:amm', namespaces={'xs': ns})
            payemp = dic.get(el[0].text)
            if payemp:
                cntr2 = cntr2 + 1
                el = i.xpath('./xs:identification/xs:bankAccount',
                             namespaces={'xs': ns})
                iban = el[0].get('iban')
                el = i.xpath('./xs:identification/xs:scale/xs:rank',
                             namespaces={'xs': ns})
                rank = el[0].text
                el = i.xpath('./xs:payment/xs:netAmount1',
                             namespaces={'xs': ns})
                netAmount1 = el[0].get('value')
                el = i.xpath('./xs:payment/xs:netAmount2',
                             namespaces={'xs': ns})
                netAmount2 = el[0].get('value')
                sql = sql + "insert into dide_paymentreport values (NULL, "
                sql = sql + "%s, %s, %s, %s, %s, " % (payemp.parent.id,
                                                      month,
                                                      year,
                                                      paytype,
                                                      rank)
                sql = sql + "'%s', '%s', '%s');" % (iban,
                                                    netAmount1,
                                                    netAmount2)
                sql = sql + '\n'
                sql = sql + 'set @lastrep = last_insert_id();' + '\n'
                el = i.xpath('./xs:payment/xs:income', namespaces={'xs': ns})
                for p in el:
                    sql = sql + "insert into dide_paymentcategory "
                    sql = sql + "(id, paymentreport_id, title_id "
                    for attr_name, attr_value in p.items():
                        if attr_name == 'startDate':
                            sql = sql + ", start_date"
                        if attr_name == 'endDate':
                            sql = sql + ", end_date"
                        if attr_name == 'month':
                            sql = sql + ", month"
                        if attr_name == 'year':
                            sql = sql + ", year"

                    sql = sql + ") values (NULL, "
                    sql = sql + "@lastrep"
                    for attr_name, attr_value in p.items():
                        if attr_name == 'type':
                            sql = sql + ", " + attr_value
                        if attr_name == 'startDate':
                            sql = sql + ", '" + attr_value + "'"
                        if attr_name == 'endDate':
                            sql = sql + ", '" + attr_value + "'"
                        if attr_name == 'month':
                            sql = sql + ", " + attr_value + ""
                        if attr_name == 'year':
                            sql = sql + ", " + attr_value + ""
                    sql = sql + ");"
                    sql = sql + '\n'

                    sql = sql + 'set @lastcat = last_insert_id();' + '\n'
                    chld = p.getchildren()
                    if chld:
                        sql = sql + "insert into dide_payment "
                        sql = sql + "(id, category_id, type, "
                        sql = sql + "code_id, amount, info) "
                        sql = sql + "values "
                        c = 0
                        for elm in chld:
                            if c > 0:
                                sql = sql + ', '
                            sql = sql + "(NULL,"
                            sql = sql + " @lastcat, '" + rmv_nsp(elm) + "',"
                            sql = sql + elm.get('code') + ","
                            sql = sql + "'" + elm.get('amount') + "',"
                            if elm.get('loanNumber'):
                                sql = sql + "'" + elm.get('loanNumber') + "')"
                            else:
                                sql = sql + "NULL)"
                            c = c + 1
                        sql = sql + ';\n'

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
    except e:
        print e
        success = 0

    return success, cntr2
