from rest_framework import serializers
from tu_entrega_app.models import User, Transaction
from tu_entrega_app.services.serializers.user_serializer import UserTransactionSerializer
import pytz

class ListTransactionsSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    admin = UserTransactionSerializer()
    type = serializers.SerializerMethodField()
    
    def get_status(self, obj: Transaction) -> str:
        return obj.last_status

    def get_type(self, obj: Transaction) -> str:
            return obj.type_str
        
    def get_user(self, obj: Transaction) -> dict:
        if obj.from_user is not None:
            serializers = UserTransactionSerializer(obj.from_user)
            return serializers.data
        elif obj.to_user is not None:
            serializers = UserTransactionSerializer(obj.to_user)
            return serializers.data
        return None
        
    def get_time(self, obj: Transaction):
        timezone = "America/Havana"
        if obj.from_user:
            timezone = obj.from_user.timezone
        elif obj.to_user:
            timezone = obj.to_user.timezone
        return obj.time.astimezone(pytz.timezone(timezone))
    
    class Meta:
        model = Transaction
        fields = ['id', 'user', 'amount', 'type', 'status', 'time', 'admin', 'external_id', 'whatsapp_url']

class ListTransactionsAdminSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    admin = UserTransactionSerializer()
    phone = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    
    
    def get_status(self, obj: Transaction) -> str:
        return obj.last_status

    def get_type(self, obj: Transaction) -> str:
            return obj.type_str
    
    def get_user(self, obj: Transaction) -> dict:
        if obj.from_user is not None:
            serializers = UserTransactionSerializer(obj.from_user)
            return serializers.data
        elif obj.to_user is not None:
            serializers = UserTransactionSerializer(obj.to_user)
            return serializers.data
        return None
    
    def get_time(self, obj: Transaction):
        timezone = "America/Havana"
        return obj.time.astimezone(pytz.timezone(timezone)).strftime('%Y-%m-%dT%H:%M:%S.%f')
        
    def get_phone(self, obj: Transaction):
        if obj.from_user:
            return obj.from_user.phone
        elif obj.to_user:
            return obj.to_user.phone
        return None
    
    class Meta:
        model = Transaction
        fields = ['id', 'user', 'amount', 'type', 'status', 'time', 'admin', 'phone', 'whatsapp_url']
