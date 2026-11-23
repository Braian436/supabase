"""
Django settings for config project.

Base para el proyecto de organizacion de Practica Profesional II - ISDEM.
Las variables de entorno se leen desde el docker-compose.yml / archivo .env.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------
# Seguridad
# --------------------------------------------------------------------------
# En desarrollo tomamos un valor por defecto para no obligar a configurar nada
# antes de la primera clase. Para producción, SIEMPRE definir SECRET_KEY como
# variable de entorno con un valor propio y secreto.
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-cambiar-esta-clave-en-produccion'
)

# DEBUG viene de la variable de entorno DEBUG definida en docker-compose.yml.
# "1" = True, cualquier otro valor (o ausencia) = False.
DEBUG = os.environ.get('DEBUG', '0') == '1'

# DJANGO_ALLOWED_HOSTS viene separado por comas, ej: "localhost,127.0.0.1"
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


# --------------------------------------------------------------------------
# Aplicaciones instaladas
# --------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',

    # Terceros
    'rest_framework',
    'corsheaders',

    # Apps propias del proyecto
    'core',
    'api',
    'productos',
    'empleados',
    'turnos',
    'servicios',
    'ventas',
    'cajas',
    'compras',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# --------------------------------------------------------------------------
# Base de datos
# --------------------------------------------------------------------------
# Se conecta al servicio "db" definido en docker-compose.yml (Postgres).
# Los valores por defecto coinciden con los del docker-compose.yml y el
# .env.example, para que funcione "out of the box" sin configurar nada.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'proyecto_db'),
        'USER': os.environ.get('POSTGRES_USER', 'proyecto_user'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'proyecto_pass'),
        'HOST': os.environ.get('POSTGRES_HOST', 'db'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}


# --------------------------------------------------------------------------
# Internacionalización
# --------------------------------------------------------------------------
LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Salta'
USE_I18N = True
USE_TZ = True


# --------------------------------------------------------------------------
# Archivos estáticos
# --------------------------------------------------------------------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --------------------------------------------------------------------------
# Django REST Framework (API pública sin autenticación)
# --------------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'UNAUTHENTICATED_USER': None,
    'UNAUTHENTICATED_TOKEN': None,
    'DEFAULT_PAGINATION_CLASS': 'api.pagination.LimitePaginaPagination',
    'PAGE_SIZE': 10,
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
