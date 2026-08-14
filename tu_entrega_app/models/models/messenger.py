from django.db import models
from tu_entrega_app.models import User

class Messenger(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messengers')
    lat = models.DecimalField(max_digits=9, decimal_places=7, null=True, blank=True)
    lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    km_rate = models.DecimalField(max_digits=11, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    free_trip = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.user.name if self.user.name else self.user.phone