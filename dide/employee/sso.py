# -*- coding: utf-8 -*-
"""Σύνδεση υπαλλήλων μέσω του SSO του Πανελλήνιου Σχολικού Δικτύου.

Υλοποιεί πελάτη **CAS** (Central Authentication Service), πρωτόκολλο 2.0 και
3.0. Η ροή είναι:

1. Ο χρήστης πατά «Σύνδεση με λογαριασμό ΠΣΔ» και ανακατευθύνεται στο
   ``<CAS>/login?service=<η δική μας callback>``.
2. Αφού ταυτοποιηθεί, ο CAS τον στέλνει πίσω με ``?ticket=ST-...``.
3. Ο **server μας** επικυρώνει το ticket κατευθείαν στον CAS
   (``/serviceValidate`` για 2.0, ``/p3/serviceValidate`` για 3.0). Το
   ticket δεν είναι διαπιστευτήριο από μόνο του: η ταυτότητα προκύπτει από
   την απάντηση του CAS, όχι από ό,τι στέλνει ο browser.
4. Το username (και τυχόν attributes) αντιστοιχίζονται σε Employee και
   γράφεται το ``matched_employee_id`` στη συνεδρία, ακριβώς όπως κάνει και
   η υπάρχουσα ταυτοποίηση με Αρ. Μητρώου/ΙΒΑΝ.

ΣΗΜΑΝΤΙΚΟ: οι διευθύνσεις και τα ονόματα των attributes δεν έχουν
επιβεβαιωθεί με το πραγματικό sso.sch.gr — ζητήστε τα από το ΠΣΔ και
συμπληρώστε τα στο ``SSO`` του settings.py. Τίποτα δεν ενεργοποιείται όσο
``SSO['enabled']`` είναι False.
"""
import logging
import ssl
import urllib.parse
import urllib.request
from xml.etree import ElementTree

from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from dideman.dide.models import Employee

logger = logging.getLogger('django.request')

CAS_NS = '{http://www.yale.edu/tp/cas}'


def config():
    """Οι ρυθμίσεις SSO, με ασφαλείς προεπιλογές."""
    cfg = dict(getattr(settings, 'SSO', {}) or {})
    cfg.setdefault('enabled', False)
    cfg.setdefault('server_url', 'https://sso.sch.gr/')
    cfg.setdefault('protocol', 3)          # 3 -> /p3/serviceValidate
    cfg.setdefault('login_path', 'login')
    cfg.setdefault('logout_path', 'logout')
    cfg.setdefault('validate_path', None)  # αλλιώς παράγεται από το protocol
    cfg.setdefault('verify_ssl', True)
    cfg.setdefault('timeout', 10)
    cfg.setdefault('username_suffix', '@sch.gr')
    # Με ποια σειρά δοκιμάζεται η αντιστοίχιση σε Employee. Κάθε στοιχείο
    # είναι (πεδίο μοντέλου, πηγή): 'username' ή το όνομα ενός attribute.
    cfg.setdefault('match_fields', [
        ('email', 'username_with_suffix'),
        ('email', 'email'),
        ('vat_number', 'taxid'),
    ])
    return cfg


def enabled():
    return bool(config()['enabled'])


def _url(cfg, path):
    return urllib.parse.urljoin(cfg['server_url'], path)


def validate_url(cfg):
    if cfg['validate_path']:
        return _url(cfg, cfg['validate_path'])
    return _url(cfg, 'p3/serviceValidate' if int(cfg['protocol']) >= 3
                else 'serviceValidate')


def service_url(request, next_url=None):
    """Η απόλυτη διεύθυνση της callback μας.

    Πρέπει να είναι *ακριβώς* η ίδια στο /login και στο /serviceValidate,
    αλλιώς ο CAS απορρίπτει το ticket.
    """
    url = request.build_absolute_uri(reverse('employee_sso_callback'))
    if next_url:
        url += '?' + urllib.parse.urlencode({'next': next_url})
    return url


def safe_next(request, default='/myinfo/edit/'):
    """Μόνο σχετικές διαδρομές, ώστε το ?next= να μη γίνει open redirect."""
    nxt = request.GET.get('next') or request.POST.get('next') or ''
    if nxt.startswith('/') and not nxt.startswith('//'):
        return nxt
    return default


def _opener(cfg):
    if cfg['verify_ssl']:
        context = ssl.create_default_context()
    else:
        # Μόνο για δοκιμές· ποτέ σε παραγωγή.
        context = ssl._create_unverified_context()
    return urllib.request.build_opener(urllib.request.HTTPSHandler(context=context))


def fetch_validation(cfg, url):
    """Κατεβάζει την απάντηση του CAS. Χωριστά, ώστε να μπορεί να δοκιμαστεί."""
    with _opener(cfg).open(url, timeout=cfg['timeout']) as response:
        return response.read().decode('utf-8', 'replace')


def parse_validation(xml_text):
    """Επιστρέφει (username, attributes) ή (None, {}) σε αποτυχία.

    Δέχεται και CAS 2.0 (μόνο <cas:user>) και 3.0 (με <cas:attributes>).
    """
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError:
        logger.warning('SSO: μη έγκυρο XML από τον CAS')
        return None, {}

    success = root.find(CAS_NS + 'authenticationSuccess')
    if success is None:
        failure = root.find(CAS_NS + 'authenticationFailure')
        code = failure.get('code') if failure is not None else 'unknown'
        logger.warning('SSO: ο CAS απέρριψε το ticket (%s)', code)
        return None, {}

    user_el = success.find(CAS_NS + 'user')
    if user_el is None or not (user_el.text or '').strip():
        return None, {}
    username = user_el.text.strip()

    attributes = {}
    attrs_el = success.find(CAS_NS + 'attributes')
    if attrs_el is not None:
        for child in attrs_el:
            name = child.tag.replace(CAS_NS, '')
            value = (child.text or '').strip()
            # Επαναλαμβανόμενα attributes -> λίστα
            if name in attributes:
                if not isinstance(attributes[name], list):
                    attributes[name] = [attributes[name]]
                attributes[name].append(value)
            else:
                attributes[name] = value
    return username, attributes


def find_employee(cfg, username, attributes):
    """Αντιστοιχίζει τον χρήστη του ΠΣΔ σε Employee.

    Δοκιμάζει με τη σειρά τα ζεύγη του ``match_fields``. Επιστρέφει το
    Employee ή None.
    """
    for field, source in cfg['match_fields']:
        if source == 'username':
            value = username
        elif source == 'username_with_suffix':
            value = username + cfg['username_suffix']
        else:
            value = attributes.get(source)
            if isinstance(value, list):
                value = value[0] if value else None
        if not value:
            continue
        match = Employee.objects.filter(**{'%s__iexact' % field: value}).first()
        if match is not None:
            return match
    return None


# -- views ------------------------------------------------------------------

def login(request):
    """Στέλνει τον χρήστη στον CAS."""
    cfg = config()
    if not cfg['enabled']:
        return render(request, 'employee/sso_disabled.html', status=503)
    params = urllib.parse.urlencode(
        {'service': service_url(request, safe_next(request))})
    return HttpResponseRedirect('%s?%s' % (_url(cfg, cfg['login_path']), params))


def callback(request):
    """Επιστροφή από τον CAS: επικύρωση ticket και σύνδεση."""
    cfg = config()
    if not cfg['enabled']:
        return render(request, 'employee/sso_disabled.html', status=503)

    next_url = safe_next(request)
    ticket = request.GET.get('ticket')
    if not ticket:
        return HttpResponseRedirect(reverse('employee_sso_login'))

    params = urllib.parse.urlencode({
        'service': service_url(request, next_url),
        'ticket': ticket,
    })
    try:
        xml_text = fetch_validation(cfg, '%s?%s' % (validate_url(cfg), params))
    except Exception as exc:                      # δίκτυο, TLS, timeout
        logger.error('SSO: αποτυχία επικοινωνίας με τον CAS: %s', exc)
        return render(request, 'employee/sso_error.html',
                      {'reason': 'unreachable'}, status=502)

    username, attributes = parse_validation(xml_text)
    if not username:
        return render(request, 'employee/sso_error.html',
                      {'reason': 'rejected'}, status=403)

    employee = find_employee(cfg, username, attributes)
    if employee is None:
        return render(request, 'employee/sso_error.html',
                      {'reason': 'unmatched', 'username': username}, status=403)

    # Ίδιο «κλειδί» συνεδρίας με την ταυτοποίηση Αρ.Μητρώου/ΙΒΑΝ.
    request.session.cycle_key()
    request.session['matched_employee_id'] = employee.id
    request.session['sso_username'] = username
    return HttpResponseRedirect(next_url)


def logout(request):
    """Καθαρίζει τη συνεδρία και, προαιρετικά, αποσυνδέει και από τον CAS."""
    cfg = config()
    was_sso = bool(request.session.get('sso_username'))
    request.session.flush()
    if cfg['enabled'] and was_sso and cfg.get('logout_path'):
        params = urllib.parse.urlencode(
            {'service': request.build_absolute_uri('/')})
        return HttpResponseRedirect(
            '%s?%s' % (_url(cfg, cfg['logout_path']), params))
    return HttpResponseRedirect('/')
