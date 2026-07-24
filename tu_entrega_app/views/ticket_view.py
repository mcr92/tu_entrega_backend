from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from tu_entrega_app.models import Ticket
from tu_entrega_app.services.serializers.ticket_serializer import TicketSerializer, TicketCreateSerializer


class TicketView(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]


    filterset_fields = ["product", "delivery_contact__address", "collection_contact__address"]
    search_fields = [
        "product", "delivery_contact__address", "collection_contact__address"
    ]

    filter_backends = [
        SearchFilter,
        OrderingFilter
    ]

    def get_serializer_class(self):
        if self.action in ["create"]:
            serializer_class = TicketCreateSerializer
        else:
            serializer_class = TicketSerializer
        
        return serializer_class