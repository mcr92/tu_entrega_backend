from django.db import models
from tu_entrega_app.utils.constants import ApiConstants

class Status_Transaction(models.Model):
    status = models.IntegerField(db_index=True, null=False, default=1,choices=ApiConstants.TransactionStatus.choices())
    created_at = models.DateTimeField(auto_now_add=True)