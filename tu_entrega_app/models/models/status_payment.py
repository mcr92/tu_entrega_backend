from django.db import models
from tu_entrega_app.utils.constants import ApiConstants

class Status_Payment(models.Model):
    status = models.IntegerField(db_index=True, null=False, default=1,choices=ApiConstants.PaymentStatus.choices())
    created_at = models.DateTimeField(auto_now_add=True)