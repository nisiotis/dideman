# Django settings for dideman project.
import importlib.util
import os
import dideman.secret_settings as secret_settings
DEBUG = True
ADMINS = (
     ('ICT Department', 'ictdep@dide.dod.sch.gr'),
)
ALLOWED_HOSTS = ['its.dod.sch.gr','its.dide.dod.sch.gr','10.103.254.11', '81.186.76.92']

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        # database name
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        # empty string for localhost
        'HOST': '',
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

#CACHES = {
#    'default': {
#        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
#        'LOCATION': '127.0.0.1:11211',
#        'JOHNNY_CACHE': True,
#    }
#}


#JOHNNY_MIDDLEWARE_KEY_PREFIX='jc_dideman'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Athens'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'el-gr'
# not a default setting!
#locale.setlocale(locale.LC_ALL, 'el_GR.utf8')


SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Ο κώδικας χρησιμοποιεί παντού naive datetimes. Το Django >= 5 έχει default
# USE_TZ = True, που θα άλλαζε σιωπηλά τη σημασία κάθε αποθηκευμένης ώρας.
USE_TZ = False

# Τα μοντέλα βασίζονται σε implicit AutoField primary keys. Χωρίς αυτό, το
# Django 5 θα ζητούσε migration για BigAutoField.
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), 'media'))

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), 'static'))

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
#ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.realpath(os.path.join(os.path.dirname(__file__), 'global')),
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = ''

# Το TEMPLATE_DIRS / TEMPLATE_LOADERS / TEMPLATE_CONTEXT_PROCESSORS
# αντικαταστάθηκαν από το ενιαίο TEMPLATES. Οι context processors που
# δηλώνονται εδώ είναι όσοι χρησιμοποιούσε σιωπηρά το παλιό default και
# χρειάζεται το admin (request, auth, messages).
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(os.path.dirname(__file__), 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
                'django.template.context_processors.media',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    #'johnny.middleware.LocalStoreClearMiddleware',
    #'johnny.middleware.QueryCacheMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
)

ROOT_URLCONF = 'dideman.urls'

INSTALLED_APPS = (

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
#    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'dideman.dide',
    'dideman.api',
    'dideman.private_teachers',
    'dideman.stats',
)

# Το admin_interface (με το colorfield) είναι προαιρετικό θέμα και πρέπει να
# προηγείται του django.contrib.admin. Δηλώνεται μόνο αν είναι εγκατεστημένο,
# ώστε το project να σηκώνεται και χωρίς αυτό.
_optional = [a for a in ('admin_interface', 'colorfield')
             if importlib.util.find_spec(a) is not None]
if _optional:
    _i = INSTALLED_APPS.index('django.contrib.admin')
    INSTALLED_APPS = INSTALLED_APPS[:_i] + tuple(_optional) + INSTALLED_APPS[_i:]


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
DEFAULT_CHARSET = 'utf-8'
DATE_INPUT_FORMATS = ('%d-%m-%Y', '%d/%m/%Y')
DATE_FORMAT = 'd-m-Y'

# Το USE_L10N καταργήθηκε στο Django 5.0 και η τοπικοποίηση είναι πλέον
# πάντα ενεργή, οπότε τα παραπάνω θα τα σκίαζε το locale «el» του Django.
# Το FORMAT_MODULE_PATH τα επαναφέρει (βλ. dideman/formats/el/formats.py).
FORMAT_MODULE_PATH = ['dideman.formats']

INTERNAL_IPS = ('127.0.0.1',)

DATABASES = secret_settings.DATABASES
EMAIL_HOST = secret_settings.EMAIL_HOST
EMAIL_HOST_USER = secret_settings.EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = secret_settings.EMAIL_HOST_PASSWORD
SECRET_KEY = secret_settings.SECRET_KEY

