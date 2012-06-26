from django.db import models
import dideman.dide.models as dide_models


class Application(models.Model):

    class Meta:
        abstract = True
        verbose_name = u'Αίτηση'
        verbose_name_plural = u'Αιτήσεις'

    employee = models.ForeignKey(dide_models.Employee,
                                 verbose_name=u'Υπάλληλος')
    choices = models.ManyToManyField(dide_models.School,
                                     through='ApplicationChoices')
    set = models.ForeignKey('ApplicationSet', verbose_name=u'Ανήκει')
    date_finished = models.DateTimeField(u'Ημερομηνία Οριστικοποίησης',
                                         null=True)

    def finished(self):
        return bool(self.date_finished)
    finished.short_description = u'Οριστικοποιήθηκε'

    def __unicode__(self):
        return '%s-%s' % (self.name, self.employee)


class TemporaryPositionApplication(Application):

    class Meta:
        verbose_name = u'Αίτηση προσωρινής τοποθέτησης'
        verbose_name_plural = u'Αιτήσεις προσωρινής τοποθέτησης'

    colocation_municipality = models.CharField(u'Δήμος Συνυπηρέτησης',
                                               max_length=200)
    nativity_municipality = models.CharField(u'Δήμος Εντοπιότητας',
                                             max_length=200)


class ApplicationType(models.Model):

    class Meta:
        verbose_name = u'Τύπος Αίτησης'
        verbose_name_plural = u'Τύποι αιτήσεων'

    name = models.CharField(u'Όνομα', max_length=100)


class ApplicationChoices(models.Model):

    class Meta:
        verbose_name = u'Επιλογή'
        verbose_name_plural = u'Επιλογές'

    application = models.ForeignKey(Application, verbose_name=u'Αίτηση')
    choice = models.ForeignKey(dide_models.School, verbose_name=u'Επιλογή')


class ApplicationSet(models.Model):

    class Meta:
        verbose_name = u'Σύνολο Αιτήσεων'
        verbose_name_plural = u'Σύνολα Αιτήσεων'

    name = models.CharField(u'Όνομα', max_length=100)
    title = models.CharField(u'Περιγραφή', max_length=300)

    start_date = models.DateField(u'Ημερομηνία Έναρξης')
    end_date = models.DateField(u'Ημερομηνία Λήξης')
    klass = models.CharField(u'Τύπος', max_length=150)
