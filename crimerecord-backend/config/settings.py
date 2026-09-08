# config/settings.py
#
# WHY each change vs. the old settings.py:
#
# 1. AUTH_USER_MODEL removed entirely.
#    It pointed to 'accounts.User' which didn't exist, crashing on startup.
#    We do not use Django's auth system — authentication is bcrypt + sessions.
#
# 2. 'rest_framework.authtoken' removed from INSTALLED_APPS.
#    It requires an authtoken_token table we don't have.
#    Token auth is replaced by session auth (see accounts/views.py).
#
# 3. 'django.contrib.admin' and 'django.contrib.auth' are kept in INSTALLED_APPS
#    because removing them causes contenttypes / permission framework errors in
#    some DRF internals.  They just won't be used for login/user management.
#
# 4. DEFAULT_AUTHENTICATION_CLASSES: TokenAuthentication removed.
#    SessionAuthentication is kept so DRF decorators work with our session keys.
#    BasicAuthentication added as a fallback for browsable API in dev.
#
# 5. SESSION_ENGINE stays as default (db-backed).  Django's session table IS
#    used (it's separate from our users table) — run:
#      python manage.py migrate sessions
#    That's the only migration you need; it touches no business tables.
#
# 6. 'evidence' removed from INSTALLED_APPS — it was in the old settings but
#    no evidence app exists in the codebase.  Add it back if you create one.

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ──────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'dev-only-key-replace-before-deploy'
)
DEBUG         = os.environ.get('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

# ── Apps ──────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party
    'rest_framework',
    'corsheaders',
    # NOTE: 'rest_framework.authtoken' intentionally removed — no Token table in DB
    # Project apps
    'accounts',
    'cases',
    'alerts',
    'analytics',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]

WSGI_APPLICATION = 'config.wsgi.application'

# ── Database — existing MySQL schema ─────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.mysql',
        'NAME':     os.environ.get('DB_NAME',     'nexus_crms'),
        'USER':     os.environ.get('DB_USER',     'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'root'),
        'HOST':     os.environ.get('DB_HOST',     '127.0.0.1'),
        'PORT':     os.environ.get('DB_PORT',     '3306'),
        'OPTIONS':  {
            'charset':      'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# ── Auth — NOT used for our users table ───────────────────────────────────────
# AUTH_USER_MODEL is intentionally absent.  Django's built-in auth is not used
# for the application users.  bcrypt + sessions handles all auth (accounts/views.py).
#
# You still need to run:
#   python manage.py migrate sessions contenttypes auth
# so that Django's session table, content types, and admin work.
# That will NOT touch any of your existing business tables (all managed=False).

AUTH_PASSWORD_VALIDATORS = []   # Not used — bcrypt validation in accounts/views.py

# ── Sessions ─────────────────────────────────────────────────────────────────
SESSION_ENGINE         = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE     = 86400 * 7    # 7 days
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
# In production set SESSION_COOKIE_SECURE = True (HTTPS only)

# ── CORS ─────────────────────────────────────────────────────────────────────
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS    = True
    CORS_ALLOW_CREDENTIALS    = True   # required for session cookies cross-origin
else:
    CORS_ALLOWED_ORIGINS      = os.environ.get(
        'CORS_ALLOWED_ORIGINS', 'http://127.0.0.1:5500'
    ).split(',')
    CORS_ALLOW_CREDENTIALS    = True

# ── DRF ───────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',   # dev fallback only
        # TokenAuthentication removed — no authtoken table in DB
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}

# ── i18n ─────────────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'UTC'
USE_I18N      = True
USE_TZ        = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'