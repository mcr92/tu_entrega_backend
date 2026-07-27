from rest_framework import serializers
from tu_entrega_app.models import Ticket, Contact, Status_Ticket
from tu_entrega_app.services.serializers.contact_serializer import ContactSerializer
from tu_entrega_app.services.serializers.user_serializer import UserUpdateSerializer
from tu_entrega_app.services.serializers.messenger_serializer import MessengerSerializer
from tu_entrega_app.utils.constants import ApiConstants


class TicketSerializer(serializers.ModelSerializer):
    
    delivery_contact = ContactSerializer(read_only=True)
    collection_contact = ContactSerializer(read_only=True)
    owner = UserUpdateSerializer(read_only=True)
    messenger = MessengerSerializer(read_only=True)
    currency = serializers.CharField(read_only = False, help_text=f"{[values for values in ApiConstants.Currency.items()]}", default="USD")
    payment_method = serializers.CharField(read_only = False, help_text=f"{[values for values in ApiConstants.Payment_Method.items()]}", default="Efectivo")
    
    
    class Meta:
        model = Ticket
        fields = [
            "id", "product", "price", "currency", "payment_method", 
            "price_save", "created_at", "updated_at",
            "delivery_contact", "collection_contact",
            "owner", "messenger"
        ]
        depth = 0  # Importante: quita el depth

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Reemplaza los valores numéricos con sus representaciones en texto
        data['currency'] = ApiConstants.Currency.get(instance.currency)
        data['payment_method'] = ApiConstants.Payment_Method.get(instance.payment_method)
        
        data['owner'] = UserUpdateSerializer(instance.owner).data
        data['messenger'] = MessengerSerializer(instance.messenger).data
        return data


class TicketCreateSerializer(serializers.ModelSerializer):
    delivery_contact = ContactSerializer(read_only=False)
    collection_contact = ContactSerializer(read_only=False)
    currency = serializers.CharField(read_only = False, help_text=f"{[values for values in ApiConstants.Currency.items()]}", default="USD")
    payment_method = serializers.CharField(read_only = False, help_text=f"{[values for values in ApiConstants.Payment_Method.items()]}", default="Efectivo")
    status = serializers.CharField(read_only = True, help_text=f"{[values for values in ApiConstants.Status_Ticket.items()]}", default="Pendiente")
    owner = UserUpdateSerializer(read_only = False)

    class Meta:
        model = Ticket
        fields = ["product", "price", "owner", "currency", "payment_method", "price_save", "delivery_contact", "collection_contact", "status"]

    def create(self, validated_data):
        return self.__perform_creadit__(validated_data)
    
    def update(self, instance, validated_data):
        return self.__perform_creadit__(validated_data, instance)

    def __perform_creadit__(self, validated_data, instance:Ticket=None):

        currency = ApiConstants.Currency.from_string(validated_data.get("currency"))

        if currency:
            validated_data["currency"] = currency

        payment_method = ApiConstants.Payment_Method.from_string(validated_data.get("payment_method"))
        
        if payment_method:
            validated_data["payment_method"] = payment_method
                
        delivery_contact = validated_data.get("delivery_contact")
        if not delivery_contact:
            raise("delivery_contact is requirement")

        change_delivery = instance and (
            instance.delivery_contact.address != delivery_contact.get("address") or
            instance.delivery_contact.phone != delivery_contact.get("phone") or
            instance.delivery_contact.lat != delivery_contact.get("lat") or
            instance.delivery_contact.lng != delivery_contact.get("lng")
            )

        if not instance or change_delivery:
            try:
                delivery_serializer = ContactSerializer(data=delivery_contact)
                delivery_serializer.is_valid(raise_exception=True)
                delivery = delivery_serializer.save()
                validated_data["delivery_contact"] = delivery
            except serializers.ValidationError as error:
                raise (f"{error}")
            except Exception as error:
                raise("Algo salio mal al crear la direccion de entrega.")
        else:
            validated_data["delivery_contact"] = instance.delivery_contact

        collection_contact = validated_data.get("collection_contact")
        if not collection_contact:
            raise("collection_contact is requirement")

        change_collection = instance and (
            instance.collection_contact.address != collection_contact.get("address") or
            instance.collection_contact.phone != collection_contact.get("phone") or
            instance.collection_contact.lat != collection_contact.get("lat") or
            instance.collection_contact.lng != collection_contact.get("lng")
            )
        if not instance or change_collection:
            try:
                collection_serializer = ContactSerializer(data=collection_contact)
                collection_serializer.is_valid(raise_exception=True)
                collection = collection_serializer.save()
                validated_data["collection_contact"] = collection
            except serializers.ValidationError as error:
                raise (f"{error}")
            except Exception as error:
                raise("Algo salio mal al crear la direccion de recogida.")
        else:
            validated_data["collection_contact"] = instance.collection_contact
        
        if instance:
            return super().update(instance, validated_data)
                
        return super().create(validated_data)

    def to_representation(self, instance):
        """Controla cómo se serializa la respuesta después de crear/actualizar"""
        # Obtén la representación por defecto
        data = super().to_representation(instance)
        
        # Convierte los valores numéricos a sus representaciones en texto
        data['currency'] = ApiConstants.Currency.get(instance.currency)
        data['payment_method'] = ApiConstants.Payment_Method.get(instance.payment_method)
        
        # También puedes serializar los contactos manualmente si quieres más control
        data['delivery_contact'] = ContactSerializer(instance.delivery_contact).data
        data['collection_contact'] = ContactSerializer(instance.collection_contact).data
        data['status'] = instance.last_status
        data['owner'] = UserUpdateSerializer(instance.owner).data
        
        return data