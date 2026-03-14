import os
import dj_database_url
from pathlib import Path
CODESPACE_NAME = os.getenv('CODESPACE_NAME')
CODESPACE_DOMAIN = os.getenv('GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN')

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- PRODUCTION SECURITY ---
# Railway will provide the SECRET_KEY via Environment Variables. 
# If not found, it falls back to your insecure local key.
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-m8#10x2ns71qgeru31p7mev-qyl!!rliu(o7p3x*o$83dn2(eb")

# Set DEBUG to False in Railway, True locally
DEBUG = os.environ.get("DEBUG", "True") == "True"

# Allow all hosts for initial setup; you can restrict this to your Wix domain later.
ALLOWED_HOSTS = ['*']

# --- APPLICATION DEFINITION ---
INSTALLED_APPS = [
    'Catalog',
    'corsheaders',            # Required for Wix connectivity
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",           # MUST be at the top
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",      # Required for static files on Railway
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "AmazonProject.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "AmazonProject.wsgi.application"

# --- DATABASE CONFIGURATION ---
# Switches to Postgres on Railway, stays SQLite locally
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600
    )
}

# --- CORS & SECURITY SETTINGS ---
# This allows your Wix site to access your Django data
CORS_ALLOW_ALL_ORIGINS = True 
CSRF_TRUSTED_ORIGINS = ["https://*.railway.app", "https://*.wixsite.com", "http://localhost:8000", "https://localhost:8000"]
if CODESPACE_NAME and CODESPACE_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(f'https://{CODESPACE_NAME}-8000.{CODESPACE_DOMAIN}')

# --- PASSWORD VALIDATION ---
AUTH_PASSWORD_VALIDATORS = []

# --- INTERNATIONALIZATION ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- STATIC FILES (CSS, JavaScript, Images) ---
STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# WhiteNoise helps serve static files without Nginx/Apache
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# --- AUTHENTICATION URLS ---
LOGIN_URL = 'staff_login'
LOGIN_REDIRECT_URL = 'staffs'

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
