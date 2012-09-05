# -*- coding: utf-8 -*-
import functools
from django.db import models
from django.db.models import Q
from dideman.dide.util.common import (current_year_date_from,
                                      current_year_date_to)
from dideman.dide.decorators import shorted
from django.db.models import Max
import sql
from django.db import connection
from south.modelsinspector import add_introspection_rules
import datetime


class NullableCharField(models.CharField):
    description = 'CharField that obeys null=True'

    def to_python(self, value):
        if isinstance(value, models.CharField):
            return value
        return value or ''

    def get_db_prep_value(self, value, *args, **kwargs):
        return value or None

add_introspection_rules([], ['^dideman\.dide\.models\.NullableCharField'])


class Application(models.Model):

    class Meta:
        verbose_name = u'Αίτηση'
        verbose_name_plural = u'Αιτήσεις'

    employee = models.ForeignKey('Employee',
                                 verbose_name=u'Υπάλληλος')
    choices = models.ManyToManyField('School',
                                     through='ApplicationChoice')
    set = models.ForeignKey('ApplicationSet', verbose_name=u'Ανήκει')
    datetime_finalised = models.DateTimeField(u'Ημερομηνία Οριστικοποίησης',
                                         null=True, blank=True)

    def join_choices(self, sep=','):
        return sep.join([
                choice.choice.name for choice in
                sorted(ApplicationChoice.objects.filter(application=self),
                       key=lambda x: x.position)])

    def finalised(self):
        return bool(self.datetime_finalised)
    finalised.short_description = u'Οριστικοποιήθηκε'

    def profession(self):
        return self.employee.profession
    profession.short_description = u'Ειδικότητα'

    def __unicode__(self):
        return u'%s-%s' % (self.set, self.employee)


class TemporaryPosition(Application):

    class Meta:
        verbose_name = u'Αίτηση προσωρινής τοποθέτησης'
        verbose_name_plural = u'Αιτήσεις προσωρινής τοποθέτησης'

    parent = models.OneToOneField('Application', parent_link=True)
    telephone_number = models.CharField(u'Τηλέφωνο επικοινωνίας',
                                        max_length=20)
    colocation_municipality = models.CharField(u'Δήμος Συνυπηρέτησης',
                                                max_length=200, null=True,
                                                blank=True)
    nativity_municipality = models.CharField(u'Δήμος Εντοπιότητας',
                                              max_length=200, null=True,
                                              blank=True)


class TemporaryPositionAllAreas(TemporaryPosition):

    class Meta:
        verbose_name = u'Αίτηση προσωρινής τοποθέτησης σε όλα τα σχολεία'
        verbose_name_plural = (u'Αίτηση προσωρινής τοποθέτησης σε όλα'
                               u' τα σχολεία')
        proxy = True


HEALTH_CHOICES = (('50-66', u'Αναπηρία 50-66%'),
                  ('67-79', u'Αναπηρία 67-79'),
                  ('80-', u'Αναπηρία 80% και άνω'))


class MoveInside(Application):

    class Meta:
        verbose_name = u'Αίτηση απόσπασης εντός Π.Υ.Σ.Δ.Ε.'
        verbose_name_plural = u'Αιτήσεις απόσπασης εντός Π.Υ.Σ.Δ.Ε.'

    parent = models.OneToOneField('Application', parent_link=True)
    telephone_number = models.CharField(u'Τηλέφωνο επικοινωνίας',
                                        max_length=20)
    colocation_municipality = models.CharField(
        u'Δήμος Συνυπηρέτησης', max_length=200, null=True, blank=True)
    nativity_municipality = models.CharField(
        u'Δήμος Εντοπιότητας', max_length=200, null=True, blank=True)
    married = models.BooleanField(u'Έγγαμος', default=False)
    divorced = models.BooleanField(u'Διαζευγμένος', default=False)
    widowed = models.BooleanField(u'Σε χηρεία', default=False)
    custody = models.BooleanField(u'Επιμέλεια παιδιών', default=False)
    single_parent = models.BooleanField(u'Μονογονεϊκή οικογένεια',
                                        default=False)
    children = models.IntegerField(u'Τέκνα ανήλικα ή σπουδάζοντα',
                                   null=True, blank=True)
    health_self = models.CharField(u'Λόγοι Υγείας', max_length=100,
                                   choices=HEALTH_CHOICES, null=True,
                                   blank=True)
    health_spouse = models.CharField(u'Λόγοι υγεία συζύγου', max_length=100,
                                     choices=HEALTH_CHOICES, null=True,
                                     default=None, blank=True)
    health_children = models.CharField(u'Λόγοι υγείας παιδιών', max_length=100,
                                   choices=HEALTH_CHOICES,  null=True,
                                   default=None, blank=True)
    health_parents = models.CharField(u'Λόγοι υγείας γονέων', max_length=100,
                                      choices=HEALTH_CHOICES,  null=True,
                                      default=None, blank=True)
    parents_place = models.CharField(u'Περιοχή διαμονής γονέων',
                                      max_length=150, null=True, blank=True)
    health_siblings = models.NullBooleanField(
        u'Λόγοι υγείας αδερφών (> 67% με επιμέλεια)', default=False,
        null=True, blank=True)
    siblings_place = models.CharField(u'Περιοχή διαμονής αδερφών',
                                       max_length=150,  null=True, blank=True)
    in_vitro = models.BooleanField(u'Θεραπεία εξωσωματικής γονιμοποίησης',
                                   default=False)
    post_graduate_subject = models.CharField(
        u'Περιοχή μεταπτυχιακών σπουδών (εφόσον υπάρχει)', null=True,
        blank=True, max_length=150)
    special_category = models.CharField(u'Ειδική κατηγορία μετάθεσης',
                                        max_length=150, null=True, blank=True)
    military_spouse = models.NullBooleanField(u'Σύζυγος στρατιωτικού',
                                              null=True, blank=True,
                                              default=False)
    elected = models.BooleanField(u'Αιρετός ΟΤΑ', default=False)
    judge_spouse = models.NullBooleanField(u'Σύζυγος δικαστικού',
                                           default=False, null=True,
                                           blank=True)
    move_primary = models.NullBooleanField(u'Απόσπαση Α\'βάθμια',
                                           default=False, null=True,
                                           blank=True)
    other_reasons = models.CharField(u'Άλλοι λόγοι', null=True, blank=True,
                                     default=None, max_length=500)


class ApplicationType(models.Model):

    class Meta:
        verbose_name = u'Τύπος Αίτησης'
        verbose_name_plural = u'Τύποι αιτήσεων'

    name = models.CharField(u'Όνομα', max_length=100)


class ApplicationChoice(models.Model):

    class Meta:
        verbose_name = u'Επιλογή'
        verbose_name_plural = u'Επιλογές'

    application = models.ForeignKey('Application', verbose_name=u'Αίτηση')
    choice = models.ForeignKey('School', verbose_name=u'Επιλογή')
    position = models.IntegerField(u'Θέση')

    def __unicode__(self):
        return self.choice.name


class ApplicationSet(models.Model):

    class Meta:
        verbose_name = u'Σύνολο Αιτήσεων'
        verbose_name_plural = u'Σύνολα Αιτήσεων'

    name = models.CharField(u'Όνομα', max_length=100)
    title = models.CharField(u'Περιγραφή', max_length=300,
                              null=True, blank=True)

    start_date = models.DateField(u'Ημερομηνία Έναρξης')
    end_date = models.DateField(u'Ημερομηνία Λήξης')
    klass = models.CharField(u'Τύπος', max_length=150, choices=(
            ('TemporaryPosition', u'Προσωρινής Τοποθέτησης'),
            ('MoveInside', u'Απόσπασης εντός Π.Υ.Σ.Δ.Ε.'),
            ('TemporaryPositionAllAreas',
             u'Προσωρινής Τοποθέτησης (όλες περιοχές)')))

    def __unicode__(self):
        return self.name


class TransferAreaManager(models.Manager):

    def get_by_natural_key(self, name):
        return self.get(name__startswith=name)


class TransferArea(models.Model):

    class Meta:
        verbose_name = u'Περιοχή μετάθεσης'
        verbose_name_plural = u'Περιοχές μετάθεσης'

    objects = TransferAreaManager()

    name = models.CharField(max_length=100)

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

    name = models.CharField(u'Όνομα', max_length=100)
    belongs = models.BooleanField(
         u'Ανήκει στην Δ.Δ.Ε. Δωδεκανήσου',
         default=True)

    def natural_key(self):
        return (self.name, )

    def __unicode__(self):
        return self.name


class PlacementTypeManager(models.Manager):

    def get_by_natural_key(self, name):
        return self.get(name=name)


class PlacementType(models.Model):

    class Meta:
        verbose_name = u'Τύπος τοποθέτησης'
        verbose_name_plural = u'Τύποι τοποθέτησης'

    objects = PlacementTypeManager()

    name = models.CharField(max_length=100, verbose_name=u'Τύπος')

    def natural_key(self):
        return (self.name, )

    def __unicode__(self):
        return self.name


class LeaveManager(models.Manager):

    def get_by_natural_key(self, name):
        return self.get(name=name)


LEAVE_TYPES = ((u'Κανονική', u'Κανονική'),
               (u'Αναρρωτική', u'Αναρρωτική'),
               (u'Ειδική', u'Ειδική'))


class Leave(models.Model):

    class Meta:
        verbose_name = u'Κατηγορία άδειας'
        verbose_name_plural = u'Κατηγορίες αδειών'

    objects = LeaveManager()

    name = models.CharField(max_length=200, verbose_name=u'Κατηγορία')
    type = models.CharField(max_length=15, verbose_name=u'Τύπος',
                            choices=LEAVE_TYPES)
    not_paying = models.BooleanField(verbose_name=u'Χωρίς αποδοχές')
    only_working_days = models.BooleanField(
         verbose_name=u'Μόνο εργάσιμες μέρες')
    orders = models.CharField(u'Διατάξεις', null=True, blank=True,
                              max_length=300)
    description = models.CharField(null=True, blank=True,
                                   verbose_name=u'Περιγραφή',
                                   max_length=300)

    def __unicode__(self):
        return self.name

    def natural_key(self):
        return (self.name, )


class Responsibility(models.Model):

    class Meta:
        verbose_name = u'Κατηγορία θέσης ευθύνης'
        verbose_name_plural = 'Κατηγορίες θέσεων ευθύνης'

    hours = models.IntegerField(max_length=2,
                                verbose_name=u'Ώρες μείωσης')
    name = models.CharField(max_length=200,
                            verbose_name=u'Θέση ευθύνης')

    def __unicode__(self):
        return self.name


class Profession(models.Model):

    class Meta:
        verbose_name = u'Ειδικότητα'
        verbose_name_plural = u'Ειδικότητες'
        ordering = ['id']

    id = models.CharField(u'Ειδικότητα', max_length=100,
                          primary_key=True)  # ΠΕ04.01 ΠΕ19.02 κτλ
    description = models.CharField(u'Λεκτικό', max_length=200,
                                   null=True)
    unified_profession = models.CharField(u'Κλάδος',
                                          max_length=100)  # ΠΕ04...

    def __unicode__(self):
        return self.id


class DegreeCategory(models.Model):

    class Meta:
        verbose_name = u'Κατηγορία πτυχίου'
        verbose_name_plural = u'Κατηγορίες πτυχίων'

    # πτυχίο, μεταπτυχιακό, διδακτορικό, τπε κτλ
    name = models.CharField(u'Τύπος', max_length=100)

    def __unicode__(self):
        return self.name


class EmployeeManager(models.Manager):

    def get_by_natural_key(self, firstname, lastname, fathername, profession):
        return self.get(firstname=firstname, lastname=lastname,
                        fathername=fathername, profession=profession)


class Employee(models.Model):

    class Meta:
        verbose_name = u'Εκπαιδευτικός'
        verbose_name_plural = u'Εκπαιδευτικοί'
        ordering = ['lastname']

    objects = EmployeeManager()

    firstname = models.CharField(u'Όνομα', max_length=100)
    lastname = models.CharField(u'Επώνυμο', max_length=100)
    fathername = models.CharField(u'Όνομα Πατέρα', max_length=100)
    mothername = models.CharField(u'Όνομα μητέρας', max_length=100,
                                  null=True, blank=True)
    date_start = models.DateField(u'Ημερομηνία έναρξης υπηρεσίας',
                                  null=True, blank=True)
    date_end = models.DateField(u'Ημερομηνία λήξης υπηρεσίας',
                                null=True, blank=True)
    currently_serves = models.BooleanField(u'Υπηρετεί στην Δ.Δ.Ε. Δωδεκανήσου',
                                           default=True)
    address = models.CharField(u'Διεύθυνση', max_length=200, null=True,
                               blank=True)
    identity_number = NullableCharField(u'Αρ. Δελτίου Ταυτότητας',
                                        max_length=8, null=True,
                                        unique=True, blank=True)
    transfer_area = models.ForeignKey(TransferArea,
                                      verbose_name=u'Περιοχή Μετάθεσης',
                                      null=True, blank=True)
    recognised_experience = models.CharField(
         u'Αναγνωρισμένη προυπηρεσία (ΕΕΜΜΗΜΗΜ)', null=True, blank=True,
         default='000000', max_length=8)
    vat_number = NullableCharField(u'Α.Φ.Μ.', max_length=9, null=True,
                                   unique=True, blank=True)
    tax_office = models.CharField(u'Δ.Ο.Υ.', max_length=100, null=True,
                                  blank=True)
    bank = models.CharField(u'Τράπεζα', max_length=100, null=True, blank=True)
    bank_account_number = models.CharField(u'Αριθμός λογαριασμού τράπεζας',
                                           max_length=100, null=True,
                                           blank=True)
    iban = models.CharField(u'IBAN', max_length=27, null=True, blank=True)
    telephone_number1 = models.CharField(u'Αρ. Τηλεφώνου 1', max_length=14,
                                         null=True, blank=True)
    telephone_number2 = models.CharField(u'Αρ. Τηλεφώνου 2', max_length=14,
                                         null=True, blank=True)
    social_security_registration_number = models.CharField('Α.Μ.Κ.Α.',
                                                           max_length=11,
                                                           null=True,
                                                           blank=True)
    before_93 = models.BooleanField(u'Ασφαλισμένος πριν το 93', default=False)
    has_family_subsidy = models.BooleanField(u'Οικογενειακό επίδομα',
                                             default=False)
    other_social_security = models.ForeignKey(
        u'SocialSecurity', verbose_name=u'Άλλο ταμείο ασφάλισης',
        null=True, blank=True)
    organization_paying = models.ForeignKey(
        Organization, verbose_name=u'Οργανισμός μισθοδοσίας',
        related_name='organization_paying',
        null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    birth_date = models.DateField(u'Ημερομηνία Γέννησης',
                                  null=True, blank=True)
    hours_current = models.IntegerField(u'Τρέχων Ωράριο', max_length=2,
                                        null=True, blank=True)
    profession = models.ForeignKey(Profession, verbose_name=u'Ειδικότητα',
                                   related_name='employees')
    placements = models.ManyToManyField(Organization, through='Placement',
                                        verbose_name=u'Σχολείο/Φορέας')
    leaves = models.ManyToManyField(Leave, through='EmployeeLeave')
    extra_professions = models.ManyToManyField(Profession,
                                               through='EmployeeProfession')
    responsibilities = models.ManyToManyField(Responsibility,
                                              through='EmployeeResponsibility')
    studies = models.ManyToManyField(DegreeCategory,
                                     through='EmployeeDegree')
    study_years = models.IntegerField(
        u'Έτη φοίτησης', max_length=1, null=True, blank=True,
        choices=[(x, str(x)) for x in range(2, 7)])
    notes = models.TextField(u'Σημειώσεις', blank=True, default='')
    date_created = models.DateField(u'Ημερομηνία δημιουργίας',
                                    auto_now_add=True)

    def last_placement(self):
        p = Placement.objects.filter(employee=self).order_by('-date_from')
        return p[0] if p else None

    def current_year_placements(self):
        return Placement.objects.filter(
            employee=self, date_from__gte=current_year_date_from())

    def unified_profession(self):
        return self.profession.unified_profession

    def temporary_position(self):
        if self.has_permanent_post:
            return None
        else:
            p = Placement.objects.filter(employee=self,
                                         date_from__gte=current_year_date_from,
                                         type__id=3).order_by('-date_from')
            return p[0] if p else None
    temporary_position.short_description = u'Προσωρινή Τοποθέτηση'

    def organization_serving(self):
        p = Placement.objects.filter(employee=self).order_by('-date_from')
        this_years = p.filter(date_from__gte=current_year_date_from()). \
            order_by('-date_from')
        if this_years:
            return this_years[0]
        else:
            valid = p.filter(date_to__gte=datetime.date.today()). \
                order_by('-date_from')
            if valid:
                return valid[0]
            return None
    organization_serving.short_description = u'Θέση υπηρεσίας'

    def natural_key(self):
        return (self.firstname, self.lastname, self.fathername,
                self.profession)

    def formatted_recognised_experience(self):
        return u'%s έτη %s μήνες %s μέρες' % (self.recognised_experience[:2],
                                              self.recognised_experience[2:4],
                                             self.recognised_experience[4:6])
    formatted_recognised_experience.short_description = \
        u'Μορφοποιημένη προϋπηρεσία'

    def total_experience(self):
        ryears = int(self.recognised_experience[:2])
        rmonths = int(self.recognised_experience[2:4])
        rdays = int(self.recognised_experience[4:6])
        now = datetime.datetime.now()
        dyears = now.year - self.date_hired.year
        dmonths = now.month - self.date_hired.month
        ddays = now.day - self.date_hired.day + 1
        if ddays < 0:
            ddays += 30
            dmonths -= 1
        if dmonths < 0:
            dmonths += 12
            dyears -= 1
        days = ddays + rdays
        months = rmonths + dmonths
        years = ryears + dyears
        if days > 30:
            days -= 30
            months += 1
        if months > 12:
            months -= 12
            years += 1
        return u'%d έτη %d μήνες %d μέρες' % (years, months, days)

    def profession_description(self):
        return self.profession.description
    profession_description.short_description = u'Λεκτικό ειδικότητας'

    def __unicode__(self):
        return u'%s %s (%s)' % (self.lastname, self.firstname, self.fathername)


class SocialSecurity(models.Model):

    class Meta:
        verbose_name = u'Ταμείο ασφάλισης'
        verbose_name_plural = u'Ταμεία ασφάλισης'

    name = models.CharField(u'Όνομα', max_length=100)

    def __unicode__(self):
        return self.name


class PermanentManager(EmployeeManager):

    def match(self, registration_number, lastname):
        try:
            return self.get(registration_number=registration_number,
                            lastname=lastname)
        except:
            return None

    def get_by_natural_key(self, registration_number):
        return self.get(registration_number=registration_number)

    def serves_in_dide_school(self):
        cursor = connection.cursor()
        cursor.execute(
            sql.serves_in_dide_school.format(str(current_year_date_from())))
        ids = [row[0] for row in cursor.fetchall()]
        return self.filter(parent_id__in=ids)

    def not_serves_in_dide_school(self):
        cursor = connection.cursor()
        cursor.execute(
            sql.serves_in_dide_school.format(
                str(current_year_date_from()),
                str(current_year_date_to())))
        ids = [row[0] for row in cursor.fetchall()]
        return self.exclude(parent_id__in=ids)

    def permanent_post_in_organization(self, org_id):
        cursor = connection.cursor()
        cursor.execute(sql.permanent_post_in_organization.format(org_id))
        ids = [row[0] for row in cursor.fetchall()]
        return self.filter(parent_id__in=ids)

    def serving_in_organization(self, org_id):
        cursor = connection.cursor()
        cursor.execute(
            sql.serving_in_organization.format(org_id,
                                               str(current_year_date_from()),
                                               str(current_year_date_to())))
        ids = [row[0] for row in cursor.fetchall()]
        return self.filter(parent_id__in=ids)

    def have_degree(self, degree_id):
        degree = DegreeCategory.objects.get(pk=degree_id)
        qs = EmployeeDegree.objects.filter(degree=degree)
        ids = [d.employee_id for d in qs]
        return self.filter(parent_id__in=ids)

    def transfered(self):
        ids = [p.employee.id for p in Placement.objects.only('employee')
               .filter(type__name=u'Μετάθεση')]
        return self.filter(pk__in=ids)

    def not_transfered(self):
        ids = [p.employee.id for p in Placement.objects.only('employee')
               .filter(type__name=u'Μετάθεση')]
        return self.all().exclude(pk__in=ids)

    def next_promotion_in_range(self, date_from, date_to):
        return Permanent.objects.filter(
            id__in=[o['employee']
                    for o in [p for p in Promotion.objects
                              .all()
                              .values('employee')
                              .annotate(
                        next_promotion_date=Max('next_promotion_date'))
                              .filter(next_promotion_date__gte=date_from,
                                      next_promotion_date__lte=date_to)]])


class Permanent(Employee):

    class Meta:
        verbose_name = u'Μόνιμος Εκπαιδευτικός'
        verbose_name_plural = u'Μόνιμοι Εκπαιδευτικοί'

    objects = PermanentManager()

    parent = models.OneToOneField(Employee, parent_link=True)
    serving_type = models.ForeignKey(PlacementType,
                                     verbose_name=u'Είδος Υπηρέτησης')
    date_hired = models.DateField(u'Ημερομηνία διορισμού', null=True,
                                  blank=True)
    order_hired = models.CharField(u'Φ.Ε.Κ. διορισμού', max_length=200,
                                   null=True, blank=True)
    registration_number = NullableCharField(u'Αρ. Μητρώου', max_length=6,
                                            unique=True, null=True, blank=True)
    inaccessible_school = models.ForeignKey(
        'School', verbose_name=u'Δυσπρόσιτος στο σχολείο', null=True,
        blank=True)
    payment_start_date_manual = models.DateField(
         u'Μισθολογική αφετηρία (μετά από άδεια)', null=True, blank=True)
    hours = models.IntegerField(u'Υποχρεωτικό Ωράριο', max_length=2, null=True,
                                blank=True)
    is_permanent = models.BooleanField(u'Έχει μονιμοποιηθεί', null=False,
                                       blank=False, default=False)
    has_permanent_post = models.BooleanField(u'Έχει οργανική θέση',
                                             null=False, blank=False,
                                             default=False)

    def natural_key(self):
        return (self.registration_number, )

    def promotions(self):
        return self.promotion_set.all()

    def permanent_post(self):
        permanent_posts = Placement.objects.filter(
             employee=self, type__name=u'Οργανική').order_by('-date_from')
        return permanent_posts[0] if permanent_posts else '-'
    permanent_post.short_description = u'Οργανική θέση'

    def current_year_services(self):
        return Placement.objects.filter(employee=self,
                                        type__name__in=[u'Μερική Διάθεση',
                                                        u'Ολική Διάθεση'],
                                        date_from__gte=current_year_date_from()
                                        ).order_by('-date_from')

    def payment_start_date_auto(self):
        days = self.date_hired.day - int(self.recognised_experience[4:])
        months = self.date_hired.month - int(self.recognised_experience[2:4])
        years = self.date_hired.year - int(self.recognised_experience[:2])
        if days <= 0:
            days = 30 + days
            months -= 1
        if months <= 0:
            months = 12 + months
            years -= 1
        return '%s-%s-%s' % (days, months, years)
    payment_start_date_auto.short_description = \
        u'Μισθολογική αφετηρία (αυτόματη)'

    def organization_serving(self):
        return super(Permanent, self).organization_serving() or \
            self.permanent_post()
    organization_serving.short_description = u'Θέση υπηρεσίας'

    def rank(self):
        r = Promotion.objects.filter(employee=self).order_by('-date')
        return r[0] if r else None
    rank.short_description = u'Βαθμός'

    def __unicode__(self):
        return '%s %s  (%s)' % (self.lastname, self.firstname,
                                 self.registration_number)


PROMOTION_CHOICES = [(x, x) for x in [u'ΣΤ', u'Ε4', u'Ε3', u'Ε2', u'Ε1',
                                      u'Ε0', u'Δ4', u'Δ3', u'Δ2', u'Δ1',
                                      u'Δ0', u'Γ4', u'Γ3', u'Γ2', u'Γ1',
                                      u'Γ0', u'Β7', u'Β6', u'Β5', u'Β4',
                                      u'Β3', u'Β2', u'Β1', u'Β0', u'Α5',
                                      u'Α4', u'Α3', u'Α2', u'Α1', u'Α0']]


class Promotion(models.Model):

    class Meta:
        verbose_name = u'Μεταβολή'
        verbose_name_plural = u'Μεταβολές'

    value = models.CharField(u'Μεταβολή', max_length=100,
                             choices=PROMOTION_CHOICES)
    employee = models.ForeignKey(Permanent)
    date = models.DateField(u'Ημερομηνία μεταβολής')
    next_promotion_date = models.DateField(u'Ημερομηνία επόμενης μεταβολής',
                                           null=True, blank=True)
    order = models.CharField(u'Απόφαση', max_length=300)
    order_pysde = models.CharField(u'Απόφαση Π.Υ.Σ.Δ.Ε.', max_length=300,
                                   null=True, blank=True)

    def __unicode__(self):
        return self.value


class NonPermanentTypeManager(models.Manager):

    def get_by_natural_key(self, name):
        return self.get(name=name)


class NonPermanentType(models.Model):

    class Meta:
        verbose_name = u'Κατηγορία μη-μόνιμης απασχόλησης'
        verbose_name_plural = u'Κατηγορίες μη-μόνιμης απασχόλησης'

    objects = NonPermanentTypeManager()

    name = models.CharField(max_length=200, verbose_name=u'Κατηγορία')

    def natural_key(self):
        return (self.name, )

    def __unicode__(self):
        return self.name


class NonPermanent(Employee):

    class Meta:
        verbose_name = u'Αναπληρωτής/Ωρομίσθιος'
        verbose_name_plural = u'Αναπληρωτές/Ωρομίσθμιοι'

    parent = models.OneToOneField(Employee, parent_link=True)
    type = models.ForeignKey(NonPermanentType,
                             verbose_name=u'Σχέση απασχόλησης')
    pedagogical_sufficiency = models.BooleanField(u'Παιδαγωγική κατάρτιση',
                                                  default=False)
    order_ministry = models.CharField(u'Απόφαση υπουργείου', max_length=300,
                                      null=True, blank=True)
    order_council = models.CharField(u'Πράξη Π.Υ.Σ.Δ.Ε.', max_length=300,
                                     null=True, blank=True)
    order_start_manager = models.CharField(u'Απόφαση έναρξης διευθυντή',
                                           max_length=300, null=True,
                                           blank=True)
    order_end_manager = models.CharField(u'Απόφαση απόλυσης διευθυντή',
                                         max_length=300, null=True, blank=True)
    social_security_number = models.CharField(u'Αριθμός Ι.Κ.Α.', max_length=10,
                                              null=True, blank=True)


class EmployeeProfession(models.Model):

    class Meta:
        verbose_name = u'Επιπλέον ειδικότητα εκπαιδευτικού'
        verbose_name_plural = u'Επιπλέον ειδικότητες εκπαιδευτικών'

    employee = models.ForeignKey(Employee)
    profession = models.ForeignKey(Profession)


class SchoolTypeManager(models.Manager):

    def get_by_natural_key(self, name):
        return self.get(name=name)


class SchoolType(models.Model):

    class Meta:
        verbose_name = u'Κατηγορία σχολείου'
        verbose_name_plural = u'Κατηγορίες σχολείων'

    objects = SchoolTypeManager()

    name = models.CharField(max_length=100,
                            verbose_name=u'Πλήρες αναγνωριστικό')
    shift = models.CharField(max_length=100, verbose_name=u'Ωράριο',
                             choices=(('day', u'Ημερήσιο'),
                                      ('night', u'Εσπερινό'),
                                      ('other', u'Άλλο')))
    category = models.CharField(max_length=100, verbose_name=u'Κατηγορία',
                                choices=(('gym', u'Γυμνάσιο'),
                                         ('lyk', u'Γενικό Λύκειο'),
                                         ('epag', u'Επαγγελματική Εκπαίδευση'),
                                         ('other', u'Άλλο')))
    # < 20 : Γυμνάσια, > 10 : Μεταγυμνασιακά
    rank = models.IntegerField(max_length=2, verbose_name=u'Βαθμίδα',
                               choices=((10, u'Γυμνάσιο'),
                                        (20, u'ΜεταΓυμνασιακό'),
                                        (15, u'Γυμνάσιο/Λ.Τ.')))

    def natural_key(self):
        return (self.name, )

    def __unicode__(self):
        return self.name


class SchoolManager(models.Manager):

    def get_by_natural_key(self, code):
        return self.get(code=code)


class School(Organization):

    class Meta:
        verbose_name = u'Σχολείο'
        verbose_name_plural = u'Σχολεία'
        ordering = ['name']

    objects = SchoolManager()

    parent_organization = models.OneToOneField(Organization, parent_link=True)
    transfer_area = models.ForeignKey(TransferArea,
                                      verbose_name=u'Περιοχή Μετάθεσης')
    points = models.IntegerField(u'Μόρια', max_length=2, null=True, blank=True)
    code = models.IntegerField(u'Κωδικός Σχολείου', max_length=5, unique=True)
    # γενικό λύκειο, γυμνάσιο, επαλ...
    type = models.ForeignKey(SchoolType, verbose_name=u'Κατηγορία')
    inaccessible = models.BooleanField(u'Δυσπρόσιτο', default=False)
    address = models.CharField(u'Διεύθυνση', max_length=200, null=True,
                               blank=True)
    post_code = models.CharField(u'Τ.Κ.', max_length=5, null=True, blank=True)
    telephone_number = models.CharField(u'Αρ. Τηλεφώνου', max_length=14,
                                        null=True, blank=True)
    fax_number = models.CharField(u'Αρ. Fax', max_length=14, null=True,
                                  blank=True)
    email = models.EmailField(null=True, blank=True)
    manager = models.ForeignKey(Permanent, null=True, blank=True,
                                verbose_name=u'Διευθυντής')

    def natural_key(self):
        return (self.code, )


class GymLyc(School):

    class Meta:
        verbose_name = u'Γυμνάσιο-Λ.Τ.'
        verbose_name_plural = u'Γυμνάσια-Λ.Τ.'

    parent_school = models.OneToOneField(School, parent_link=True)
    gymlyc_code = models.IntegerField(u'Κωδικός Λυκειακών τάξεων',
                                      max_length=5, unique=True)


class OtherOrganization(Organization):

    class Meta:
        verbose_name = u'Άλλος φορέας'
        verbose_name_plural = u'Άλλοι φορείς'
        ordering = ['name']

    parent_organization = models.OneToOneField(Organization, parent_link=True)
    description = models.CharField(max_length=300, null=True, blank=True,
                                   verbose_name=u'Περιγραφή')

# PLACEMENT_TYPES = ((1, 'Οργανική'), (2, 'Απόσπαση'),
#    (3, 'Διάθεση'), (4, 'Προσωρινή τοποθέτηση'))


class Placement(models.Model):

    class Meta:
        verbose_name = u'Τοποθέτηση'
        verbose_name_plural = u'Τοποθετήσεις'
        ordering = ['-date_from']

    employee = models.ForeignKey(Employee)
    organization = models.ForeignKey(Organization,
                                     verbose_name=u'Σχολείο/Φορέας')
    date_from = models.DateField(u'Ημερομηνία Έναρξης')
    date_to = models.DateField(u'Ημερομηνία Λήξης', null=True, blank=True)
    type = models.ForeignKey(PlacementType, verbose_name=u'Είδος τοποθέτησης',
                             default=1)
    order = models.CharField(u'Απόφαση', max_length=300, null=True, blank=True,
                             default=None)
    order_pysde = models.CharField(u'Απόφαση Π.Υ.Σ.Δ.Ε.', max_length=300,
                                   null=True, blank=True)

    def natural_key(self):
        return (self.employee, self.organization, self.date_from)

    def __unicode__(self):
        return self.organization.name


class Service(Placement):

    class Meta:
        verbose_name = u'Διάθεση'
        verbose_name_plural = u'Διαθέσεις'
        ordering = ['-date_from']

    parent = models.OneToOneField(Placement, parent_link=True)
    order_manager = models.CharField(u'Απόφαση Διευθυντή', max_length=300,
                                     null=True, blank=True, default=None)
    hours = models.IntegerField(u'Ώρες μείωσης', max_length=2, null=True,
                                blank=True)
    hours_overtime = models.IntegerField(u'Ώρες Υπερωρίας', max_length=2,
                                         null=True, blank=True, default=0)

    def __unicode__(self):
        return self.organization.name + self.date_from.strftime('%d-%m-%Y')


class EmployeeLeaveManager(models.Manager):

    def date_range_intersect(self, ds, de):
        return self.filter(Q(date_from__gte=ds, date_from__lte=de) |
                    Q(date_from__lte=ds, date_to__gte=ds))


class EmployeeLeave(models.Model):

    class Meta:
        verbose_name = u'Άδεια'
        verbose_name_plural = u'Άδειες'
        ordering = ['-date_to']

    objects = EmployeeLeaveManager()
    employee = models.ForeignKey(Employee, verbose_name=u'Υπάλληλος')
    leave = models.ForeignKey(Leave, verbose_name=u'Κατηγορία Άδειας')
    date_issued = models.DateField(u'Χορήγηση', null=True, blank=True)
    date_from = models.DateField(u'Έναρξη', null=True, blank=True)
    date_to = models.DateField(u'Λήξη', null=True, blank=True)
    order = models.CharField(u'Απόφαση', max_length=300, null=True, blank=True)
    authority = models.CharField(u'Αρχή έγκρισης', max_length=200, null=True,
                                 blank=True)
    protocol_number = models.CharField(u'Αρ. πρωτ.', max_length=10, null=True,
                                       blank=True)
    description = models.CharField(u'Σημειώσεις', null=True, blank=True,
                                   max_length=300)
    duration = models.IntegerField(max_length=3, verbose_name=u'Διάρκεια',
                                   null=True, blank=True)

    @shorted(15)
    def category(self):
        return self.leave.name
    category.short_description = u'Κατηγορία'

    def permanent_post(self):
        if hasattr(self.employee, 'permanent'):
            return self.employee.permanent.permanent_post()
        else:
            return None
    permanent_post.short_description = u'Οργανική θέση'

    def organization_serving(self):
        if hasattr(self.employee, 'permanent'):
            return self.employee.permanent.organization_serving()
        else:
            return self.employee.organization_serving()
    organization_serving.short_description = u'Θέση υπηρεσίας'
    # a leave intersects with another date range (ds: date start, de: date end)

    def date_range_intersects(ds, de):
        return (self.date_from <= ds <= self.date_to) or \
            (ds <= self.date_from <= de)

    def profession(self):
        return self.employee.profession
    profession.short_description = u'Ειδικότητα'

    def __unicode__(self):
        return unicode(self.employee) + '-' + unicode(self.date_from)


class EmployeeResponsibility(models.Model):

    class Meta:
        verbose_name = u'Θέση ευθύνης'
        verbose_name_plural = u'Θέσεις ευθύνης'

    employee = models.ForeignKey(Employee)
    responsibility = models.ForeignKey(Responsibility,
                                       verbose_name=u'Θέση ευθύνης')
    date_from = models.DateField(u'Ημ. Έναρξης')
    date_to = models.DateField(u'Ημ. Λήξης')
    order = models.CharField(max_length=200)
    description = models.CharField(max_length=300, null=True, blank=True)

    def __unicode__(self):
        return self.date_from.strftime('%d-%m-%Y') + '-' + self.order


class EmployeeDegree(models.Model):

    class Meta:
        verbose_name = u'Πτυχία/Προσόντα εκπαιδευτικού'
        verbose_name_plural = u'Πτυχία/Προσόντα εκπαιδευτικών'

    name = models.CharField(u'Τίτλος', max_length=200)  # τιτλος πτυχίου
    degree = models.ForeignKey(DegreeCategory, verbose_name=u'Κατηγορία')
    date = models.DateField(u'Ημερομηνία Λήψης', null=True, blank=True)
    employee = models.ForeignKey(Employee)

    def __unicode__(self):
        return self.name


class Child(models.Model):

    class Meta:
        verbose_name = u'Παιδί'
        verbose_name_plural = u'Παιδιά'

    employee = models.ForeignKey(Employee, verbose_name=u'Υπάλληλος')
    date_birth = models.DateField(u'Ημ. Γέννησης')
    date_university_registration = models.DateField(u'Ημ. Εγγραφής',
                                                    null=True, blank=True)
    study_years = models.IntegerField(u'Έτη σπουδών', null=True, blank=True)
    special_condition = models.CharField(u'Ειδική κατάσταση', max_length=10,
                                         default='no', null=True,
                                         choices=(('no', u'Όχι'),
                                                  ('died', u'Απεβίωσε'),
                                                  ('yes', u'Ναι')))

    def __unicode(self):
        return self.date_birth.strftime('%d-%m-%Y')


class LoanCategory(models.Model):

    class Meta:
        verbose_name = u'Κατηγορία δανείων'
        verbose_name_plural = u'Κατηγορίες δανείων'

    name = models.CharField(u'Κατηγορία', max_length=200)

    def __unicode__(self):
        return self.name


class Loan(models.Model):

    class Meta:
        verbose_name = u'Δάνειο'
        verbose_name_plural = u'Δάνεια'

    employee = models.ForeignKey(Employee, verbose_name=u'Υπάλληλος')
    category = models.ForeignKey(LoanCategory,
                                 verbose_name=u'Κατηγορία δανείου')

    installment = models.IntegerField(max_length=4,
                                      verbose_name=u'Δόση δανείου')
    date_start = models.DateField(u'Ημ. έναρξης')
    date_end = models.DateField(u'Ημ. λήξης')

    def __unicode__(self):
        return self.date_start.strftime('%d-%m-%Y')


class Settings(models.Model):

    class Meta:
        verbose_name = u'Ρύθμιση'
        verbose_name_plural = u'Ρυθμίσεις'

    name = models.CharField(u'Πεδίο', max_length=200)
    value = models.CharField(u'Τιμή', max_length=300)
    internal_name = models.CharField(u'Όνομα συστήματος', max_length=200,
                                     unique=True)

    def __unicode__(self):
        return self.name
