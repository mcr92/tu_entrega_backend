from rest_framework import serializers
from tu_entrega_app.models import User


class UserLoginSerializer(serializers.ModelSerializer):
    is_admin = serializers.SerializerMethodField()
        
    def get_is_admin(self, obj:User) -> bool:
        return True if (obj.is_staff or obj.is_superuser) else False
    
    class Meta:
        model = User
        fields = ["id", "name", "phone", "is_admin"]


class UserSerializer(serializers.ModelSerializer):
    is_admin = serializers.SerializerMethodField()
        
    def get_is_admin(self, obj:User) -> bool:
        return True if (obj.is_staff or obj.is_superuser) else False
    
    class Meta:
        model = User
        fields = ["id", "name", "phone", "lastTimeInSystem", "is_admin"]

class UserUpdateSerializer(serializers.ModelSerializer):
        
    class Meta:
        model = User
        fields = ["name", "phone"]

class UserTransactionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ["id", "name", "phone"]