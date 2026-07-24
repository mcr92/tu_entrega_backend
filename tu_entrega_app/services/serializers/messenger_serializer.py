from rest_framework import serializers
from tu_entrega_app.models import Messenger


class MessengerSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Messenger
        fields = "__all__"
        depth = 1



