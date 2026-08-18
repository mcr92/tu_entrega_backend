from django.db import models
from django.core.validators import (
    RegexValidator
)
from tu_entrega_app.models import User

class Shop(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    lat = models.DecimalField(max_digits=25, decimal_places=22, null=True, blank=True)
    lng = models.DecimalField(max_digits=25, decimal_places=22, null=True, blank=True)
    other_phone = models.CharField(max_length=20, validators=[RegexValidator(regex=r'^\+{1}?\d{9,15}$')], null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shops')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name