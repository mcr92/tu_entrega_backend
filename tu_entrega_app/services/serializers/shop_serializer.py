from rest_framework import serializers
from tu_entrega_app.models import Shop


class ShopSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Shop
        fields = "__all__"
        depth = 1



