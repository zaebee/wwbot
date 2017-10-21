from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ServicesConfig(AppConfig):
    name = 'services'
    label = 'services'
    verbose_name = _('Services app')
