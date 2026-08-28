# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import Q
from dideman.lib.common import *
from dideman.lib.date import *
from dideman.dide.decorators import shorted
from django.db.models import Max
from django.db import connection, transaction
#from south.modelsinspector import add_introspection_rules
from django.db.models import Sum
from dideman import settings
from operator import itemgetter, concat
from itertools import groupby
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
import datetime
from . import sql
import os
from functools import reduce


class NullableCharField(models.CharField):
    description = 'CharField that obeys null=True'

    def to_python(self, value):
        if isinstance(value, models.CharField):
            return value
        return value or ''

    def get_db_prep_value(self, value, *args, **kwargs):
        return value or None

    def deconstruct(self):
        name, path, args, kwargs = super(NullableCharField, self).deconstruct()
        return name, path, args, kwargs


#add_introspection_rules([], ['^dideman\.dide\.models\.NullableCharField'])


class RankCode(models.Model):

    class Meta:
        verbose_name = 'Βαθμίδα Εξέλιξης / Κλιμάκιο'
        verbose_name_plural = 'Βαθμίδες Εξέλιξης / Κλιμάκια'

    id = models.IntegerField('Κωδικός', primary_key=True)
    rank = models.CharField('Βαθμός', max_length=4)

    def __unicode__(self):
        return self.rank


PDF_FILE_TYPES = [(1, 'Μήνιαίες Βεβαιώσεις'),
                  (2, 'Έτήσιες Βεβαιώσεις')]


class PaymentFilePDF(models.Model):

    class Meta:
        verbose_name = 'Οικονομικά: Αρχείο Πληρωμής σε PDF'
        verbose_name_plural = 'Οικονομικά: Αρχεία Πληρωμών σε PDF'

    def timestampedfiles(instance, filename):
        ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = "%s%s" % (ts, filename[-4:])
        return os.path.join(settings.MEDIA_ROOT, "pdffiles", filename)

    id = models.AutoField(primary_key=True)
    pdf_file = models.FileField('Αρχείο', upload_to=timestampedfiles)
    description = models.CharField('Περιγραφή', max_length=255)
    status = models.BooleanField('Κατάσταση', blank=True, default=None)
    extracted_files = models.IntegerField('Αρχεία που \
    δημιουργίθηκαν', null=True, blank=True)
    pdf_file_type = models.IntegerField('Τύπος αποδοχών', 
                                        choices=PDF_FILE_TYPES, blank=True, 
                                        default=1)

    def __unicode__(self):
        return self.description


class PaymentEmployeePDF(models.Model):

    id = models.AutoField(primary_key=True)
    employee_vat = models.CharField('Αριθμός φορολογικού μητρώου υπαλλήλου', 
                                    max_length=255)
    paymentfilepdf = models.ForeignKey('PaymentFilePDF', 
                                       verbose_name='Αρχείο', on_delete=models.CASCADE)
    employeefile = models.CharField('Αρχείο υπαλλήλου',
                                    max_length=255)
    pdf_file_type = models.IntegerField('Τύπος αποδοχών', 
                                        choices=PDF_FILE_TYPES, 
                                        blank=True, default=1)

    def __unicode__(self):
        return self.employeefile


@receiver(pre_delete, sender=PaymentFilePDF)
def pdffile_delete(sender, instance, **kwargs):
    if instance.pdf_file:
        l = os.listdir(os.path.join(settings.MEDIA_ROOT, "pdffiles", "extracted"))
        f = instance.pdf_file.name.replace(os.path.join(settings.MEDIA_ROOT,
                                                        'pdffiles'),'')[1:-4]
        for itm in l:
            if itm.startswith("%s" % f):
                os.remove(os.path.join(settings.MEDIA_ROOT,
                                       "pdffiles",
                                       "extracted", itm))
        instance.pdf_file.delete(False)


TAXED_TYPES = [(11, 'Τακτικές Μονίμων'),
               (12, 'Τακτικές Αναπληρωτών'),
               (21, 'Έκτακτες που φορολογούνται'),
               (22, 'Έκτακτες που δεν φορολογούνται'),
               (23, 'Έκτακτες με αυτοτελή φόρο')]


class PaymentFileName(models.Model):

    class Meta:
        verbose_name = 'Οικονομικά: Αρχείο Πληρωμής'
        verbose_name_plural = 'Οικονομικά: Αρχεία Πληρωμών'

    id = models.AutoField(primary_key=True)
    xml_file = models.FileField(upload_to="xmlfiles")
    description = models.CharField('Περιγραφή', max_length=255)
    status = models.BooleanField('Κατάσταση', blank=True, default=0)
    imported_records = models.IntegerField('Εγγραφές που ενημερώθηκαν', 
                                           null=True, blank=True)
    taxed = models.IntegerField('Τύπος αποδοχών', choices=TAXED_TYPES, 
                                blank=True, default=11)

    def __unicode__(self):
        return self.description

@receiver(pre_delete, sender=PaymentFileName)
def xmlfile_delete(sender, instance, **kwargs):
    if instance.xml_file:
        instance.xml_file.delete(False)


class PaymentReportType(models.Model):

    class Meta:
        verbose_name = 'Οικονομικά: Τύπος Μισθολογικής Κατάστασης'
        verbose_name_plural = 'Οικονομικά: Τύποι Μισθολογικών Καταστάσεων'

    id = models.IntegerField('Κωδικός', primary_key=True)
    type = models.CharField('Περιγραφή', max_length=255)

    def __unicode__(self):
        return self.type


class PaymentCategoryTitle(models.Model):

    class Meta:
        verbose_name = 'Οικονομικά: Τύπος Πληρωμής'
        verbose_name_plural = 'Οικονομικά: Τύποι Πληρωμών'

    id = models.IntegerField('Κωδικός', primary_key=True)
    title = models.CharField('Περιγραφή', max_length=255)

    def __unicode__(self):
        return self.title


class PaymentReport(models.Model):
    class Meta:
        verbose_name = 'Οικονομικά: Μισθολογική Κατάσταση'
        verbose_name_plural = 'Οικονομικά: Μισθολογικές Καταστάσεις'

    paymentfilename = models.ForeignKey('PaymentFileName', verbose_name='Αρχείο', on_delete=models.CASCADE)
    employee = models.ForeignKey('Employee', verbose_name='Υπάλληλος', on_delete=models.CASCADE)
    type = models.ForeignKey('PaymentReportType', verbose_name='Τύπος Αναφοράς', on_delete=models.CASCADE)
    year = models.IntegerField('Έτος')
    pay_type = models.IntegerField('Τύπος πληρωμής')
    rank = models.ForeignKey('RankCode', verbose_name='Βαθμός', null=True, blank=True, on_delete=models.CASCADE)
    iban = models.CharField('iban', max_length=50, null=True, blank=True)
    net_amount1 = models.CharField("Α' Δεκαπενθήμερο", max_length=50, null=True, blank=True)
    net_amount2 = models.CharField("Β' Δεκαπενθήμερο", max_length=50, null=True, blank=True)
    taxed = models.IntegerField('Τύπος αποδοχών', choices=TAXED_TYPES, blank=True, default=11)

    def netab_amount(self):
        return float(self.net_amount1) + float(self.net_amount2)

    def calc_amount(self):
        ta = 0.00
        if self.net_amount1 == '0' and self.net_amount2 == '0':
            ta = 0.00
            for c in PaymentCategory.objects.filter(paymentreport=self.id):
                grnum = 0.00
                denum = 0.00
                for p in Payment.objects.filter(category=c.id):
                    if p.type == 'gr':
                        grnum += float(str(p.amount))
                    if p.type == 'de':
                        denum += float(str(p.amount))
                ta += (grnum - denum)
        return ta

    def __unicode__(self):
        return "%s: %s" % (self.paymentfilename, self.employee)


class PaymentCategory(models.Model):
    paymentreport = models.ForeignKey('PaymentReport', on_delete=models.CASCADE)
    title = models.ForeignKey('PaymentCategoryTitle', verbose_name='Τίτλος Κατηγορίας', on_delete=models.CASCADE)
    start_date = models.CharField('Ημερομηνία Έναρξης', max_length=50, null=True, blank=True)
    end_date = models.CharField('Ημερομηνία Λήξης', max_length=50, null=True, blank=True)
    month = models.IntegerField('Μήνας', null=True, blank=True)
    year = models.IntegerField('Έτος', null=True, blank=True)
    payments = models.ManyToManyField('PaymentCode', through='Payment')


class Payment(models.Model):
    category = models.ForeignKey('PaymentCategory', on_delete=models.CASCADE)
    type = models.CharField('Τύπος', max_length=2)  # (gr, et, de)
    code = models.ForeignKey('PaymentCode', on_delete=models.CASCADE)
    amount = models.CharField('Ποσό', max_length=10)
    info = models.CharField('Σχετικές πληοροφορίες', max_length=255, null=True, blank=True)


CALC_TYPES = [(1, 'Φόρος'), (2,'Ταμείο'), (3,'Απεργία'), (4,'Σύνταξη'),  (5,'Εισφορά'), (0,'Άλλο')]


class PaymentCode(models.Model):

    class Meta:
        verbose_name = 'Οικονομικά: Κωδικός Πληρωμής'
        verbose_name_plural = 'Οικονομικά: Κωδικοί Πληρωμών'

    id = models.IntegerField('Κωδικός', primary_key=True)
    description = models.CharField('Περιγραφή', max_length=255)
    group_name =  models.CharField('Όνομα ομάδας', max_length=100, null=True, blank=True)
    calc_type = models.IntegerField('Τύπος', choices=CALC_TYPES, null=True, blank=True)

    def __unicode__(self):
        return self.description


class Application(models.Model):

    class Meta:
        verbose_name = 'Αίτηση'
        verbose_name_plural = 'Αιτήσεις'

    employee = models.ForeignKey('Employee', verbose_name='Υπάλληλος', on_delete=models.CASCADE)
    choices = models.ManyToManyField('School', through='ApplicationChoice')
    set = models.ForeignKey('ApplicationSet', verbose_name='Ανήκει', on_delete=models.CASCADE)
    datetime_finalised = models.DateTimeField('Ημερομηνία Οριστικοποίησης', null=True, blank=True)

    def join_choices(self, sep=','):
        return sep.join([
                choice.choice.name for choice in
                sorted(ApplicationChoice.objects.filter(application=self), key=lambda x: x.position)])
    join_choices.short_description = 'Επιλογές'

    def finalised(self):
        return bool(self.datetime_finalised)
    finalised.short_description = 'Οριστικοποιήθηκε'

    def profession(self):
        return self.employee.profession
    profession.short_description = 'Ειδικότητα'

    def __unicode__(self):
        return '%s-%s' % (self.set, self.employee)


class TemporaryPosition(Application):

    class Meta:
        verbose_name = 'Αίτηση προσωρινής τοποθέτησης'
        verbose_name_plural = 'Αιτήσεις προσωρινής τοποθέτησης'

    parent = models.OneToOneField('Application', parent_link=True, on_delete=models.CASCADE)
    telephone_number = models.CharField('Τηλέφωνο επικοινωνίας', max_length=20)
    colocation_municipality = models.CharField('Δήμος Συνυπηρέτησης', max_length=200, null=True, blank=True)
    nativity_municipality = models.CharField('Δήμος Εντοπιότητας', max_length=200, null=True, blank=True)


class TemporaryPositionAllAreas(TemporaryPosition):

    class Meta:
        verbose_name = 'Αίτηση προσωρινής τοποθέτησης σε όλα τα σχολεία'
        verbose_name_plural = ('Αίτηση προσωρινής τοποθέτησης σε όλα'
                               ' τα σχολεία')
        proxy = True


HEALTH_CHOICES = (('50-66', 'Αναπηρία 50-66%'),
                  ('67-79', 'Αναπηρία 67-79'),
                  ('80-', 'Αναπηρία 80% και άνω'))


class MoveInside(Application):

    class Meta:
        verbose_name = 'Αίτηση απόσπασης εντός Π.Υ.Σ.Δ.Ε.'
        verbose_name_plural = 'Αιτήσεις απόσπασης εντός Π.Υ.Σ.Δ.Ε.'

    parent = models.OneToOneField('Application', parent_link=True, on_delete=models.CASCADE)
    telephone_number = models.CharField('Τηλέφωνο επικοινωνίας', max_length=20)
    colocation_municipality = models.CharField('Δήμος Συνυπηρέτησης', max_length=200, null=True, blank=True)
    nativity_municipality = models.CharField('Δήμος Εντοπιότητας', max_length=200, null=True, blank=True)
    married = models.BooleanField('Έγγαμος', default=False)
    divorced = models.BooleanField('Διαζευγμένος', default=False)
    widowed = models.BooleanField('Σε χηρεία', default=False)
    custody = models.BooleanField('Επιμέλεια παιδιών', default=False)
    single_parent = models.BooleanField('Μονογονεϊκή οικογένεια', default=False)
    children = models.IntegerField('Τέκνα ανήλικα ή σπουδάζοντα', null=True, blank=True)
    health_self = models.CharField('Λόγοι Υγείας', max_length=100, choices=HEALTH_CHOICES, null=True, blank=True)
    health_spouse = models.CharField('Λόγοι υγεία συζύγου', max_length=100, choices=HEALTH_CHOICES, null=True, default=None, blank=True)
    health_children = models.CharField('Λόγοι υγείας παιδιών', max_length=100, choices=HEALTH_CHOICES, null=True, default=None, blank=True)
    health_parents = models.CharField('Λόγοι υγείας γονέων', max_length=100, choices=HEALTH_CHOICES, null=True, default=None, blank=True)
    parents_place = models.CharField('Περιοχή διαμονής γονέων', max_length=150, null=True, blank=True)
    health_siblings = models.NullBooleanField('Λόγοι υγείας αδερφών (> 67% με επιμέλεια)', default=False, null=True, blank=True)
    siblings_place = models.CharField('Περιοχή διαμονής αδερφών', max_length=150,  null=True, blank=True)
    in_vitro = models.BooleanField('Θεραπεία εξωσωματικής γονιμοποίησης', default=False)
    post_graduate_subject = models.CharField('Περιοχή μεταπτυχιακών σπουδών (εφόσον υπάρχει)', null=True, blank=True, max_length=150)
    special_category = models.CharField('Ειδική κατηγορία μετάθεσης', max_length=150, null=True, blank=True)
    military_spouse = models.NullBooleanField('Σύζυγος στρατιωτικού', null=True, blank=True, default=False)
    elected = models.BooleanField('Αιρετός ΟΤΑ', default=False)
    judge_spouse = models.NullBooleanField('Σύζυγος δικαστικού',default=False, null=True, blank=True)
    move_primary = models.NullBooleanField('Απόσπαση Α\'βάθμια', default=False, null=True, blank=True)
    other_reasons = models.CharField('Άλλοι λόγοι', null=True, blank=True, default=None, max_length=500)


class ApplicationType(models.Model):

    class Meta:
        verbose_name = 'Τύπος Αίτησης'
        verbose_name_plural = 'Τύποι αιτήσεων'

    name = models.CharField('Όνομα', max_length=100)


class ApplicationChoice(models.Model):

    class Meta:
        verbose_name = 'Επιλογή'
        verbose_name_plural = 'Επιλογές'

    application = models.ForeignKey('Application', verbose_name='Αίτηση', on_delete=models.CASCADE)
    choice = models.ForeignKey('School', verbose_name='Επιλογή', on_delete=models.CASCADE)
    position = models.IntegerField('Θέση')

    def __unicode__(self):
        return self.choice.name


class ApplicationSet(models.Model):

    class Meta:
        verbose_name = 'Σύνολο Αιτήσεων'
        verbose_name_plural = 'Σύνολα Αιτήσεων'

    name = models.CharField('Όνομα', max_length=100)
    title = models.CharField('Περιγραφή', max_length=300, null=True, blank=True)

    start_date = models.DateField('Ημερομηνία Έναρξης')
    end_date = models.DateField('Ημερομηνία Λήξης')
    klass = models.CharField('Τύπος', max_length=150, choices=(
            ('TemporaryPosition', 'Προσωρινής Τοποθέτησης'),
            ('MoveInside', 'Απόσπασης εντός Π.Υ.Σ.Δ.Ε.'),
            ('TemporaryPositionAllAreas',
             'Προσωρινής Τοποθέτησης (όλες περιοχές)')))

    def __unicode__(self):
        return self.name


class TransferAreaManager(models.Manager):

    def get_by_natural_key(self, name):
        return self.get(name__startswith=name)


class TransferArea(models.Model):

    class Meta:
        verbose_name = 'Περιοχή μετάθεσης'
        verbose_name_plural = 'Περιοχές μετάθεσης'

    objects = TransferAreaManager()

    name = models.CharField(max_length=100)

    def natural_key(self):
        return (self.name, )

    def __unicode__(self):
        return self.name


class Island(models.Model):

    class Meta:
        verbose_name = 'Νησί'
        verbose_name_plural = 'Νησιά'
        ordering = ['name']

    name = models.CharField('Νησί', max_length=100)
    transfer_area = models.ForeignKey(TransferArea, verbose_name='Περιοχή Μετάθεσης', on_delete=models.CASCADE)

    def natural_key(self):
        return (self.name, )

    def __unicode__(self):
        return self.name


class OrganizationManager(models.Manager):

    def get_by_natural_key(self, name):
        return self.get(name=name)


class Organization(models.Model):

    class Meta:
        ordering = ['name']

    objects = OrganizationManager()

    name = models.CharField('Όνομα', max_length=100)
    belongs = models.BooleanField('Ανήκει στην Δ.Δ.Ε. Δωδεκανήσου', default=None)

    def natural_key(self):
        return (self.name, )

    def __unicode__(self):
        return self.name


class PlacementTypeManager(models.Manager):

    def get_by_natural_key(self, name):
        return self.get(name=name)


class PlacementType(models.Model):

    class Meta:
        verbose_name = 'Τύπος τοποθέτησης'
        verbose_name_plural = 'Τύποι τοποθέτησης'

    objects = PlacementTypeManager()

    name = models.CharField(max_length=100, verbose_name='Τύπος')

    def natural_key(self):
        return (self.name, )

    def __unicode__(self):
        return self.name


class LeaveManager(models.Manager):

    def get_by_natural_key(self, name):
        return self.get(name=name)

    def choices(self, for_non_permanents=False):
        qs = self.filter(for_non_permanents=for_non_permanents).only('id', 'name')
        choices = [(obj.id, obj.name) for obj in qs]
        return choices


LEAVE_TYPES = (('Κανονική', 'Κανονική'),
               ('Αναρρωτική', 'Αναρρωτική'),
               ('Ειδική', 'Ειδική'))


class Leave(models.Model):

    class Meta:
        verbose_name = 'Κατηγορία άδειας'
        verbose_name_plural = 'Κατηγορίες αδειών'
        ordering = ['name']

    objects = LeaveManager()

    name = models.CharField(max_length=200, verbose_name='Κατηγορία')
    type = models.CharField(max_length=15, verbose_name='Τύπος', choices=LEAVE_TYPES)
    not_paying = models.BooleanField(verbose_name='Χωρίς αποδοχές', default=None)
    is_service = models.BooleanField(verbose_name='Χρόνος κανονικής υπηρεσίας', default=None)
    only_working_days = models.BooleanField(verbose_name='Μόνο εργάσιμες μέρες', default=None)
    orders = models.CharField('Διατάξεις', null=True, blank=True, max_length=3000)
    subject_line = models.CharField('Θέμα', null=True, blank=True, max_length=300)
    description = models.CharField(null=True, blank=True, verbose_name='Περιγραφή', max_length=3000)
    notify_to = models.CharField(null=True, blank=True, verbose_name='Κοινοποίηση άδειας', max_length=300) 
    for_non_permanents = models.BooleanField(null=False, blank=False, verbose_name='Αναπληρωτών', default=None)
    service_days_count = models.IntegerField(null=True, blank=True, max_length=3, verbose_name='Μέρες μετρήσιμης προϋπηρεσίας', default=0)
    
    
    def __unicode__(self):
        return self.name

    def natural_key(self):
        return (self.name, )


class Responsibility(models.Model):

    class Meta:
        verbose_name = 'Κατηγορία θέσης ευθύνης'
        verbose_name_plural = 'Κατηγορίες θέσεων ευθύνης'

    hours = models.IntegerField(max_length=2, verbose_name='Ώρες μείωσης')
    name = models.CharField(max_length=200, verbose_name='Θέση ευθύνης')

    def __unicode__(self):
        return self.name


class Profession(models.Model):

    class Meta:
        verbose_name = 'Ειδικότητα'
        verbose_name_plural = 'Ειδικότητες'
        ordering = ['id']

    id = models.CharField('Ειδικότητα', max_length=100, primary_key=True)  # ΠΕ04.01 ΠΕ19.02 κτλ
    description = models.CharField('Λεκτικό', max_length=200, null=True)
    unified_profession = models.CharField('Κλάδος', max_length=100)  # ΠΕ04...
    unique_identity = models.CharField('Κλάδος Κενών', max_length=100, null=True,  blank=True) # Για την φόρμα των κενών...

    def category(self):
        """ΠΕ, ΤΕ, ΔΕ"""
        return self.id[:2]

    def __unicode__(self):
        return self.id


class DegreeCategory(models.Model):

    class Meta:
        verbose_name = 'Κατηγορία πτυχίου'
        verbose_name_plural = 'Κατηγορίες πτυχίων'

    # πτυχίο, μεταπτυχιακό, διδακτορικό, τπε κτλ
    name = models.CharField('Τύπος', max_length=100)

    def __unicode__(self):
        return self.name


class EmployeeManager(models.Manager):
    def match(self, vat_number, lastname, iban_4):
        try:
            return self.get(vat_number=vat_number, lastname=lastname, iban__endswith=iban_4)
        except:
            return None

    def get_by_natural_key(self, firstname, lastname, fathername, profession):
        return self.get(firstname=firstname, lastname=lastname, fathername=fathername, profession=profession)

    def get_queryset(self):
        # select permanent if exists
        return super(EmployeeManager, self).get_queryset().select_related('permanent')


SEX_TYPES = (('Άνδρας', 'Άνδρας'),
             ('Γυναίκα', 'Γυναίκα'))

MARITAL_TYPES = ((0, 'Άγαμος'),
                 (1, 'Έγγαμος'),
                 (2, 'Διαζευγμένος'),
                 (3, 'Χήρος'))


class Employee(models.Model):

    class Meta:
        verbose_name = 'Εκπαιδευτικός'
        verbose_name_plural = 'Εκπαιδευτικοί'
        ordering = ['lastname']

    objects = EmployeeManager()

    firstname = models.CharField('Όνομα', max_length=100)
    lastname = models.CharField('Επώνυμο', max_length=100)
    fathername = models.CharField('Όνομα Πατέρα', max_length=100)
    mothername = models.CharField('Όνομα Μητέρας', max_length=100, null=True, blank=True)
    sex = models.CharField('Φύλο', max_length=10, null=True, blank=True, choices=SEX_TYPES)
    address = models.CharField('Διεύθυνση - Οδός, Αριθμός', max_length=200, null=True, blank=True)
    address_postcode = models.CharField('Ταχ. Κωδικός', max_length=6, null=True, blank=True)
    address_city = models.CharField('Πόλη', max_length=30, null=True, blank=True)    
    identity_number = NullableCharField('Αρ. Δελτίου Ταυτότητας', max_length=9, null=True, unique=True, blank=True)
    transfer_area = models.ForeignKey(TransferArea, verbose_name='Περιοχή Μετάθεσης', null=True, blank=True, on_delete=models.CASCADE)
    recognised_experience = models.CharField('Συνολική προϋπηρεσία (ΕΕΜΜΗΗ)', null=True, blank=True, default='000000', max_length=8)
    salary_experience = models.CharField('Μισθολογική Προϋπηρεσία (ΕΕΜΜΗΗ)', null=True, blank=True, default='000000', max_length=8)
    # the following field needs to be added to the recognised experience
    recognised_experience_n4354_2015 = models.CharField('Προϋπηρεσία Ν. 4354/2015 (ΕΕΜΜΗΗ)', null=True, blank=True, default='000000', max_length=8)
    # new field with filter
    recognised_experience_n4452_2017 = models.CharField('Προϋπηρεσία Ν. 4452/2017 Βαθμολογική (ΕΕΜΜΗΗ)', null=True, blank=True, default='000000', max_length=8)
    non_educational_experience = models.CharField('Εκτός Ωραρίου (ΕΕΜΜΗΗ)', null=True, blank=True, default='000000', max_length=8)
    vat_number = NullableCharField('Α.Φ.Μ.', max_length=9, null=True, unique=True, blank=True)
    tax_office = models.CharField('Δ.Ο.Υ.', max_length=100, null=True, blank=True)
    bank = models.CharField('Τράπεζα', max_length=100, null=True, blank=True)
    bank_account_number = models.CharField('Αριθμός λογαριασμού τράπεζας', max_length=100, null=True, blank=True)
    iban = models.CharField('IBAN', max_length=27, null=True, blank=True)
    telephone_number1 = models.CharField('Αρ. Τηλεφώνου 1', max_length=14, null=True, blank=True)
    telephone_number2 = models.CharField('Αρ. Τηλεφώνου 2', max_length=14, null=True, blank=True)
    marital_status = models.IntegerField('Οικογενειακή Κατάσταση', null=True, blank=True, choices=MARITAL_TYPES)
    social_security_registration_number = models.CharField('Α.Μ.Κ.Α.', max_length=11, null=True, blank=True)
    before_93 = models.BooleanField('Ασφαλισμένος πριν το 93', default=0)
    has_family_subsidy = models.BooleanField('Οικογενειακό επίδομα', default=0)
    other_social_security = models.ForeignKey('SocialSecurity', verbose_name='Άλλο ταμείο ασφάλισης', null=True, blank=True, on_delete=models.CASCADE)
    organization_paying = models.ForeignKey(Organization, verbose_name='Οργανισμός μισθοδοσίας',related_name='organization_paying', null=True, blank=True, on_delete=models.CASCADE)
    email = models.EmailField(null=True, blank=True)
    birth_date = models.DateField('Ημερομηνία Γέννησης',null=True, blank=True)
    hours_current = models.IntegerField('Τρέχων Ωράριο', max_length=2, null=True, blank=True)
    profession = models.ForeignKey(Profession, verbose_name='Ειδικότητα', related_name='employees', on_delete=models.CASCADE)
    second_profession = models.ForeignKey(Profession, verbose_name='Δεύτερη Ειδικότητα',null=True, blank=True, on_delete=models.CASCADE)
    second_profession_order = models.CharField('Απόφαση απόδοσης δεύτερης ειδικότητας', max_length=100, null=True, blank=True)
    placements = models.ManyToManyField(Organization, through='Placement', verbose_name='Σχολείο/Φορέας')
    leaves = models.ManyToManyField(Leave, through='EmployeeLeave')
    #extra_professions = models.ManyToManyField(Profession, through='EmployeeProfession')
    responsibilities = models.ManyToManyField(Responsibility, through='EmployeeResponsibility')
    studies = models.ManyToManyField(DegreeCategory, through='EmployeeDegree')
    study_years = models.IntegerField('Έτη φοίτησης', max_length=1, null=True, blank=True,
        choices=[(x, str(x)) for x in range(2, 7)])
    notes = models.TextField('Σημειώσεις', blank=True, default='')
    show_mass_pay = models.NullBooleanField('Εμφάνιση μισθοδοτικών καταστάσεων στο χρήστη', null=True, blank=True, default=True)
    ama = models.CharField('ΑΜΑ ΙΚΑ ΕΤΑΜ', max_length=10, null=True, blank=True)
    date_created = models.DateField('Ημερομηνία δημιουργίας', auto_now_add=True)
    date_modified = models.DateField('Τελευταία ενημέρωση', auto_now=True)
    checked_service = models.BooleanField('Ελεγμένη προϋπηρεσία', default=0)
    citizenship_code = models.CharField('Κωδικός Υπηκοότητας', max_length=3, null=True, blank=True, default='048')
    photo = models.TextField('Φωτογραφία', blank=True, default=None)
    photo_type = models.CharField('Τύπος Φωτογραφίας', max_length=10, null=True, blank=True)

    def show_photo(self):
        if self.photo:
            return "<img src='/admin/dide/photo/%s/' style='width:75px;height:100px;padding-right:5px;vertical-align:top;'><a href='/admin/dide/photo_edit/%s/'  onclick=\"return focusOrOpen(this, 'Φωτογραφία',{'width': 350, 'height': 600});\">Αλλαγή Φωτογραφίας</a>" % (self.id, self.id)
        else:
            return "Δ/Υ <a href='/admin/dide/photo_edit/%s/'  onclick=\"return focusOrOpen(this, 'Φωτογραφία',{'width': 350, 'height': 600});\">Αλλαγή Φωτογραφίας</a>" % self.id

    show_photo.allow_tags = True
    show_photo.short_description = "Φωτογραφία"

    def profession_description(self):
        return self.profession.description
    profession_description.short_description = 'Λεκτικό ειδικότητας'

    def second_profession_description(self):
        if self.second_profession:
            return self.second_profession.description 
        else: 
            return None
    second_profession_description.short_description = 'Λεκτικό δεύτερης ειδικότητας'

    def last_placement(self):
        return first_or_none(Placement.objects.filter(
                employee=self).order_by('-date_from'))

    def current_year_placements(self):
        return Placement.objects.filter(
            employee=self, date_from__gte=current_year_date_from())

    def unified_profession(self):
        return self.profession.unified_profession

    def organization_serving(self):
        p = Placement.objects.filter(employee=self).order_by('-date_from')
        this_years = p.filter(date_from__gte=current_year_date_from(), date_to__gte=datetime.date.today()).order_by('-date_from')
        if this_years:
            return this_years[0]
        else:
            valid = p.filter(date_to__gte=datetime.date.today()). \
                order_by('-date_from')
            if valid:
                return valid[0]
            return None
    organization_serving.short_description = 'Θέση υπηρεσίας'

    def natural_key(self):
        return (self.firstname, self.lastname, self.fathername,
                self.profession)

    def formatted_recognised_experience_n4452_2017(self):
        return DateInterval(self.recognised_experience_n4452_2017)
    formatted_recognised_experience_n4452_2017.short_description = 'Μορφοποιημένη Προϋπηρεσία Ν. 4452/2017 (Βαθμολογική)'

    def formatted_recognised_experience(self):
        return DateInterval(self.recognised_experience)
    formatted_recognised_experience.short_description = 'Μορφοποιημένη προϋπηρεσία'

    def educational_service(self):
        return self.total_service() - DateInterval(self.non_educational_experience)
    educational_service.short_description = 'Εκπαιδευτική υπηρεσία (για μείωση ωραρίου)'

    def not_service_in_years(self):
        """Returns a dict of {year: sum_of_not_service_days } form"""
        today = datetime.date.today()
        last_day = datetime.date(day=31, month=12, year=today.year)
        leaves = self.employeeleave_set.filter(leave__is_service=False, date_from__lt=today)
        seq = reduce(concat, [l.split() for l in leaves], tuple())
        seq = [s for s in seq if s[0] <= today.year]
        # Για τις αδειες που δεν εχουν ληξει ακομη μην υπολογισεις στις αφαιρουμενες μερες
        # το διαστημα απο την ληξη της αδειας η το τελος του ετους μεχρι σημερα
        sub = sum([(min(l.date_to, last_day) - today).days
                   for l in leaves if l.date_to > today and l.date_from < today])
        groups = [(k, sum(map(itemgetter(1), g)))
                  for k, g in groupby(sorted(seq), key=itemgetter(0))]
        return [((y, d) if y != today.year else (y, max(0, d - sub))) for y, d in groups]

    def calculable_not_service(self):
        return sum([max(days - 30, 0)
                    for year, days in self.not_service_in_years()])
    calculable_not_service.short_description = 'Υπολογισμένες ημέρες άδειας εκτός υπηρεσίας'

    def totals_per_year(self, year):
        total_y = 0.00
        pay_reports = PaymentReport.objects.filter(employee=self, year=year)
        for each_pay in pay_reports:
            total_y += each_pay.calc_amount()
            total_y += each_pay.netab_amount()
        return total_y

    def become(self, model_to):
        cursor = connection.cursor()
        query = """INSERT IGNORE INTO `{table}`(`{column}`) VALUES({pk})""".format(
            table=model_to._meta.db_table, column=model_to._meta.pk.column, pk=self.pk)
        cursor.execute(query)
        transaction.commit_unless_managed()

    def subclass(self):
        for attr in ["administrative", "permanent", "nonnermanent", "privateteacher"]:
            try:
                m = getattr(self, attr)
                if hasattr(m, "currently_serves"):
                    if getattr(m, "currently_serves") == 1:
                        return m
                else:
                    return m
            except:
                continue
        if m:
            return m
        return self

    def normal_leave_days(self):
        raise NotImplementedError

    def to_text(self):
        if self.sex == "Άνδρας":
            return "στον"
        else:
            return "στην"

    def employment_text(self):
        return "υπάλληλος"

    def __unicode__(self):
        if hasattr(self, 'permanent') and self.permanent is not None:
            return '%s %s (%s)' % (self.lastname, self.firstname,
                                    self.permanent.registration_number)
        else:
            return '%s %s (%s)' % (self.lastname, self.firstname,
                                    self.vat_number)


class SocialSecurity(models.Model):

    class Meta:
        verbose_name = 'Ταμείο ασφάλισης'
        verbose_name_plural = 'Ταμεία ασφάλισης'

    name = models.CharField('Όνομα', max_length=100)
    code = models.CharField('Κωδικός', max_length=100)

    def __unicode__(self):
        return self.name


class PermanentManager(models.Manager):

    def match(self, registration_number, vat_number, lastname, iban_4):
        try:
            return self.get(Q(lastname=lastname), Q(iban__endswith=iban_4),
                            Q(registration_number=registration_number) |
                            Q(vat_number=vat_number))
        except:
            return None

    def get_by_natural_key(self, registration_number):
        return self.get(registration_number=registration_number)

    def choices(self):
        qs = self.filter(currently_serves=True).only(
            'firstname', 'lastname', 'fathername', 'registration_number')
        choices = ([(None, '---------')] +
                    [(obj.parent_id,
                      "%s %s (%s)" % (obj.lastname, obj.firstname,
                                      obj.registration_number)) for obj in qs])
        return choices

    def on_service(self, exclude=False):
        cursor = connection.cursor()
        cursor.execute(sql.on_service.format(datetime.date.today()))
        ids = [row[0] for row in cursor.fetchall()]
        if exclude:
            return self.exclude(id__in=ids)
        else:
            return self.filter(id__in=ids)

    def serves_in_dide_school(self):
        cursor = connection.cursor()
        cursor.execute(sql.serves_in_dide_school.format(datetime.date.today()))
        ids = [row[0] for row in cursor.fetchall()]
        return self.filter(parent_id__in=ids)

    def not_serves_in_dide_school(self):
        cursor = connection.cursor()
        cursor.execute(sql.serves_in_dide_school.format(datetime.date.today()))
        ids = [row[0] for row in cursor.fetchall()]
        return self.exclude(parent_id__in=ids)

    def serves_in_dide_org(self):
        cursor = connection.cursor()
        cursor.execute(sql.serves_in_other_org.format(datetime.date.today()))
        ids = [row[0] for row in cursor.fetchall()]
        return self.exclude(parent_id__in=ids)

    def not_serves_in_dide_org(self):
        cursor = connection.cursor()
        cursor.execute(sql.serves_in_other_org.format(datetime.date.today()))
        ids = [row[0] for row in cursor.fetchall()]
        return self.filter(parent_id__in=ids)

    def temporary_post_in_organization(self, org_id):
        cursor = connection.cursor()
        cursor.execute(sql.temporary_post_in_organization.format(org_id))
        ids = [row[0] for row in cursor.fetchall()]
        return self.filter(parent_id__in=ids)

    def permanent_post_in_island(self, island_id):
        cursor = connection.cursor()
        cursor.execute(sql.permanent_post_in_island.format(island_id))
        ids = [row[0] for row in cursor.fetchall()]
        return self.filter(parent_id__in=ids)

    def permanent_post_in_organization(self, org_id):
        cursor = connection.cursor()
        cursor.execute(sql.permanent_post_in_organization.format(org_id))
        ids = [row[0] for row in cursor.fetchall()]
        return self.filter(parent_id__in=ids)

    def permanent_post_in_organization_api(self, org_id):
        cursor = connection.cursor()
        cursor.execute(sql.serving_in_organization.format(org_id, datetime.date(datetime.date.today().year, 9, 1)))
        ids = [row[0] for row in cursor.fetchall()]
        return self.filter(parent_id__in=ids)

    def serving_in_organization(self, org_id):
        cursor = connection.cursor()
        cursor.execute(
            sql.serving_in_organization.format(org_id, datetime.date.today()))
        ids = [row[0] for row in cursor.fetchall()]
        return self.filter(parent_id__in=ids)

    def serving_in_organization_api(self, org_id):
        cursor = connection.cursor()
        cursor.execute(
            sql.serving_in_organization.format(org_id, datetime.date(datetime.date.today().year, 9, 1)))
        ids = [row[0] for row in cursor.fetchall()]
        return self.filter(parent_id__in=ids)

    def serving_in_island(self, island_id):
        cursor = connection.cursor()
        cursor.execute(
            sql.serving_in_island.format(island_id, datetime.date.today()))
        ids = [row[0] for row in cursor.fetchall()]
        return self.filter(parent_id__in=ids)

    def have_degree(self, degree_id):
        degree = DegreeCategory.objects.get(pk=degree_id)
        qs = EmployeeDegree.objects.filter(degree=degree)
        ids = [d.employee_id for d in qs]
        return self.filter(parent_id__in=ids)

    def transfered(self):
        ids = [p.employee.id for p in Placement.objects.only('employee')
               .filter(type__name='Μετάθεση')]
        return self.filter(pk__in=ids)

    def not_transfered(self):
        ids = [p.employee.id for p in Placement.objects.only('employee')
               .filter(type__name='Μετάθεση')]
        return self.all().exclude(pk__in=ids)

    # New Extra Rank Previous Service
    # Field is in Employee table
    def extra_rank_service(self):
        ids = [p.id for p in Employee.objects.exclude(recognised_experience_n4452_2017__isnull=True).exclude(recognised_experience_n4452_2017__exact='').exclude(recognised_experience_n4452_2017__exact='000000')]
        return self.filter(pk__in=ids)

    # New Promotion Filter 
    def next_promotion_in_range(self, date_from, date_to):
        return Permanent.objects.filter(
            id__in=[o['employee']
                    for o in [p for p in PromotionNew.objects
                              .all()
                              .values('employee')
                              .annotate(
                        next_promotion_date=Max('next_promotion_date'))
                              .filter(next_promotion_date__gte=date_from,
                                      next_promotion_date__lte=date_to)]])

    # φίλτρο επόμενης μείωσης ωραρίου     
    def next_hours_reduction_in_range(self, date_from, date_to):
        d_i = DateInterval(date_to.year-date_from.year, date_to.month-date_from.month, date_to.day-date_from.day)
        p = self.filter(currently_serves=True).exclude(non_educational_experience__isnull=True).exclude(non_educational_experience__exact='')
        return [o.id for o in p if o.hours_next() is not None and o.hours_next() < d_i]


class Permanent(Employee):

    class Meta:
        verbose_name = 'Μόνιμος Εκπαιδευτικός'
        verbose_name_plural = 'Μόνιμοι Εκπαιδευτικοί'

    objects = PermanentManager()

    parent = models.OneToOneField(Employee, parent_link=True, on_delete=models.CASCADE)
    serving_type = models.ForeignKey(PlacementType, null=True, blank=True, verbose_name='Είδος Υπηρέτησης', on_delete=models.CASCADE)
    date_hired = models.DateField('Ημερομηνία διορισμού', null=True, blank=True)
    date_end = models.DateField('Ημερομηνία λήξης υπηρεσίας', null=True, blank=True)
    order_hired = models.CharField('Φ.Ε.Κ. διορισμού', max_length=200, null=True, blank=True)
    registration_number = NullableCharField('Αρ. Μητρώου', max_length=6, unique=True, null=True, blank=True)
    inaccessible_school = models.ForeignKey('School', verbose_name='Δυσπρόσιτος στο σχολείο', null=True, blank=True, on_delete=models.CASCADE)
    payment_start_date_manual = models.DateField('Μισθολογική αφετηρία (μετά από άδεια)', null=True, blank=True)
    is_permanent = models.NullBooleanField('Έχει μονιμοποιηθεί', null=True, blank=True, default=False)
    has_permanent_post = models.NullBooleanField('Έχει οργανική θέση',null=True, blank=True, default=False)
    not_service_existing = models.IntegerField('Αφαιρούμενες μέρες άδειας', default=0)
    currently_serves = models.NullBooleanField('Υπηρετεί στην Δ.Δ.Ε. Δωδεκανήσου', null=True, default=True)
    educated = models.NullBooleanField('Έχει περάσει Π.Ε.Κ.', null=False, default=False)

    def object_name(self):
        return self._meta.object_name

    def app_label(self):
        return self._meta.app_label

    def total_service(self):
        if self.payment_start_date_manual:
            start = Date(self.payment_start_date_manual)
        else:
            start = self.payment_start_date_auto()
        return Date(datetime.date.today()) - start
    total_service.short_description = 'Συνολική υπηρεσία'

    def hours(self):
        """
        Π.Ε.
        μέχρι 6 έτη        -> 23
        6 έως 12           -> 21
        12 έως 20          -> 20
        περισσότερα από 20 -> 18

        Τ.Ε.
        μέχρι 7 έτη        -> 24
        7 έως 13 έτη       -> 21
        13 έως 20          -> 20
        περισσότερα από 20 -> 18

        Δ.Ε.
        ΔΕ.01 Αρχιτεχνίτες 28
        ΔΕ.01 Τεχνίτες 30
        ΕΙΔΙΚΟ ΕΚΠΑΙΔΕΥΤΙΚΟ ΠΡΟΣΩΠΙΚΟ ( 66082/Δ3/8-5-2018)
        [u'ΠΕ21', u'ΠΕ22', u'ΠΕ23', u'ΠΕ25', u'ΠΕ28', u'ΠΕ29', u'ΠΕ30',u'ΠΕ31']
         μεχρι 5 ετη -->25
         μεχρι 10 ετη -->24
         μεχρι 15 ετη -->23
         μεχρι 20 ετη -->22
        """

        # Modified by nisiotis as suggested by mi235
        upl = self.unified_profession()
        cat = self.profession.category()
        CL = self.unified_profession()
        years = self.educational_service().years
        pe = [(5, 23), (11, 21), (19, 20), (50, 18)]
        te = [(6, 24), (12, 21), (19, 20), (50, 18)]
        eep = [(4, 25), (9, 24), (14, 23), (19, 22), (50, 22)]
        get_hours = lambda sy, l: next((y, h) for y, h in l if sy <= y)[1]
        if upl in ['ΠΕ21', 'ΠΕ22', 'ΠΕ23', 'ΠΕ25', 'ΠΕ28', 'ΠΕ29', 'ΠΕ30','ΠΕ31']:
            return get_hours(years, eep)
        elif cat == 'ΠΕ':
            return get_hours(years, pe)
        elif cat == 'ΤΕ':
            return get_hours(years, te)
        else:
            return 30
    hours.short_description = 'Υποχρεωτικό ωράριο'

    # επόμενη μείωση ωραρίου σε διάστημα 
    def hours_next(self):

        # Modified by nisiotis as suggested by mi235
        upl = self.unified_profession()
        cat = self.profession.category()
        years = self.educational_service().years
        months = self.educational_service().months
        days = self.educational_service().days
        pe = [(5, 23), (11, 21), (19, 20), (50, 18)]
        te = [(6, 24), (12, 21), (19, 20), (50, 18)]
        eep = [(4, 25), (9, 24), (14, 23), (19, 22), (50, 22)]
        get_hours = lambda sy, l: next((y, h) for y, h in l if sy <= y)[0]

        if upl in ['ΠΕ21', 'ΠΕ22', 'ΠΕ23', 'ΠΕ25', 'ΠΕ28', 'ΠΕ29', 'ΠΕ30', 'ΠΕ31']:
            dt = DateInterval(days=30 - days, months=11 - months, years=get_hours(years, eep) - years)        

        elif cat == 'ΠΕ':
            dt = DateInterval(days=30-days, months=11-months, years=get_hours(years, pe)-years)
        elif cat == 'ΤΕ':
            dt = DateInterval(days=30-days, months=11-months, years=get_hours(years, te)-years)
        else:
            dt = None # DateInterval(days=0, months=0, years=0)

        #if self.hours() == 18:
        #    return None #DateInterval(days=0, months=0, years=0)
        #else:
        #    return dt
        if self.hours() == 18 or (upl in ['ΠΕ21', 'ΠΕ22', 'ΠΕ23', 'ΠΕ25', 'ΠΕ28', 'ΠΕ29', 'ΠΕ30', 'ΠΕ31'] and  self.hours() == 22):
            return None #DateInterval(days=0, months=0, years=0)
        else:
            return dt
    hours_next.short_description = 'Επόμενη αλλαγή ωραρίου'


    def natural_key(self):
        return (self.registration_number, )

    def promotions(self):
        return self.promotion_set.all()

    # Νέοι βαθμοί με τον Νόμο 4354/2015
    def promotionsnew(self):
        return self.promotionnew_set.all()

    def permanent_post(self):
        if self.has_permanent_post:
            permanent_posts = Placement.objects.filter(
             employee=self, type__name='Οργανική').order_by('-date_from')
            return permanent_posts[0] if permanent_posts else '-'
        else:
            return '-'
    permanent_post.short_description = 'Οργανική θέση'


    def temporary_position(self):
        if self.has_permanent_post:
            return None
        else:
            return first_or_none(Placement.objects.filter(employee=self,
                                         date_from__lte=current_year_date_to,
                                         date_to__gte=current_year_date_from,
                                         type__id=3).order_by('-date_from'))
    temporary_position.short_description = 'Προσωρινή Τοποθέτηση'

    def current_year_services(self):
        return Placement.objects.filter(employee=self,
                                        type__name__in=['Μερική Διάθεση',
                                                        'Ολική Διάθεση'],
                                        date_from__gte=current_year_date_from()
                                        ).order_by('-date_from')

    def total_not_service(self):
        return self.calculable_not_service() + self.not_service_existing

    def payment_start_date_auto(self):
        if not self.date_hired:
            return Date(datetime.date.today())
        return (Date(self.date_hired) -
                DateInterval(self.recognised_experience) +
                DateInterval(days=self.total_not_service()))
    payment_start_date_auto.short_description =  'Αυτόματη αφετηρία διορισμού'

    def organization_serving(self):
        return Employee.organization_serving(self) or self.permanent_post()
    organization_serving.short_description = 'Θέση υπηρεσίας'

    def permanent_post_island(self):
        permanent_post = self.permanent_post()
        if permanent_post != "-":
            return permanent_post.organization.school.island
        else:
            return "-"
    permanent_post_island.short_description = 'Νησί Οργανικής'

    def normal_leave_days(self):
        return 10

    def rank(self):
        return first_or_none(
            Promotion.objects.filter(employee=self).order_by('-date')) or \
            Promotion(value='Χωρίς', date=datetime.date.today())
    rank.short_description = 'Παλιός Βαθμός'

    def rank_date(self):
        rankdate = first_or_none(
            Promotion.objects.filter(employee=self).order_by('-date'))
        return rankdate.date if rankdate else ''
    rank_date.short_description = 'Ημερομηνία τελευταίου βαθμού'

    def next_rank_date(self):
        rankdate = first_or_none(
            Promotion.objects.filter(employee=self).order_by('-date'))
        return rankdate.next_promotion_date
    next_rank_date.short_description = 'Ημερομηνία επόμενου βαθμού'

    def rank_id(self):
        promotion = first_or_none(
            Promotion.objects.filter(employee=self).order_by('-date'))
        if not promotion:
            return None
        else:
            rank = RankCode.objects.get(rank=promotion.value)
            return rank.id if rank else None

    rank_id.short_description = 'ID Βαθμού'

    # Νέοι βαθμοί με τον Νόμο 4354/2015
    def ranknew(self):
        return first_or_none(
            PromotionNew.objects.filter(employee=self).order_by('-date').order_by('-id')) or \
            PromotionNew(value='Χωρίς', date=datetime.date.today())
    ranknew.short_description = 'Νέος Βαθμός / Κλιμάκιο'

    def ranknew_date(self):
        rankdate = first_or_none(
            PromotionNew.objects.filter(employee=self).order_by('-date'))
        return rankdate.date if rankdate else ''
    ranknew_date.short_description = 'Ημερομηνία τελευταίου νέου βαθμού'

    def next_ranknew_date(self):
        rankdate = first_or_none(
            PromotionNew.objects.filter(employee=self).order_by('-date'))
        return rankdate.next_promotion_date
    next_ranknew_date.short_description = 'Ημερομηνία επόμενου νέου βαθμού'

    def ranknew_id(self):
        promotion = first_or_none(
            PromotionNew.objects.filter(employee=self).order_by('-date'))
        if not promotion:
            return None
        else:
            rank = RankCode.objects.get(rank=promotion.value)
            return rank.id if rank else None
    ranknew_id.short_description = 'ID Νέου Βαθμού'
    # --- Νέοι βαθμοί

    def checked_qualifications(self):
        return ['%s %s, %s' % (d.degree, d.name, d.organization) for d in EmployeeDegree.objects.filter(employee=self.parent).exclude(checked=False).order_by('-date')]

    def employment_type_text(self):
        if self.sex == "Άνδρας":
            return "μόνιμος"
        else:
            return "μόνιμη"

    def __unicode__(self):
        return '%s %s  (%s)' % (self.lastname, self.firstname,
                                self.registration_number)


PROMOTION_CHOICES = [(x, x) for x in ['ΣΤ0', 'Ε4', 'Ε3', 'Ε2', 'Ε1',
                                      'Ε0', 'Δ4', 'Δ3', 'Δ2', 'Δ1',
                                      'Δ0', 'Γ4', 'Γ3', 'Γ2', 'Γ1',
                                      'Γ0', 'Β7', 'Β6', 'Β5', 'Β4',
                                      'Β3', 'Β2', 'Β1', 'Β0', 'Α7',
                                      'Α6', 'Α5', 'Α4', 'Α3', 'Α2',
                                      'Α1', 'Α0']]


class AdministrativeManager(models.Manager):
    pass


AdministrativeManager.choices = PermanentManager.choices


class Administrative(Employee):
    class Meta:
        verbose_name = 'Διοικητικός'
        verbose_name_plural = 'Διοικητικοί'

    objects = AdministrativeManager()

    parent = models.OneToOneField(Employee, parent_link=True, on_delete=models.CASCADE)
    serving_type = models.ForeignKey(PlacementType, null=True, blank=True, verbose_name='Είδος Υπηρέτησης', on_delete=models.CASCADE)
    date_hired = models.DateField('Ημερομηνία διορισμού', null=True, blank=True)
    date_end = models.DateField('Ημερομηνία λήξης υπηρεσίας', null=True, blank=True)
    order_hired = models.CharField('Φ.Ε.Κ. διορισμού', max_length=200, null=True, blank=True)
    registration_number = NullableCharField('Αρ. Μητρώου', max_length=7, unique=True, null=True, blank=True)
    payment_start_date_manual = models.DateField('Μισθολογική αφετηρία (μετά από άδεια)', null=True, blank=True)
    is_permanent = models.NullBooleanField('Έχει μονιμοποιηθεί', null=True, blank=True, default=False)
    has_permanent_post = models.NullBooleanField('Έχει οργανική θέση', null=True, blank=True, default=False)
    not_service_existing = models.IntegerField('Αφαιρούμενες μέρες άδειας', null=True, blank=True, default=0)
    currently_serves = models.NullBooleanField('Υπηρετεί στην Δ.Δ.Ε. Δωδεκανήσου', null=True, default=True)

    def object_name(self):
        return self._meta.object_name

    def app_label(self):
        return self._meta.app_label

    def normal_leave_days(self):
        return min(24 + self.total_service().years, 29)

    def employee_type_text(self):
        if self.sex == "Άνδρας":
            return "διοικητικός"
        else:
            return "διοικητική"

methods = ["total_service", "natural_key", "promotionsnew", "promotions", "permanent_post", "total_not_service", "payment_start_date_auto",
           "organization_serving", "permanent_post_island", "rank", "rank_date", "next_rank_date", "rank_id", "ranknew", "ranknew_date", "next_ranknew_date", "ranknew_id", "__unicode__"]

for m in methods:
    setattr(Administrative, m, getattr(Permanent, m))


class Promotion(models.Model):

    class Meta:
        verbose_name = 'Μεταβολή Νόμου 4024 / 2011'
        verbose_name_plural = 'Μεταβολές Νόμου 4024 / 2011'

    value = models.CharField('Μεταβολή', max_length=100, choices=PROMOTION_CHOICES)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField('Ημερομηνία μεταβολής')
    next_promotion_date = models.DateField('Ημερομηνία επόμενης μεταβολής', null=True, blank=True)
    order = models.CharField('Απόφαση', max_length=300)
    order_pysde = models.CharField('Απόφαση Π.Υ.Σ.Δ.Ε.', max_length=300, null=True, blank=True)

    def __unicode__(self):
        return self.value


class PromotionNew(models.Model):

    class Meta:
        verbose_name = 'Μεταβολή Νόμου 4354 / 2015'
        verbose_name_plural = 'Μεταβολές Νόμου 4354 / 2015'

    rank = models.CharField('Βαθμός', max_length=5)
    value = models.ForeignKey(RankCode, verbose_name='Κλιμάκιο', on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField('Ημερομηνία μεταβολής')
    next_promotion_date = models.DateField('Ημερομηνία επόμενης μεταβολής', null=True, blank=True)
    time_left = models.CharField('Πλεονάζων χρόνος στον βαθμό μέχρι 31/12/2015 (ΕΕΜΜΗΗ)', max_length=10, null=True, blank=True)
    order = models.CharField('Απόφαση', max_length=300)
    order_pysde = models.CharField('Απόφαση Π.Υ.Σ.Δ.Ε.', max_length=300, null=True, blank=True)

    def __unicode__(self):
        return "%s %s" % (self.rank, self.value)

class NonPermanentTypeManager(models.Manager):

    def get_by_natural_key(self, name):
        return self.get(name=name)


WORK_TYPES = ((0, 'Πλήρης'),
              (1, 'Μερική'),
              (2, 'Εκ περιτροπής'))



class NonPermanentType(models.Model):

    class Meta:
        verbose_name = 'Κατηγορία μη-μόνιμης απασχόλησης'
        verbose_name_plural = 'Κατηγορίες μη-μόνιμης απασχόλησης'

    objects = NonPermanentTypeManager()

    name = models.CharField(max_length=200, verbose_name='Κατηγορία')
    work_mode = models.IntegerField('Καθεστός απασχόλησης (ΟΑΕΔ)', max_length=2, null=True, blank=True, choices=WORK_TYPES)

    def natural_key(self):
        return (self.name, )

    def __unicode__(self):
        return self.name


class NonPermanentManager(models.Manager):
    def substitutes_in_transfer_area(self, area_id):
        ids = []
        for s in OrderedSubstitution.objects.filter(transfer_area=area_id):
            ids.append(s.substitute_id)
        return self.filter(parent_id__in=ids)

    def substitutes_in_order(self, order_id):
        ids = [s.substitute_id for s in OrderedSubstitution.objects.filter(order_id=order_id)]
        return self.filter(parent_id__in=ids)

    def substitutes_in_date_range(self, date_from, date_to):
        ids = [s.substitute_id for s in OrderedSubstitution.objects.\
                   filter(order__date__lte=date_to,
                          order__date__gte=date_from)]
        return self.filter(parent_id__in=ids)

    def temporary_post_in_organization(self, org_id):
        td = datetime.date.today()
        ids = [o.employee_id
               for o in Placement.objects.only('employee').filter(
                date_from__lte=td, date_to__gte=td, type__id=3,
                organization_id=org_id)]
        return self.filter(id__in=ids)

    def with_total_extra_position(self, exclude=False):
        td = datetime.date.today()
        ids = [o.employee_id
               for o in Placement.objects.only('employee').filter(
                date_from__lte=td, date_to__gte=td, type__id=4)]
        if exclude:
            return self.exclude(id__in=ids)
        else:
            return self.filter(id__in=ids)

    def choices(self):
        cursor = connection.cursor()
        cursor.execute(sql.current_year_non_permanents.format(current_year_date_from()))
        choices = [(row[0], "%s %s (%s)" % (row[1], row[2], row[3])) for row in cursor.fetchall()]
        return [(None, '---------')] + choices


EDU_LEVEL = ((11, 'ΑΕΙ'),
             (13, 'ΑΛΛΟ'),
             (3, 'ΓΥΜΝΑΣΙΟ'),
             (1, 'ΔΕΝ ΠΗΓΕ ΚΑΘΟΛΟΥ ΣΧΟΛΕΙΟ'),
             (2, 'ΔΗΜΟΤΙΚΟ'),
             (17, 'ΔΙΔΑΚΤΟΡΙΚΟ'),
             (4, 'ΕΝΙΑΙΟ ΛΥΚΕΙΟ'),
             (9, 'ΙΕΚ ΜΕ ΠΙΣΤΟΠΟΙΗΣΗ'),
             (14, 'ΙΕΚ ΧΩΡΙΣ ΠΙΣΤΟΠΟΙΗΣΗ'),
             (8, 'ΜΑΘΗΤΕΙΑ'),
             (12, 'ΜΕΤΑΠΤΥΧΙΑΚΟ'),
             (6, 'ΠΟΛΥΚΛΑΔΙΚΟ'),
             (15, 'ΤΕΕ Α ΚΥΚΛΟΥ'),
             (16, 'ΤΕΕ Β ΚΥΚΛΟΥ'),
             (10, 'ΤΕΙ'),
             (5, 'ΤΕΛ'),
             (7, 'ΤΕΣ'))


class NonPermanent(Employee):

    class Meta:
        verbose_name = 'Αναπληρωτής/Ωρομίσθιος'
        verbose_name_plural = 'Αναπληρωτές/Ωρομίσθιοι'

    objects = NonPermanentManager()

    parent = models.OneToOneField(Employee, parent_link=True, on_delete=models.CASCADE)
    pedagogical_sufficiency = models.BooleanField('Παιδαγωγική κατάρτιση', default=None)
    social_security_number = models.CharField('Αριθμός Ι.Κ.Α.', max_length=10, null=True, blank=True)
    profession_code_oaed = models.CharField('Κωδικός ειδικότητας ΟΑΕΔ', max_length=10, null=True, blank=True)
    show_exp_report = models.NullBooleanField('Εμφάνιση Προϋπηρεσίας - Απόλυσης', null=True, blank=True, default=True)

    educational_level = models.IntegerField('Επίπεδο μόρφωσης', null=True, blank=True, choices=EDU_LEVEL, default=11)
    ergani_new = models.NullBooleanField('Νέος Μισθωτός', null=True, blank=True, default=False)

    def object_name(self):
        return self._meta.object_name

    def app_label(self):
        return self._meta.app_label

    def order(self, d=current_year_date_from()):
        return first_or_none(self.substituteministryorder_set.filter(date__gte=d))
    order.short_description = 'Υπουργική απόφαση τρέχουσας τοποθέτησης'

    def substitution(self, d=current_year_date_from()):
        return first_or_none(self.orderedsubstitution_set.filter(order__date__gte=d))

    def current_placement(self, d=current_year_date_from()):
        return first_or_none(self.placement_set.filter(date_from__gte=d, type__id=3))
    current_placement.short_description = 'Προσωρινή τοποθέτηση'

    def organization_serving(self):
        return self.total_extra_position_school() or self.current_placement()
    organization_serving.short_description = 'Θέση υπηρεσίας'

    def total_extra_position_school(self):
        td = datetime.date.today()
        return first_or_none(self.placement_set.filter(date_from__lte=td, date_to__gte=td, type__id=4))

    def current_transfer_area(self, d=current_year_date_from()):
        s = self.substitution(d)
        return s.transfer_area if s else None
    current_transfer_area.short_description = 'Περιοχή τοποθέτησης'

    def type(self, d=current_year_date_from()):
        s = self.substitution(d)
        return s.type if s else None
    type.short_description = 'Τύπος απασχόλησης'

    def experience(self):
        p = self.current_placement()
        if p:
            return Date(p.date_to) - Date(p.date_from) + DateInterval(days=1)
        else:
            return DateInterval()

    def experience_salary(self):
        p = self.current_placement()
        #import pdb; pdb.set_trace()
        if p:
            if p.substituteplacement.date_from_show:
                return Date(p.date_to) - Date(p.substituteplacement.date_from_show) + DateInterval(days=1)
            else:
                return Date(p.date_to) - Date(p.date_from) + DateInterval(days=1)
        else:
            return DateInterval()

    def employment_type_text(self):
        t = self.type()
        if t is not None:
            if t.name == "Ωρομίσθιος":
                if self.sex == "Άνδρας":
                    return "ωρομίσθιος"
                else:
                    return "ωρομίσθιας"
            else:
                if self.sex == "Άνδρας":
                    return "αναπληρωτής"
                else:
                    return "αναπληρώτρια"

    def normal_leave_days(self):
        return 7

    def __unicode__(self):
        return '%s %s του %s' % (self.lastname, self.firstname, self.fathername)


class EmployeeProfession(models.Model):
    class Meta:
        verbose_name = 'Επιπλέον ειδικότητα εκπαιδευτικού'
        verbose_name_plural = 'Επιπλέον ειδικότητες εκπαιδευτικών'

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    profession = models.ForeignKey(Profession, on_delete=models.CASCADE)


class SchoolTypeManager(models.Manager):

    def get_by_natural_key(self, name):
        return self.get(name=name)


class SchoolType(models.Model):

    class Meta:
        verbose_name = 'Κατηγορία σχολείου'
        verbose_name_plural = 'Κατηγορίες σχολείων'

    objects = SchoolTypeManager()

    name = models.CharField(max_length=100, verbose_name='Πλήρες αναγνωριστικό')
    shift = models.CharField(max_length=100, verbose_name='Ωράριο', choices=(('day', 'Ημερήσιο'), ('night', 'Εσπερινό'), ('other', 'Άλλο')))
    category = models.CharField(max_length=100, verbose_name='Κατηγορία', choices=(('gym', 'Γυμνάσιο'), ('lyk', 'Γενικό Λύκειο'), ('epag', 'Επαγγελματική Εκπαίδευση'), ('other', 'Άλλο')))
    # < 20 : Γυμνάσια, > 10 : Μεταγυμνασιακά
    rank = models.IntegerField(max_length=2, verbose_name='Βαθμίδα', choices=((10, 'Γυμνάσιο'), (20, 'ΜεταΓυμνασιακό'), (15, 'Γυμνάσιο/Λ.Τ.'), (11, 'Ιδιωτικό')))

    def natural_key(self):
        return (self.name, )

    def __unicode__(self):
        return self.name


class SchoolManager(models.Manager):

    def get_by_natural_key(self, code):
        return self.get(code=code)


MUNICIPALITIES = ("Αγαθονησίου", "Αστυπάλαιας", "Καλυμνίων", "Καρπάθου", "Κάσου", "Κω", "Λειψών", "Λέρου",
                  "Μεγίστης",  "Νισύρου", "Πάτμου", "Ρόδου", "Σύμης", "Τήλου", "Χάλκης")
MUNICIPALITIES_CHOICES = [(x, x) for x in MUNICIPALITIES]


class SchoolCommission(models.Model):

    class Meta:
        verbose_name = 'Σχολική επιτροπή'
        verbose_name_plural = 'Σχολικές επιτροπές'
        ordering = ['municipality']

    municipality = models.CharField('Δήμος', max_length=100, choices=MUNICIPALITIES_CHOICES)
    vat_number = models.CharField('Α.Φ.Μ.', max_length=9, unique=True)
    tax_office = models.CharField('Δ.Ο.Υ.', max_length=100)
    bank = models.CharField('Τράπεζα', max_length=100, null=True, blank=True)
    bank_account_number = models.CharField('Αριθμός λογαριασμού τράπεζας', max_length=100, null=True, blank=True)
    iban = models.CharField('IBAN', max_length=27, null=True, blank=True)



    def __unicode__(self):
        return 'Σχολική Επιτροπή Δήμου ' + self.municipality

class School(Organization):

    class Meta:
        verbose_name = 'Σχολείο'
        verbose_name_plural = 'Σχολεία'
        ordering = ['name']

    objects = SchoolManager()

    parent_organization = models.OneToOneField(Organization, parent_link=True, on_delete=models.CASCADE)
    transfer_area = models.ForeignKey(TransferArea, verbose_name='Περιοχή Μετάθεσης', on_delete=models.CASCADE)
    island = models.ForeignKey(Island, verbose_name='Νησί', null=True, blank=True, on_delete=models.CASCADE)
    commission = models.ForeignKey(SchoolCommission, verbose_name='Σχολική επιτροπή', null=True, blank=True, on_delete=models.CASCADE)
    points = models.IntegerField('Μόρια', max_length=2, null=True, blank=True)
    code = models.IntegerField('Κωδικός Σχολείου', max_length=5, unique=True)
    # γενικό λύκειο, γυμνάσιο, επαλ...
    type = models.ForeignKey(SchoolType, verbose_name='Κατηγορία', on_delete=models.CASCADE)
    inaccessible = models.BooleanField('Δυσπρόσιτο', default=None)
    address = models.CharField('Διεύθυνση', max_length=200, null=True, blank=True)
    post_code = models.CharField('Τ.Κ.', max_length=5, null=True, blank=True)
    telephone_number = models.CharField('Αρ. Τηλεφώνου', max_length=14, null=True, blank=True)
    fax_number = models.CharField('Αρ. Fax', max_length=14, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    manager = models.ForeignKey(Permanent, null=True, blank=True, verbose_name='Διευθυντής', on_delete=models.CASCADE)
    google_maps_x = models.CharField('Γεωγραφικές συντεταγμένες Χ', max_length=14, null=True, blank=True)
    google_maps_y = models.CharField('Γεωγραφικές συντεταγμένες Υ', max_length=14, null=True, blank=True)

    def commission_data(self):
        return "ΑΦΜ: %s , ΔΟΥ: %s" % (self.commission.vat_number, self.commission.tax_office)
    commission_data.short_description = 'Στοιχεία σχολ. επ.'

    def natural_key(self):
        return (self.code, )


class GymLyc(School):

    class Meta:
        verbose_name = 'Γυμνάσιο-Λ.Τ.'
        verbose_name_plural = 'Γυμνάσια-Λ.Τ.'

    parent_school = models.OneToOneField(School, parent_link=True, on_delete=models.CASCADE)
    gymlyc_code = models.IntegerField('Κωδικός Λυκειακών τάξεων', max_length=5, unique=True)


class OtherOrganization(Organization):

    class Meta:
        verbose_name = 'Άλλος φορέας'
        verbose_name_plural = 'Άλλοι φορείς'
        ordering = ['name']

    parent_organization = models.OneToOneField(Organization, parent_link=True, on_delete=models.CASCADE)
    description = models.CharField(max_length=300, null=True, blank=True, verbose_name='Περιγραφή')

# PLACEMENT_TYPES = ((1, 'Οργανική'), (2, 'Απόσπαση'),
#    (3, 'Διάθεση'), (4, 'Προσωρινή τοποθέτηση'))


class Placement(models.Model):

    class Meta:
        verbose_name = 'Τοποθέτηση'
        verbose_name_plural = 'Τοποθετήσεις'
        ordering = ['-date_from']

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, verbose_name='Σχολείο/Φορέας', on_delete=models.CASCADE)
    date_from = models.DateField('Ημερομηνία Έναρξης')
    date_to = models.DateField('Ημερομηνία Λήξης', null=True, blank=True)
    type = models.ForeignKey(PlacementType, verbose_name='Είδος τοποθέτησης', default=1, on_delete=models.CASCADE)
    order = models.CharField('Απόφαση', max_length=300, null=True, blank=True, default=None)
    order_pysde = models.CharField('Απόφαση Π.Υ.Σ.Δ.Ε.', max_length=300, null=True, blank=True)
    # New field to add for the type of experience
    teaching_service = models.NullBooleanField('Είναι διδακτική προϋπηρεσία;', null=True, default=True)
    reduce_hours = models.NullBooleanField('Προσμέτρηση για μείωση ωραρίου', null=True, default=True)

    def natural_key(self):
        return (self.employee, self.organization, self.date_from)

    def __unicode__(self):
        return self.organization.name


class Service(Placement):

    class Meta:
        verbose_name = 'Διάθεση'
        verbose_name_plural = 'Διαθέσεις'
        ordering = ['-date_from']

    parent = models.OneToOneField(Placement, parent_link=True, on_delete=models.CASCADE)
    order_manager = models.CharField('Απόφαση Διευθυντή', max_length=300, null=True, blank=True, default=None)
    hours = models.IntegerField('Ώρες μείωσης', max_length=2, null=True, blank=True)
    hours_overtime = models.IntegerField('Ώρες Υπερωρίας', max_length=2, null=True, blank=True, default=0)

    def __unicode__(self):
        return self.organization.name + self.date_from.strftime('%d-%m-%Y')


# Μερικές διαθέσεις - δεν είναι τοποθετήσεις
class PartialService(models.Model):

    class Meta:
        verbose_name = 'Μερική Διάθεση'
        verbose_name_plural = 'Μερικές Διαθέσεις'
        ordering = ['-date_from']

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, verbose_name='Σχολείο/Φορέας', on_delete=models.CASCADE)
    date_from = models.DateField('Ημερομηνία Έναρξης')
    date_to = models.DateField('Ημερομηνία Λήξης', null=True, blank=True)
    type = models.ForeignKey(PlacementType, verbose_name='Είδος διάθεσης', default=None, on_delete=models.CASCADE)
    order_min = models.CharField('Απόφαση', max_length=300, null=True, blank=True, default=None)
    order_pysde = models.CharField('Απόφαση Π.Υ.Σ.Δ.Ε.', max_length=300, null=True, blank=True)
    order_manager = models.CharField('Απόφαση Διευθυντή', max_length=300, null=True, blank=True, default=None)
    hours = models.IntegerField('Ώρες Διάθεσης', max_length=2, null=True, blank=True)
    hours_overtime = models.IntegerField('Ώρες Υπερωρίας', max_length=2, null=True, blank=True, default=0)

    def natural_key(self):
        return (self.employee, self.organization, self.date_from)

    def __unicode__(self):
        return self.organization.name


class SubstituteMinistryOrder(models.Model):

    class Meta:
        verbose_name = 'Υπουργική απόφαση αναπληρωτών'
        verbose_name_plural = 'Υπουργικές αποφάσεις αναπληρωτών'
        ordering = ['-date']

    order = models.CharField('Υπουργική Απόφαση', max_length=300)
    date = models.DateField('Ημερομηνία')
    web_code = models.CharField('Αρ. Διαδικτυακής ανάρτησης', max_length=100)
    order_start_manager = models.CharField('Απόφαση τοποθέτησης Διεθυντή Δ.Ε.', max_length=300, null=True, blank=True)
    order_end_manager = models.CharField('Απόφαση απόλυσης Διευθυντή Δ.Ε.', max_length=300, null=True, blank=True)
    order_pysde = models.CharField('Απόφαση Π.Υ.Σ.Δ.Ε.', max_length=300, null=True, blank=True)
    order_type = models.IntegerField(max_length=1, verbose_name='Μισθοδοσία', choices=((1, 'Τακτικός Προυπολογισμός'), (2, 'Πρόγραμμα Δημοσίων Επενδύσεων'), (3, 'Ε.Σ.Π.Α.'), (4, 'Ταμείο Ασύλου')))
    show_online_order = models.NullBooleanField('Εμφάνιση στο χρήστη', null=True, blank=True, default=True)
    substitutes = models.ManyToManyField(NonPermanent, through='OrderedSubstitution', verbose_name='Αναπηρωτές')

    def __unicode__(self):
        return '%s - %s' % (self.order, str(self.date))

    def order_no(self):
        return '%s' % self.order_pysde

    def subs_in_order_count(self):
        return self.substitutes.count()

    subs_in_order_count.short_description = 'Αριθμός αναπληρωτών'


class OrderedSubstitution(models.Model):

    class Meta:
        verbose_name = 'Αναπλήρωση από υπουργική απόφαση'
        verbose_name_plural = 'Αναπληρώσεις από υπουργικές αποφάσεις'

    order = models.ForeignKey(SubstituteMinistryOrder, verbose_name='Υπουργική απόφαση', on_delete=models.CASCADE)
    substitute = models.ForeignKey(NonPermanent, verbose_name='Αναπλήρωτής', on_delete=models.CASCADE)
    type = models.ForeignKey(NonPermanentType, verbose_name='Σχέση απασχόλησης', on_delete=models.CASCADE)
    transfer_area = models.ForeignKey(TransferArea, verbose_name='Περιοχή Μετάθεσης', on_delete=models.CASCADE)

    def __unicode__(self):
        return str(self.substitute)

OAED_CHOICES = ((101303,'Ε.Κ.Ο. ΑΘΗΝΑΣ'), (301202,'ΚΠΑ2 25ης ΜΑΡΤΙΟΥ'),
                (101213,'ΚΠΑ2 ΑΓ. ΑΝΑΡΓΥΡΩΝ - ΙΛΙΟΥ'), (108202,'ΚΠΑ2 ΑΓ.ΚΗΡΥΚΑ ΙΚΑΡΙΑΣ'),
                (704201,'ΚΠΑ2 ΑΓ.ΝΙΚΟΛΑΟΥ'), (101202,'ΚΠΑ2 ΑΓ.ΠΑΡΑΣΚΕΥΗΣ'),
                (601203,'ΚΠΑ2 ΑΓΙΟΥ ΑΝΔΡΕΑ ΠΑΤΡΑΣ'), (608201,'ΚΠΑ2 ΑΓΡΙΝΙΟΥ'),
                (101201,'ΚΠΑ2 ΑΘΗΝΩΝ'), (101225,'ΚΠΑ2 ΑΙΓΑΛΕΩ'), (601202,'ΚΠΑ2 ΑΙΓΙΟΥ'),
                (307202,'ΚΠΑ2 ΑΛΕΞΑΝΔΡΕΙΑΣ'), (206201,'ΚΠΑ2 ΑΛΕΞΑΝΔΡΟΥΠΟΛΗΣ'),
                (701202,'ΚΠΑ2 ΑΛΙΚΑΡΝΑΣΣΟΥ'), (402202,'ΚΠΑ2 ΑΛΜΥΡΟΥ'),
                (604202,'ΚΠΑ2 ΑΜΑΛΙΑΔΑΣ'), (101206,'ΚΠΑ2 ΑΜΑΡΟΥΣΙΟΥ'),
                (101208,'ΚΠΑ2 ΑΜΠΕΛΟΚΗΠΩΝ'), (309202,'ΚΠΑ2 ΑΜΥΝΤΑΙΟΥ'),
                (609201,'ΚΠΑ2 ΑΜΦΙΣΣΑΣ'), (610201,'ΚΠΑ2 ΑΡΓΟΣΤΟΛΙΟΥ'), (602202,'ΚΠΑ2 ΑΡΓΟΥΣ'),
                (304201,'ΚΠΑ2 ΑΡΙΔΑΙΑΣ'), (302203,'ΚΠΑ2 ΑΡΝΑΙΑΣ'), (502201,'ΚΠΑ2 ΑΡΤΑΣ'),
                (105202,'ΚΠΑ2 ΑΡΧΑΓΓΕΛΟΥ ΡΟΔΟΥ'), (101224,'ΚΠΑ2 ΑΧΑΡΝΩΝ'),
                (307201,'ΚΠΑ2 ΒΕΡΟΙΑΣ'), (402201,'ΚΠΑ2 ΒΟΛΟΥ'), (304203,'ΚΠΑ2 ΓΙΑΝΝΙΤΣΩΝ'),
                (101228,'ΚΠΑ2 ΓΛΥΦΑΔΑΣ'), (303202,'ΚΠΑ2 ΓΟΥΜΕΝΙΣΣΑΣ'), (407201,'ΚΠΑ2 ΓΡΕΒΕΝΩΝ'), 
                (101230,'ΚΠΑ2 ΔΑΦΝΗΣ'), (206203,'ΚΠΑ2 ΔΙΔΥΜΟΤΕΙΧΟΥ'), (203201,'ΚΠΑ2 ΔΡΑΜΑΣ'),
                (304202,'ΚΠΑ2 ΕΔΕΣΣΑΣ'), (401202,'ΚΠΑ2 ΕΛΑΣΣΟΝΑΣ'),
                (201202,'ΚΠΑ2 ΕΛΕΥΘΕΡΟΥΠΟΛΗΣ'), (101221,'ΚΠΑ2 ΕΛΕΥΣΙΝΑΣ'), (611201,'ΚΠΑ2 ΖΑΚΥΝΘΟΥ'), 
                (504201,'ΚΠΑ2 ΗΓΟΥΜΕΝΙΤΣΑΣ'), (701201,'ΚΠΑ2 ΗΡΑΚΛΕΙΟΥ ΚΡΗΤΗΣ'), (201204,'ΚΠΑ2 ΘΑΣΟΥ'),
                (301201,'ΚΠΑ2 ΘΕΣ/ΝΙΚΗΣ'), (102201,'ΚΠΑ2 ΘΗΒΩΝ'), (704203,'ΚΠΑ2 ΙΕΡΑΠΕΤΡΑΣ'), 
                (501201,'ΚΠΑ2 ΙΩΑΝΝΙΝΩΝ'), (301204,'ΚΠΑ2 ΙΩΝΙΑΣ ΘΕΣ/ΝΙΚΗΣ'), (201201,'ΚΠΑ2 ΚΑΒΑΛΑΣ'),
                (101218,'ΚΠΑ2 ΚΑΙΣΑΡΙΑΝΗΣ'), (605201,'ΚΠΑ2 ΚΑΛΑΜΑΤΑΣ'), (404202,'ΚΠΑ2 ΚΑΛΑΜΠΑΚΑΣ'), 
                (101203,'ΚΠΑ2 ΚΑΛΛΙΘΕΑΣ-ΜΟΣΧΑΤΟΥ'), (405201,'ΚΠΑ2 ΚΑΡΔΙΤΣΑΣ'), (406201,'ΚΠΑ2 ΚΑΡΠΕΝΗΣΙΟΥ'),
                (308201,'ΚΠΑ2 ΚΑΣΤΟΡΙΑΣ'), (305201,'ΚΠΑ2 ΚΑΤΕΡΙΝΗΣ'),
                (101217,'ΚΠΑ2 ΚΕΡΑΤΣΙΝΙΟΥ'), (505201,'ΚΠΑ2 ΚΕΡΚΥΡΑΣ'), (101246,'ΚΠΑ2 ΚΗΦΙΣΙΑΣ'),
                (607202,'ΚΠΑ2 ΚΙΑΤΟΥ'), (303201,'ΚΠΑ2 ΚΙΛΚΙΣ'), (306201,'ΚΠΑ2 ΚΟΖΑΝΗΣ'),
                (205201,'ΚΠΑ2 ΚΟΜΟΤΗΝΗΣ'), (607201,'ΚΠΑ2 ΚΟΡΙΝΘΟΥ'), (105203,'ΚΠΑ2 ΚΩ'),
                (301208,'ΚΠΑ2 ΛΑΓΚΑΔΑ'), (403201,'ΚΠΑ2 ΛΑΜΙΑΣ'), (401201,'ΚΠΑ2 ΛΑΡΙΣΑΣ'),
                (101231,'ΚΠΑ2 ΛΑΥΡΙΟΥ'), (102202,'ΚΠΑ2 ΛΕΙΒΑΔΙΑΣ'), (506201,'ΚΠΑ2 ΛΕΥΚΑΔΑΣ'),
                (505202,'ΚΠΑ2 ΛΕΥΚΙΜΗΣ'), (607203,'ΚΠΑ2 ΛΟΥΤΡΑΚΙΟΥ'), (101233,'ΚΠΑ2 ΜΑΡΚΟΠΟΥΛΟΥ'),
                (101223,'ΚΠΑ2 ΜΕΓΑΡΩΝ'), (608202,'ΚΠΑ2 ΜΕΣΟΛΟΓΓΙΟΥ'), (106201,'ΚΠΑ2 ΜΥΤΙΛΗΝΗΣ'),
                (101207,'ΚΠΑ2 Ν.ΙΩΝΙΑΣ'), (302202,'ΚΠΑ2 Ν.ΜΟΥΔΑΝΙΩΝ'), (104202,'ΚΠΑ2 ΝΑΞΟΥ'),
                (307203,'ΚΠΑ2 ΝΑΟΥΣΑΣ'), (608203,'ΚΠΑ2 ΝΑΥΠΑΚΤΟΥ'), (602201,'ΚΠΑ2 ΝΑΥΠΛΙΟΥ'),
                (301205,'ΚΠΑ2 ΝΕΑΠΟΛΗΣ'), (202202,'ΚΠΑ2 ΝΙΓΡΙΤΑΣ'), (101222,'ΚΠΑ2 ΝΙΚΑΙΑΣ'),
                (204201,'ΚΠΑ2 ΞΑΝΘΗΣ'), (206202,'ΚΠΑ2 ΟΡΕΣΤΙΑΔΑΣ'), (101210,'ΚΠΑ2 ΠΑΛΛΗΝΗΣ'),
                (104203,'ΚΠΑ2 ΠΑΡΟΥ'), (101209,'ΚΠΑ2 ΠΑΤΗΣΙΩΝ'), (601201,'ΚΠΑ2 ΠΑΤΡΑΣ'),
                (101204,'ΚΠΑ2 ΠΕΙΡΑΙΑ'), (101205,'ΚΠΑ2 ΠΕΡΙΣΤΕΡΙΟΥ'), (101245,'ΚΠΑ2 ΠΛ. ΑΤΤΙΚΗΣ'),
                (302201,'ΚΠΑ2 ΠΟΛΥΓΥΡΟΥ'), (503201,'ΚΠΑ2 ΠΡΕΒΕΖΑΣ'), (306202,'ΚΠΑ2 ΠΤΟΛΕΜΑΪΔΑΣ'),
                (301203,'ΚΠΑ2 ΠΥΛΗΣ ΑΞΙΟΥ'), (604201,'ΚΠΑ2 ΠΥΡΓΟΥ'), (702201,'ΚΠΑ2 ΡΕΘΥΜΝΟΥ'),
                (105201,'ΚΠΑ2 ΡΟΔΟΥ'), (108201,'ΚΠΑ2 ΣΑΜΟΥ'), (104204,'ΚΠΑ2 ΣΑΝΤΟΡΙΝΗΣ'),
                (205202,'ΚΠΑ2 ΣΑΠΩΝ'), (202201,'ΚΠΑ2 ΣΕΡΡΩΝ'), (704202,'ΚΠΑ2 ΣΗΤΕΙΑΣ'),
                (202203,'ΚΠΑ2 ΣΙΔΗΡΟΚΑΣΤΡΟΥ'), (606201,'ΚΠΑ2 ΣΠΑΡΤΗΣ'), (104201,'ΚΠΑ2 ΣΥΡΟΥ'),
                (301206,'ΚΠΑ2 ΤΟΥΜΠΑΣ'), (404201,'ΚΠΑ2 ΤΡΙΚΑΛΩΝ'), (603201,'ΚΠΑ2 ΤΡΙΠΟΛΗΣ'),
                (309201,'ΚΠΑ2 ΦΛΩΡΙΝΑΣ'), (103201,'ΚΠΑ2 ΧΑΛΚΙΔΑΣ'),
                (703201,'ΚΠΑ2 ΧΑΝΙΩΝ'), (107201,'ΚΠΑ2 ΧΙΟΥ'), (201203,'ΚΠΑ2 ΧΡΥΣΟΥΠΟΛΗΣ'))


class SubstitutePlacement(Placement):

    class Meta:
        verbose_name = 'Τοποθέτηση Αναπληρωτή'
        verbose_name_plural = 'Τοποθετήσεις Αναπληρωτών'

    parent = models.OneToOneField(Placement, parent_link=True, on_delete=models.CASCADE)
    ministry_order = models.ForeignKey(SubstituteMinistryOrder, verbose_name='Υπουργική Απόφαση', on_delete=models.CASCADE)

    last_total_grosspay = models.CharField('Σύνολο μεικτών αποδοχών κατά την απόλυση', max_length=10, null=True, blank=True)
    last_hourspay = models.CharField('Ωρομίσθιο', max_length=10, null=True, blank=True)
    week_hours = models.CharField('Ώρες εργασίας / εβδομάδα', max_length=10, null=True, blank=True)
    work_experience_years = models.CharField('Έτη προϋπηρεσίας', max_length=3, null=True, blank=True)

    date_from_show = models.DateField('Ημερομηνία ανάληψης υπηρεσίας', null=True, blank=True)
    oaed_nopay = models.NullBooleanField('Επίδομα ΟΑΕΔ', null=True, blank=True, default=True)
    oaed_nopay_from = models.IntegerField(max_length=6, null=True, blank=True, 
                                          verbose_name='Κατάστημα Επιδόματος ΟΑΕΔ',
                                          choices=OAED_CHOICES)


#class NonPermanentLeave(models.Model):

#    class Meta:
#        verbose_name = u'Άδεια Αναπληρωτή/Ωρoμίσθιου'
#        verbose_name_plural = u'Άδειες Αναπληρωτών/Ωρoμισθίων'
#        ordering = ['-date_to']
#
#    non_permanent = models.ForeignKey(NonPermanent, verbose_name=u'Υπάλληλος')
#    leave = models.ForeignKey(Leave, verbose_name=u'Κατηγορία Άδειας')
#    date_issued = models.DateField(u'Χορήγηση', null=True, blank=True)
#    date_from = models.DateField(u'Έναρξη')
#    date_to = models.DateField(u'Λήξη')
#    order = models.CharField(u'Απόφαση', max_length=300, null=True, blank=True)
#    authority = models.CharField(u'Αρχή έγκρισης', max_length=200, null=True, blank=True)
#    protocol_number = models.CharField(u'Αρ. πρωτ.', max_length=10, null=True, blank=True)
#    description = models.CharField(u'Σημειώσεις', null=True, blank=True, max_length=300)
#    duration = models.IntegerField(max_length=3, verbose_name=u'Διάρκεια')

#    @shorted(15)
#    def category(self):
#        return self.leave.name
#    category.short_description = u'Κατηγορία'

#    def affects_payment(self):
#        return self.leave.not_paying or self.leaveperiod_set.exclude(payment='yes').count() > 0

#    def organization_serving(self):
#        return self.employee.subclass().organization_serving()
#    organization_serving.short_description = u'Θέση υπηρεσίας'

#    def profession(self):
#        return self.non_permanent.profession
#    profession.short_description = u'Ειδικότητα'

#    def period_description(self):
#        periods = self.leaveperiod_set.all()
#        if len(periods) > 0:
#            if len(periods) > 1:
#                desc = u"%s ημερών για τα διαστήματα %s " %(self.duration, u", ".join(map(unicode, periods)))
#            else:
#                desc = u", ".join(map(unicode, periods))
#        else:
#            if self.leave.not_paying:
#                s = u"χωρίς αποδοχές"
#            else:
#                s = u"με αποδοχές"
#            if self.duration == 1:
#                dur_desc = u"ημέρα"
#            else:
#                dur_desc = u"ημέρες"

#            desc = u"από %s έως %s (%s %s %s)" % (self.date_from, self.date_to, self.duration, dur_desc, s)
#        return desc

#    def clean(self):
#        from django.core.exceptions import ValidationError
#        if hasattr(self, 'leave') and hasattr(self, 'non_permanent'):
#            limit = self.non_permanent.normal_leave_days()

#            if self.leave.name == u'Κανονική':
#                y = self.date_from.year
#                dur = EmployeeLeave.objects.filter(
#                    employee=self.non_permanent, leave=self.leave, date_from__gte=current_year_date_from(),
#                    date_to__lte=current_year_date_to()
#                ).exclude(id=self.id).aggregate(Sum('duration'))['duration__sum'] or 0

#                msg = u'Οι ημέρες κανονικής άδειας ξεπερνούν τις {0}. Μέρες χωρίς την τρέχουσα άδεια: {1}'
#                if dur + self.duration > limit:
#                    raise ValidationError(msg.format(limit, dur))


#    def __unicode__(self):
#        return unicode(self.non_permanent) + '-' + unicode(self.date_from)



#LEAVE_PERIOD_CHOICES = (('no', u'Χωρίς Αποδοχές'),
#                        ('yes', u'Με Αποδοχές'),
#                        ('half', u'Μισές Αποδοχές'))

#class LeavePeriod(models.Model):

#    class Meta:
#        verbose_name = u'Χρονικό Διάστημα'
#        verbose_name_plural = u'Χρονικά Διαστήματα'

#    date_from = models.DateField(u'Έναρξη')
#    date_to = models.DateField(u'Λήξη')
#    duration = models.IntegerField(max_length=3, verbose_name=u'Διάρκεια')
#    payment = models.CharField(u'Καθεστώς Πληρωμής', max_length=10, choices=LEAVE_PERIOD_CHOICES)
#    leave = models.ForeignKey(NonPermanentLeave, verbose_name=u'Άδεια')

#    def __unicode__(self):
#        if self.duration == 1:
#            dur_desc = u"ημέρα"
#        else:
#            dur_desc = u"ημέρες"
#        return u"από %s έως %s (%s %s, %s)" % (self.date_from, self.date_to, self.duration, dur_desc, dict(LEAVE_PERIOD_CHOICES)[self.payment].lower())


class EmployeeLeaveManager(models.Manager):

    def date_range_intersect(self, ds, de):
        return self.exclude(Q(date_to__lt=ds) | Q(date_from__gt=de))


class EmployeeLeave(models.Model):

    class Meta:
        verbose_name = 'Άδεια'
        verbose_name_plural = 'Άδειες'
        ordering = ['-date_to']

    objects = EmployeeLeaveManager()
    employee = models.ForeignKey(Employee, verbose_name='Υπάλληλος', on_delete=models.CASCADE)
    leave = models.ForeignKey(Leave, verbose_name='Κατηγορία Άδειας', on_delete=models.CASCADE)
    date_issued = models.DateField('Χορήγηση', null=True, blank=True)
    date_from = models.DateField('Έναρξη')
    date_to = models.DateField('Λήξη')
    order = models.CharField('Απόφαση', max_length=300, null=True, blank=True)
    authority = models.CharField('Αρχή έγκρισης', max_length=200, null=True, blank=True)
    protocol_number = models.CharField('Αρ. πρωτ.', max_length=10, null=True, blank=True)
    description = models.CharField('Σημειώσεις', null=True, blank=True, max_length=300)
    duration = models.IntegerField(max_length=3, verbose_name='Διάρκεια')

    @shorted(15)
    def category(self):
        return self.leave.name
    category.short_description = 'Κατηγορία'

    def permanent_post(self):
        if hasattr(self.employee, 'permanent'):
            return self.employee.permanent.permanent_post()
        else:
            return None
    permanent_post.short_description = 'Οργανική θέση'

    def organization_serving(self):
        return self.employee.subclass().organization_serving()
    organization_serving.short_description = 'Θέση υπηρεσίας'

    def profession(self):
        return self.employee.profession
    profession.short_description = 'Ειδικότητα'

    def clean(self):
        from django.core.exceptions import ValidationError
        if hasattr(self, 'leave') and hasattr(self, 'employee'):
            if hasattr(self.employee, 'permanent'):
                limit = self.employee.permanent.normal_leave_days()
            elif hasattr(self.employee, 'administrative'):
                limit = self.employee.administrative.normal_leave_days()
            else:
                limit = 0

            if self.leave.name == 'Κανονική' and limit:
                y = self.date_from.year

                # Οι διοικητικοί έχουν έξτρα 5 μέρες αν πάρουν την άδειά τους από 1/1 έως 14/5
                if hasattr(self.employee, 'administrative'):
                    leaves = list(EmployeeLeave.objects.filter(
                        employee=self.employee, leave=self.leave, date_from__gte=datetime.date(y, 1, 1),
                        date_to__lte=datetime.date(y, 12, 31)
                    ).exclude(id=self.id))
                    dur = sum([l.duration for l in leaves])
                    extra_range = (datetime.date(y, 11, 1), datetime.date(y, 5, 14))
                    extra5 = all([not intersect((l.date_from, l.date_to), extra_range) for l in leaves + [self]])
                    if extra5:
                        limit += 5
                else:
                    dur = EmployeeLeave.objects.filter(
                        employee=self.employee, leave=self.leave, date_from__gte=datetime.date(y, 1, 1),
                        date_to__lte=datetime.date(y, 12, 31)
                    ).exclude(id=self.id).aggregate(Sum('duration'))['duration__sum'] or 0


                msg = 'Οι ημέρες κανονικής άδειας ξεπερνούν τις {0}. Μέρες χωρίς την τρέχουσα άδεια: {1}'
                if dur + self.duration > limit:
                    raise ValidationError(msg.format(limit, dur))

            if len(self.intersects_with()) > 0:
                raise ValidationError('Υπάρχει και άλλη άδεια αυτό διάστημα')

    def intersects_with(self):
        df, dt = [d.strftime('%Y-%m-%d') for d in (self.date_from, self.date_to)]
        return EmployeeLeave.objects.filter(
            Q(employee=self.employee),
            Q(date_from__range=[df, dt]) |
            Q(date_to__range=[df, dt]) |
            Q(date_to__gte=df, date_from__lte=dt)).\
            exclude(id=self.id)

    def split(self):
        """Returns a tuple containing two tuples if the leave spans between two
        years or one if not. The tuple is of the form (year, days).
        Date conversions are made using 360 day year"""
        if self.date_from.year != self.date_to.year:
            end = datetime.date(self.date_from.year, 12, 31)
            start = datetime.date(self.date_to.year, 1, 1)
            s = Date(start)
            e = Date(end)
            df = Date(self.date_from)
            dt = Date(self.date_to)
            d1 = end.year, (e - df).total
            d2 = start.year, (dt - s).total
            return d1, d2
        else:
            return ((self.date_from.year,
                    self.duration if self.duration < 360 else 360,), )

    def __unicode__(self):
        return str(self.employee) + '-' + str(self.date_from)

    
class PermanentLeaveManager(models.Manager):        
    def get_queryset(self):
        ids = Permanent.objects.all().values_list("parent_id", flat=True)
        return super(PermanentLeaveManager, self).get_queryset().filter(employee_id__in=ids)


class PermanentLeave(EmployeeLeave):

    class Meta:
        proxy = True
        verbose_name = 'Άδεια Μόνιμου Εκπαιδευτικού'
        verbose_name_plural = 'Άδειες Μόνιμων Εκπαιδευτικών'

    objects = PermanentLeaveManager()


class NonPermanentLeaveManager(models.Manager):
    def get_queryset(self):
        ids = NonPermanent.objects.all().values_list("parent_id", flat=True)
        return super(NonPermanentLeaveManager, self).get_queryset().filter(employee_id__in=ids)


class NonPermanentLeave(EmployeeLeave):

    class Meta:
        proxy = True
        verbose_name = 'Άδεια Αναπληρωτή Εκπαιδευτικού'
        verbose_name_plural = 'Άδειες Αναπληρωτων Εκπαιδευτικών'

    objects = NonPermanentLeaveManager()


class AdministrativeLeaveManager(models.Manager):
    def get_queryset(self):
        ids = Administrative.objects.all().values_list("parent_id", flat=True)
        return super(AdministrativeLeaveManager, self).get_queryset().filter(employee_id__in=ids)


class AdministrativeLeave(EmployeeLeave):

    class Meta:
        proxy = True
        verbose_name = 'Άδεια Διοικητικού'
        verbose_name_plural = 'Άδειες Διοικητικών'

    objects = AdministrativeLeaveManager()
    
    
class EmployeeResponsibility(models.Model):

    class Meta:
        verbose_name = 'Θέση ευθύνης'
        verbose_name_plural = 'Θέσεις ευθύνης'

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    responsibility = models.ForeignKey(Responsibility, verbose_name='Θέση ευθύνης', on_delete=models.CASCADE)
    date_from = models.DateField('Ημ. Έναρξης')
    date_to = models.DateField('Ημ. Λήξης')
    order = models.CharField('Απόφαση', max_length=200)
    description = models.CharField('Περιγραφή', max_length=300, null=True, blank=True)

    def __unicode__(self):
        return self.date_from.strftime('%d-%m-%Y') + '-' + self.order


class DegreeOrganization(models.Model):

    class Meta:
        verbose_name = 'Φορέας Πιστοποίησης'
        verbose_name_plural = 'Φορείς Πιστοποίησης'

    name = models.CharField('Τίτλος', max_length=200)

    def __unicode__(self):
        return self.name


class EmployeeDegree(models.Model):

    class Meta:
        verbose_name = 'Πτυχία/Προσόντα εκπαιδευτικού'
        verbose_name_plural = 'Πτυχία/Προσόντα εκπαιδευτικών'
        ordering = ['-date']

    name = models.CharField('Τίτλος', max_length=200)  # τιτλος πτυχίου
    degree = models.ForeignKey(DegreeCategory, verbose_name='Κατηγορία', on_delete=models.CASCADE)
    date = models.DateField('Ημερομηνία Λήψης', null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    score = models.CharField('Βαθμός', max_length=20, null=True, blank=True)
    degree_number = models.CharField('Αρ. πιστοποιητικού', max_length=20, null=True, blank=True)
    organization = models.ForeignKey(DegreeOrganization, verbose_name='Φορέας Πιστοποίησης', null=True, on_delete=models.CASCADE)
    checked = models.BooleanField('Ελεγμένο', default=None)
    relevance = models.BooleanField('Συνάφεια', default=None)

    def __unicode__(self):
        return self.name


class Child(models.Model):

    class Meta:
        verbose_name = 'Παιδί'
        verbose_name_plural = 'Παιδιά'

    employee = models.ForeignKey(Employee, verbose_name='Υπάλληλος', on_delete=models.CASCADE)
    first_name = models.CharField('Όνομα Τέκνου', max_length=250, null=True, blank=True)
    date_birth = models.DateField('Ημ. Γέννησης')
    date_university_registration = models.DateField('Ημ. Εγγραφής', null=True, blank=True)
    study_years = models.IntegerField('Έτη σπουδών', null=True, blank=True)
    special_condition = models.CharField('Ειδική κατάσταση', max_length=10, default='no', null=True,
                                         choices=(('no', 'Όχι'),
                                                  ('died', 'Απεβίωσε'),
                                                  ('yes', 'Ναι')))
    is_dependent = models.NullBooleanField('Είναι προστατευόμενο μέλος', null=True, blank=True, default=True)

    def __unicode__(self):
        return "%s %s" % (self.first_name, self.date_birth.strftime('%d-%m-%Y'))


class LoanCategory(models.Model):

    class Meta:
        verbose_name = 'Κατηγορία δανείων'
        verbose_name_plural = 'Κατηγορίες δανείων'

    name = models.CharField('Κατηγορία', max_length=200)

    def __unicode__(self):
        return self.name


class Loan(models.Model):

    class Meta:
        verbose_name = 'Δάνειο'
        verbose_name_plural = 'Δάνεια'

    employee = models.ForeignKey(Employee, verbose_name='Υπάλληλος', on_delete=models.CASCADE)
    category = models.ForeignKey(LoanCategory, verbose_name='Κατηγορία δανείου', on_delete=models.CASCADE)

    installment = models.IntegerField(max_length=4, verbose_name='Δόση δανείου')
    date_start = models.DateField('Ημ. έναρξης')
    date_end = models.DateField('Ημ. λήξης')

    def __unicode__(self):
        return self.date_start.strftime('%d-%m-%Y')


class NonPermanentInsuranceFile(models.Model):

    class Meta:
        verbose_name = 'Aρχείο στοιχείων ασφάλισης'
        verbose_name_plural = 'Αρχεία στοιχείων ασφάλισης'

    id = models.AutoField(primary_key=True)
    xls_file1 = models.FileField('Αρχείο 1ου μήνα', upload_to="xlsfiles")
    xls_file2 = models.FileField('Αρχείο 2ου μήνα', upload_to="xlsfiles")
    xls_file3 = models.FileField('Αρχείο 3ου μήνα', upload_to="xlsfiles")
    description = models.CharField('Περιγραφή', max_length=255)
    status = models.BooleanField('Κατάσταση', blank=True, default=None)

    def __unicode__(self):
        return self.description


@receiver(pre_delete, sender=NonPermanentInsuranceFile)
def xls_file1_delete(sender, instance, **kwargs):
    if instance.xls_file1:
        instance.xls_file1.delete(False)


@receiver(pre_delete, sender=NonPermanentInsuranceFile)
def xls_file2_delete(sender, instance, **kwargs):
    if instance.xls_file2:
        instance.xls_file2.delete(False)


@receiver(pre_delete, sender=NonPermanentInsuranceFile)
def xls_file3_delete(sender, instance, **kwargs):
    if instance.xls_file3:
        instance.xls_file3.delete(False)


class NonPermanentUnemploymentMonth(models.Model):

    class Meta:
        verbose_name = 'Στοιχεία ανεργίας μηνός'
        verbose_name_plural = 'Στοιχεία ανεργίας μηνών'

    insurance_file = models.ForeignKey(NonPermanentInsuranceFile, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    pay_type = models.CharField('Τύπος μισθοδοσίας', max_length=200)
    days_insured = models.IntegerField(max_length=4, verbose_name='Ημέρες ασφάλισης')
    month = models.IntegerField(max_length=4, verbose_name='Μήνας')
    year = models.IntegerField(max_length=4, verbose_name='Έτος')
    insured_from = models.CharField(max_length=50, verbose_name='Ασφάλιση από')
    insured_to = models.CharField(max_length=50, verbose_name='Ασφάλιση μέχρι')
    total_earned = models.CharField("Σύνολο αποδοχών", max_length=50, null=True, blank=True) 
    employee_contributions = models.CharField("Εισφορές εργαζομένου", max_length=50, null=True, blank=True)
    employer_contributions = models.CharField("Εισφορές εργοδότη", max_length=50, null=True, blank=True)
    total_contributions = models.CharField("Σύνολο Εισφορών", max_length=50, null=True, blank=True)

    def __unicode__(self):
        return '%s %s' % (self.month, self.year)


class Settings(models.Model):

    class Meta:
        verbose_name = 'Ρύθμιση'
        verbose_name_plural = 'Ρυθμίσεις'

    name = models.CharField('Πεδίο', max_length=200)
    value = models.CharField('Τιμή', max_length=300)
    internal_name = models.CharField('Όνομα συστήματος', max_length=200, unique=True)

    def __unicode__(self):
        return self.name


class GeoSchool(School):

    class Meta:
        verbose_name = 'Σχολεία - Γεωγραφική Απεικόνιση'
        verbose_name_plural = 'Σχολεία - Γεωγραφική Απεικόνιση'
        proxy = True
        managed = False

class ImportExport(Employee):

    class Meta:
        verbose_name = 'Εισαγωγή - Εξαγωγή Δεδομένων'
        verbose_name_plural = 'Εισαγωγή - Εξαγωγή Δεδομένων'
        proxy = True
        managed = False
