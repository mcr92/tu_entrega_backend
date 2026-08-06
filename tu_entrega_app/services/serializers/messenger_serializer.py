from rest_framework import serializers
from tu_entrega_app.models import Messenger
from tu_entrega_app.services.serializers.user_serializer import UserSerializer


class MessengerSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Messenger
        fields = "__all__"
        depth = 1


class MessengerCreateUpdateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Messenger
        fields = "__all__"

class MessengerResponseSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    
    class Meta:
        model = Messenger
        fields = "__all__"




