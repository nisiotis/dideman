# -*- coding: utf-8 -*-
from dideman.dide.models import Permanent, Employee, RankCode, PaymentCode
from django.db import connection, transaction
from lxml import etree
from time import time


def rmv_nsp(node):  # function to remove the namespace from node
    return node.tag.rsplit('}', 1)[-1]


def query_value(field, value):
    if field in ['startDate', 'endDate']:
        return "'%s'" % str(value)[:10]
    else:
        return value


def read(file, filerec, istaxed):
    elapsed = 0
    start = time()
    recs_missed = {}
    payment_category_fields = ['type', 'startDate', 'endDate',
                               'month', 'year']
    objects = Employee.objects.all()
    e_dic = {o.vat_number: o for o in objects}
    objects = Permanent.objects.all()
    p_dic = {o.registration_number: o for o in objects}
    objects = RankCode.objects.all()
    rankdic = {o.id for o in objects}
    objects = PaymentCode.objects.all()
    paycodesdic = {o.id for o in objects}
    try:        
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
            if int(paytype) not in [1, 11, 12, 13]:
                month = 16
        e = element.xpath('//xs:psp/xs:body/xs:organizations' +
                          '/xs:organization/xs:employees/xs:employee',
                          namespaces={'xs': ns})
        cursor = connection.cursor()
        for i in e:
            employeeID = 0
            iban = ''
            netAmount1 = ''
            netAmount2 = ''
            rank = 0
            cntr1 += 1
            el = i.xpath('./xs:identification/xs:amm', namespaces={'xs': ns})
            payemp = p_dic.get(el[0].text)
            if not payemp:
                el = i.xpath('./xs:identification/xs:tin',
                             namespaces={'xs': ns})
                payemp = e_dic.get(el[0].text)
                if payemp:
                    employeeID = payemp.id
            else:
                employeeID = payemp.parent.id
            if employeeID != 0:
                cntr2 += 1
                el = i.xpath('./xs:identification/xs:bankAccount',
                             namespaces={'xs': ns})
                iban = el[0].get('iban')
                el = i.xpath('./xs:identification/xs:scale/xs:mk',
                             namespaces={'xs': ns})
                if el:
                    rank = 'NULL' if int(el[0].text) not in rankdic else el[0].text
                else:
                    rank = 'NULL'
                
                el = i.xpath('./xs:payment/xs:netAmount1',
                             namespaces={'xs': ns})
                netAmount1 = el[0].get('value')
                el = i.xpath('./xs:payment/xs:netAmount2',
                             namespaces={'xs': ns})
                netAmount2 = el[0].get('value')
                sql += "insert into dide_paymentreport ("
                sql += "id, paymentfilename_id, employee_id, "
                sql += "type_id, year, pay_type, rank_id, iban,"
                sql += "net_amount1, net_amount2, taxed) values (NULL, "
                sql += "%s, %s, %s, %s, %s, %s, " % (filerec,
                                                     employeeID,
                                                     month,
                                                     year,
                                                     paytype,
                                                     rank)
                sql += "'%s', '%s', '%s', %s);" % (iban,
                                               netAmount1,
                                               netAmount2,
                                               istaxed)
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
                            if int(elm.get('code')) not in paycodesdic:
                                pc = PaymentCode(id=int(elm.get('code')),
                                                 description='')
                                pc.save()
                                paycodesdic.add(pc.id)
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
                        try:
                            cursor.execute(s_s)
                        except:
                            print s_s
                            raise
                sql = ''
            else:
                rNum = el[0].text
                el = i.xpath('./xs:identification/xs:firstName',
                             namespaces={'xs': ns})
                fName = el[0].text
                el = i.xpath('./xs:identification/xs:lastName',
                             namespaces={'xs': ns})
                lName = el[0].text
                recs_missed[rNum] = '%s %s' % (lName, fName)

        transaction.commit_unless_managed()
        cursor.close()
        recs_affected = cntr2
        success = 1
        elapsed = time() - start
    except:
        recs_missed = {}
        recs_affected = 0
        success = 0
        elapsed = 0
        raise
    return success, recs_affected, elapsed, recs_missed
