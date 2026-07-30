"""
Конфигурация WSGI проекта.

Публикует вызываемый объект WSGI в переменной модуля ``application``.
Подробности приведены в документации Django:
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
