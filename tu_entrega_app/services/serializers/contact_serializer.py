from rest_framework import serializers
from tu_entrega_app.models import Contact


class ContactSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Contact
        fields = "__all__"
        depth = 0



