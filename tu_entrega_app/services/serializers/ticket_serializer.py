from rest_framework import serializers
from tu_entrega_app.models import Ticket
from tu_entrega_app.services.serializers.contact_serializer import ContactSerializer


class TicketSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Ticket
        fields = "__all__"
        depth = 1



class TicketCreateSerializer(serializers.ModelSerializer):
    delivery_contact = ContactSerializer()
    collection_contact = ContactSerializer()

    class Meta:
        model = Ticket
        fields = ["product", "price", "currency", "payment_method", "price_save", "delivery_contact", "collection_contact"]