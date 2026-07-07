import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class PasswordValidator:
    def __init__(self, field):
        self.field = field

    def __call__(self, value):
        reg_patter = re.compile(r'^[A-Za-z0-9]+$')
        tmp_value = dict(value).get(self.field)
        if not bool(reg_patter.match(tmp_value)):
            raise ValidationError(_('Password must contain only letters and numbers'))