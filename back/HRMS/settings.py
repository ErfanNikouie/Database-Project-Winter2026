"""Django settings for the configurable HRMS backend."""

import os
from pathlib import Path
from typing import Optional

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(name: str, default: Optional[str] = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise ImproperlyConfigured(f"Missing required environment variable: {name}")
    return value


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return int(raw_value)


SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-only-unsafe-secret")

DEBUG = env_bool("DJANGO_DEBUG", True)

ALLOWED_HOSTS = [host.strip() for host in env("DJANGO_ALLOWED_HOSTS", "*").split(",") if host.strip()]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    'rest_framework_simplejwt.token_blacklist',
    'apps.common.apps.CommonConfig',
    'apps.authentication.apps.AuthenticationConfig',
    'apps.users.apps.UsersConfig',
    'apps.lookups.apps.LookupsConfig',
    'apps.forms.apps.FormsConfig',
    'apps.menus.apps.MenusConfig',
    'apps.dynamic_engine.apps.DynamicEngineConfig',
    'apps.reports.apps.ReportsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'HRMS.urls'

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

WSGI_APPLICATION = 'HRMS.wsgi.application'


DB_ENGINE = env("DB_ENGINE", "postgres").lower()
if DB_ENGINE == "sqlite":
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': str(BASE_DIR / 'db.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env("DB_NAME", "hrms"),
            'USER': env("DB_USER", "postgres"),
            'PASSWORD': env("DB_PASSWORD", "postgres"),
            'HOST': env("DB_HOST", "127.0.0.1"),
            'PORT': env("DB_PORT", "5432"),
            'CONN_MAX_AGE': env_int("DB_CONN_MAX_AGE", 60),
        }
    }


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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

AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'EXCEPTION_HANDLER': 'apps.common.api.exception_handler.custom_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

from datetime import timedelta  # noqa: E402

JWT_ACCESS_TOKEN_TIMEOUT_SECONDS = env_int("JWT_ACCESS_TOKEN_TIMEOUT_SECONDS", 86400)
JWT_REFRESH_TOKEN_TIMEOUT_SECONDS = env_int("JWT_REFRESH_TOKEN_TIMEOUT_SECONDS", 86400)

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(seconds=JWT_ACCESS_TOKEN_TIMEOUT_SECONDS),
    'REFRESH_TOKEN_LIFETIME': timedelta(seconds=JWT_REFRESH_TOKEN_TIMEOUT_SECONDS),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

ENABLE_SWAGGER = env_bool("ENABLE_SWAGGER", True)
SWAGGER_REQUIRE_AUTH = env_bool("SWAGGER_REQUIRE_AUTH", True)
SWAGGER_SCHEMA_CACHE_TIMEOUT = env_int("SWAGGER_SCHEMA_CACHE_TIMEOUT", 300)

SPECTACULAR_SETTINGS = {
    'TITLE': env('OPENAPI_TITLE', 'HRMS Dynamic Enterprise Platform API'),
    'DESCRIPTION': env(
        'OPENAPI_DESCRIPTION',
        'A configurable Human Resource Management System where administrators can create and modify business entities entirely from the UI.',
    ),
    'VERSION': env('OPENAPI_VERSION', '1.0.0'),
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    'COMPONENT_SPLIT_REQUEST': True,
    'CONTACT': {
        'name': env('OPENAPI_CONTACT_NAME', 'HRMS API Team'),
        'email': env('OPENAPI_CONTACT_EMAIL', 'api-team@example.com'),
    },
    'LICENSE': {
        'name': env('OPENAPI_LICENSE_NAME', 'Proprietary'),
        'url': env('OPENAPI_LICENSE_URL', 'https://example.com/license'),
    },
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'BearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            }
        }
    },
    'SECURITY': [{'BearerAuth': []}] if SWAGGER_REQUIRE_AUTH else [],
    'POSTPROCESSING_HOOKS': [
        'apps.forms.services.dynamic_openapi_service.inject_dynamic_form_schemas',
    ],
    'TAGS': [
        {'name': 'Authentication', 'description': 'JWT authentication APIs.'},
        {'name': 'Dynamic Data', 'description': 'Generic CRUD APIs over system and dynamic tables.'},
        {'name': 'Forms', 'description': 'Form metadata and runtime schema APIs.'},
        {'name': 'Menus', 'description': 'Permission-aware menu tree APIs.'},
        {'name': 'System', 'description': 'Platform metadata and system-level endpoints.'},
    ],
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,
        'displayRequestDuration': True,
        'docExpansion': 'none',
    },
}


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'apps': {
            'handlers': ['console'],
            'level': env('LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

HRMS = {
    'ROOT_USERNAME': env('HRMS_ROOT_USERNAME', 'root'),
    'ROOT_PASSWORD': env('HRMS_ROOT_PASSWORD', 'ChangeMe123!'),
    'ROOT_GROUP_NAME': env('HRMS_ROOT_GROUP_NAME', 'Root Administrators'),
}

