"""
Django settings for config project.
"""
import os

from pathlib import Path

import dj_database_url
import dotenv

dotenv.load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-pvbql8bi=baoyahjqvx7r!^w!1aa!&$mdg%_^jc3cx1=@ss$ia'
DEBUG = os.environ.get('DEBUG', False)

ALLOWED_HOSTS = [
    '127.0.0.1',
    "ride-production-89bb.up.railway.app"
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    "corsheaders",
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'drf_yasg',  # coreapi o'rniga

    # Local apps
    'bot_app',
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


DATABASES = {
    'default': dj_database_url.config(
        default="postgresql://postgres:KfXSxCytxDoCpmnwwnkobIKtPjvOuiyL@shortline.proxy.rlwy.net:14241/railway",
        conn_max_age=600,
        ssl_require=False
    )
}

# REST Framework settings
REST_FRAMEWORK = {
    # To'g'ri schema class
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.openapi.AutoSchema',

    # Renderer va Parser sozlamalari
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        # 'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],

    # Autentifikatsiya va ruxsatlar
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],

    # Filter va qidiruv
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],

    # Pagination
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,

    # Exception handling
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',

    # Default format
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATE_FORMAT': '%Y-%m-%d',
    'TIME_FORMAT': '%H:%M:%S',
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
STATICFILES_DIRS = [
    BASE_DIR / "staticfiles",  # agar sizda qo‘shimcha static papkalar bo‘lsa
]

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


REDOC_SETTINGS = {
    'LAZY_RENDERING': False,
}



STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

CSRF_TRUSTED_ORIGINS = [
    "https://ride-production-89bb.up.railway.app"
]

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

CELERY_BROKER_URL = 'redis://default:GCcEotAzxsPJAsyehxeImPDSTzpPISLX@metro.proxy.rlwy.net:50038'
CELERY_RESULT_BACKEND = 'redis://default:GCcEotAzxsPJAsyehxeImPDSTzpPISLX@metro.proxy.rlwy.net:50038'

SWAGGER_SETTINGS = {
    'DEFAULT_MODEL_RENDERING': 'example',
    'USE_SESSION_AUTH': False,
    'SECURITY_DEFINITIONS': {
        'Token': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'SUPPORTED_SUBMIT_METHODS': ['get', 'post', 'put', 'patch', 'delete'],
    'DEFAULT_API_URL': 'https://ride-production-89bb.up.railway.app'
}

