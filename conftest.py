from __future__ import annotations

import logging
import uuid

import icecream
import pytest
from django_svcs.apps import svcs_from
from nomnom.convention import ConventionConfiguration

icecream.install()

logging.disable(logging.CRITICAL)


@pytest.fixture(autouse=True)
def use_test_settings(settings):
    settings.DEBUG = False

    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

    settings.MIDDLEWARE = [
        middleware
        for middleware in settings.MIDDLEWARE
        if middleware != "whitenoise.middleware.WhiteNoiseMiddleware"
    ]

    # Use a faster password hasher
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

    settings.STORAGES = {
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        }
    }

    settings.WHITENOISE_AUTOREFRESH = True

    settings.CONTROLL_JWT_KEY = str(uuid.uuid4())


@pytest.fixture
def convention() -> ConventionConfiguration:
    return svcs_from().get(ConventionConfiguration)
