from django.db import models
from tu_entrega_app.utils.constants import ApiConstants
from tu_entrega_app.utils.constants import Status_Ticket as Status_Values
from tu_entrega_app.models import Contact, User, Messenger, Status_Ticket, MessengerAvailable

class Ticket(models.Model):
    product = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    currency = models.IntegerField(db_index=True, null=False, default=1, choices=ApiConstants.Currency.choices())
    payment_method = models.IntegerField(db_index=True, null=False, default=1, choices=ApiConstants.Payment_Method.choices())
    price_save = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) ## Valor que debe dejar el mensajero de fondo

    delivery_contact = models.ForeignKey(Contact, on_delete=models.RESTRICT, related_name= 'delivery_contact') 
    collection_contact = models.ForeignKey(Contact, on_delete=models.RESTRICT, related_name= 'collection_contact')

    owner = models.ForeignKey(User, on_delete=models.RESTRICT, related_name= 'owner_tickets')

    messenger = models.ForeignKey(Messenger, on_delete=models.RESTRICT, related_name= 'messenger_tickets', null=True, blank=True)

    messenger_available_list = models.ManyToManyField(to=MessengerAvailable, blank=True, related_name="messengers_available")

    status = models.ManyToManyField(to=Status_Ticket, blank=True, related_name="status_ticket")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product}_{self.id}"

    @property
    def last_status(self):
        status_obj = self.status.all().order_by('-created_at').first()
        if status_obj:
            return ApiConstants.Status_Ticket.get(int(status_obj.status))
        
        return ApiConstants.Status_Ticket.get(int(Status_Values.PENDIENTE[1]))
    