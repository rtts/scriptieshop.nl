import os, sys, random, string, pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
MOLLIE_API_KEY = 'test_123'
DEBUG = 'runserver' in sys.argv
CANONICAL_URL = 'https://www.scriptieshop.nl'
KEYFILE = '/tmp/scriptieshop.secret'
ADMINS = [('Jaap Joris Vens', 'jj@rtts.eu')]
DEFAULT_FROM_EMAIL = 'noreply@rtts.eu'
DEFAULT_TO_EMAIL = ['info@copyshopdenbosch.nl']
ALLOWED_HOSTS = ['*']
ROOT_URLCONF = 'scriptieshop.urls'
WSGI_APPLICATION = 'scriptieshop.wsgi.application'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LANGUAGE_CODE = 'nl'
TIME_ZONE = 'Europe/Amsterdam'
USE_I18N = True
USE_L10N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
SAFE_ROOT = BASE_DIR / 'customer_files'
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

try:
    with open(KEYFILE) as f:
        SECRET_KEY = f.read()
except IOError:
    SECRET_KEY = ''.join(random.choice(string.printable) for x in range(50))
    with open(KEYFILE, 'w') as f:
        f.write(SECRET_KEY)

INSTALLED_APPS = [
    'scriptieshop',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'cms',
    'embed_video',
    'easy_thumbnails',
    'django_extensions',
]
if not DEBUG:
    INSTALLED_APPS += ['django.contrib.staticfiles']

MIDDLEWARE = [
    'django.middleware.cache.UpdateCacheMiddleware',
    'cms.middleware.SassMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
