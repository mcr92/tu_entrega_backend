from rest_framework import serializers
from tu_entrega_app.models import MessengerAvailable
from tu_entrega_app.services.serializers.user_serializer import UserSerializer
from tu_entrega_app.services.serializers.messenger_serializer import MessengerResponseSerializer


class MessengerAvailableSerializer(serializers.ModelSerializer):
    messenger = MessengerResponseSerializer()

    class Meta:
        model = MessengerAvailable
        fields = "__all__"




