from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from tu_entrega_app.models import Messenger
from tu_entrega_app.services.serializers.messenger_serializer import MessengerSerializer


class MessengerView(viewsets.ModelViewSet):
    queryset = Messenger.objects.all()
    serializer_class = MessengerSerializer
    permission_classes = [IsAuthenticated]


    filterset_fields = ["user__name", "user__phone"]
    search_fields = [
        "user__name", "user__phone"
    ]

    filter_backends = [
        SearchFilter,
        OrderingFilter
    ]