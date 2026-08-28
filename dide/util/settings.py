import sys

from django.utils.functional import lazy

from dideman.dide.models import Settings


class DideSettings(object):
    _settings = {}
    _descriptions = {}

    @classmethod
    def _get_from_db(cls):
        l = Settings.objects.all()
        for s in l:
            DideSettings._settings[s.internal_name] = s.value
            DideSettings._descriptions[s.internal_name] = s

    def __getitem__(self, key):
        if not DideSettings._settings:
            DideSettings._get_from_db()
        return DideSettings._settings.get(key, None)

    def __setitem__(self, key, value):
        DideSettings._settings[key] = value

    def get_desc(self, key):
        if not DideSettings._settings:
            DideSettings._get_from_db()
        return DideSettings._descriptions.get(key, None)

current_module = sys.modules[__name__]

if not hasattr(current_module, 'SETTINGS'):
    setattr(current_module, 'SETTINGS', DideSettings())


# Τα reports δημιουργούνται σε import time, οπότε δεν μπορούν να διαβάσουν
# τιμές από τη βάση εκείνη τη στιγμή: το ερώτημα θα εκτελούνταν πριν καν
# υπάρξουν οι πίνακες και θα έσπαγε κάθε manage.py εντολή. Το lazy_setting
# επιστρέφει proxy που διαβάζει τη ρύθμιση την πρώτη φορά που θα
# χρησιμοποιηθεί ως συμβολοσειρά.
lazy_setting = lazy(lambda key: SETTINGS[key] or '', str)
