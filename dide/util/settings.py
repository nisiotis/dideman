import sys
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
