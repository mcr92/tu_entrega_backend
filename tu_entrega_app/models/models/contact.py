from django.db import models
from django.core.validators import (
    RegexValidator
)

class Contact(models.Model):
    address = models.CharField(max_length=200)
    lat = models.DecimalField(max_digits=25, decimal_places=22, null=True, blank=True)
    lng = models.DecimalField(max_digits=25, decimal_places=22, null=True, blank=True)
    phone = models.CharField(max_length=20, validators=[RegexValidator(regex=r'^\+{1}?\d{9,15}$')], null=True, blank=True)
    
    def __str__(self):
        return f"{self.id}_{self.address}"