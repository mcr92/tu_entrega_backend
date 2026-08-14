import uuid
from django.db import models
from tu_entrega_app.models import User, Status_Payment
from tu_entrega_app.utils.constants import ApiConstants

class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True, db_index=True)
    external_id = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    status_list = models.ManyToManyField(to=Status_Payment, blank=True, related_name="status_payment")
    user = models.ForeignKey(User,related_name="payer_payment",on_delete=models.PROTECT)
    amount = models.DecimalField(default=0, decimal_places=2, max_digits= 11)
    paymentmethod = models.IntegerField(db_index=True, null=False, default=2,choices=ApiConstants.Payment_Method.choices())
    created_at = models.DateTimeField(auto_now_add=True)
    paid_time = models.DateTimeField(blank=True, null=True)
    currency = models.IntegerField(db_index=True, null=False, default=2,choices=ApiConstants.Currency.choices())

    @property
    def last_status(self):
        status_obj = self.status_list.all().order_by('-created_at').first()
        if status_obj:
            return ApiConstants.PaymentStatus.get(int(status_obj.status))
        
        return ApiConstants.PaymentStatus.get(int(ApiConstants.PaymentStatus.Payment_PENDING.value[0]))

    @property
    def paymentmethod_str(self):
        if self.paymentmethod:
            return ApiConstants.Payment_Method.get(int(self.paymentmethod))
        return "-"
    
    @property
    def currency_str(self):
        if self.currency:
            return ApiConstants.Currency.get(int(self.currency))
        return "-"

    
        