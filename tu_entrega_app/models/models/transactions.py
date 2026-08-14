import uuid
from django.db import models
from tu_entrega_app.models import User, Status_Transaction, Payment
from tu_entrega_app.utils.constants import ApiConstants

class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    from_user = models.ForeignKey(User,related_name="payer",on_delete=models.PROTECT,null=True,blank=True)
    to_user = models.ForeignKey(User,related_name="collector",on_delete=models.PROTECT,null=True,blank=True)
    amount = models.DecimalField(default=0, decimal_places=2, max_digits= 11)
    time = models.DateTimeField(auto_now_add=True)
    status_list = models.ManyToManyField(to=Status_Transaction, blank=True, related_name="status_transaction")
    type = models.IntegerField(db_index=True, null=False, default=1,choices=ApiConstants.TransactionType.choices())
    admin = models.ForeignKey(User, related_name="admin_user", blank=True, null=True, on_delete=models.PROTECT)
    external_id = models.CharField(max_length=50, null=True, blank=True)
    payment = models.ForeignKey(Payment, related_name="payment", blank=True, null=True, on_delete=models.SET_NULL)
    descriptions = models.CharField(max_length=100, null=True, blank=True)
    whatsapp_url = models.URLField(null=True, blank=True, max_length=1500)


    @property
    def last_status(self)-> str:
        status_obj = self.status_list.all().order_by('-created_at').first()
        if status_obj:
            return ApiConstants.TransactionStatus.get(int(status_obj.status))
        
        return ApiConstants.TransactionStatus.get(int(ApiConstants.TransactionStatus.TRANSACTION_PENDING.value[0]))

    @property
    def type_str(self)->str:
        if self.type:
            return ApiConstants.TransactionType.get(int(self.type))
        return "-"

    @property
    def status_int(self):
        status_obj = self.status_list.all().order_by('-created_at').first()
        if status_obj:
            return int(status_obj.status)
        
        return int(ApiConstants.TransactionStatus.TRANSACTION_PENDING.value[0])
        