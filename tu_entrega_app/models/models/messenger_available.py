from django.db import models
from tu_entrega_app.models import Messenger

class MessengerAvailable(models.Model):
    messenger = models.ForeignKey(Messenger, on_delete=models.CASCADE, related_name='messenger_available')
    amount = models.DecimalField(max_digits=11, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)