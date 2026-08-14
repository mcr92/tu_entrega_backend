from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiParameter
from rest_framework.serializers import CharField, DecimalField, URLField, IntegerField
from tu_entrega_app.models import Ticket
from tu_entrega_app.services.serializers.ticket_serializer import TicketSerializer, TicketCreateSerializer
from tu_entrega_app.services.serializers.messenger_available_serializaer import MessengerAvailableSerializer
from tu_entrega_app.views.requests.ticket_request import CreateRequest, AcceptRequest
from tu_entrega_app.services.ticket_service import TicketService


class TicketListPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"

class TicketView(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = TicketListPagination

    filterset_fields = ["product", "delivery_contact__address", "collection_contact__address"]
    search_fields = [
        "product", "delivery_contact__address", "collection_contact__address"
    ]

    filter_backends = [
        SearchFilter,
        OrderingFilter
    ]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            serializer_class = TicketCreateSerializer
        else:
            serializer_class = TicketSerializer
        
        return serializer_class

    def create(self, request, *args, **kwargs):
        validator = CreateRequest(request)
        if not validator.is_valid:
            return validator.error_response        
        return TicketService.process_create(request)

    @extend_schema(
            operation_id="ticket_canceled",
            request = None,
            responses={
            204: None,
            404: inline_serializer(
                name="Error Response",
                fields={
                    "detail": CharField()
                    },
            ),
            409: inline_serializer(
                name="Error Response",
                fields={
                    "detail": CharField()
                    },
            ),
            
        }
    )
    @action(detail=True, methods=["post"])
    def canceled(self, request, pk = None):    
        return TicketService.process_accept(request, pk)
    
    @extend_schema(
            operation_id="ticket_accept",
            request = inline_serializer(
                    name="Ticket_Accept",
                    fields={
                        "amount": DecimalField(max_digits=5, decimal_places=2)
                    }
                )
            ,
            responses={
            204: None,
            404: inline_serializer(
                name="Error Response",
                fields={
                    "detail": CharField()
                    },
            ),
            409: inline_serializer(
                name="Error Response",
                fields={
                    "detail": CharField()
                    },
            ),
            
        }
    )
    @action(detail=True, methods=["post"])
    def accept(self, request, pk = None):
        validator = AcceptRequest(request)
        if not validator.is_valid:
            return validator.error_response     
        return TicketService.process_accept(request, pk)

    @extend_schema(
                operation_id="confirm_messenger",
                request = None
                ,
                responses={
                204: None,
                404: inline_serializer(
                    name="Error Response",
                    fields={
                        "detail": CharField()
                        },
                ),
                409: inline_serializer(
                    name="Error Response",
                    fields={
                        "detail": CharField()
                        },
                ),
                
            }
        )
    @action(detail=True, methods=["post"], url_path="messenger/(?P<messenger_id>[^/.]+)")
    def confirm_messenger(self, request, pk = None, messenger_id=None):
        return TicketService.process_confirm_messenger(request, pk, messenger_id)
    
    @extend_schema(
                operation_id="messengers_list",
                 parameters=[
                    OpenApiParameter(name="ordering", description="Which field to use when ordering the results."),
                    OpenApiParameter(name="page", type=int, description="A page number within the paginated result set."),
                    OpenApiParameter(name="page_size", type=int, description= "Number of results to return per page."),
                    OpenApiParameter(name="search", description="A search term.")
                ],
                request = None
                ,
                responses={
                204: inline_serializer(
                    name="List Messenger Available",
                    fields={
                        "count": IntegerField(),
                        "next": URLField(),
                        "previous": URLField(),
                        "results": MessengerAvailableSerializer(many=True)
                    }
                ),
                404: inline_serializer(
                    name="Error Response",
                    fields={
                        "detail": CharField()
                        },
                ),
                409: inline_serializer(
                    name="Error Response",
                    fields={
                        "detail": CharField()
                        },
                ),
                
            }
        )
    @action(detail=True, methods=["get"])
    def messenger(self, request, pk = None):
        return TicketService.process_messenger_list(request, pk)