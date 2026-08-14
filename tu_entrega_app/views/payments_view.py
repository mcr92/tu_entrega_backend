from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import OrderingFilter
from django.db.models import Q
from tu_entrega_app.models import Transaction
from tu_entrega_app.views.requests.payments_request import ReloadRequest, RequestRechargeRequest
from tu_entrega_app.services.payments_service import PaymentService
from tu_entrega_app.services.serializers.transaction_serializer import ListTransactionsSerializer, ListTransactionsAdminSerializer
from tu_entrega_app.views.filters.payment_filter import PaymentSearchFilter
from tu_entrega_app.utils.request_permitions import IsSuperAdminUser
from drf_spectacular.utils import extend_schema, inline_serializer,OpenApiParameter, OpenApiExample
from rest_framework.serializers import BooleanField, IntegerField, CharField, ListField, UUIDField, DecimalField

class PaymentListPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"

class PaymentView(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = Transaction.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = PaymentListPagination
    serializer_class = ListTransactionsSerializer
    filter_backends = [
        OrderingFilter,
        PaymentSearchFilter
        ]
    search_fields = ['type', 'from_user__name', 'from_user__phone', 'to_user__phone', 'to_user__name', 'status_list__status']

    def get_permissions(self):
        if self.action in ["select", "confirm", "cancel"]:
            permission_classes = [IsAdminUser]
        elif self.action in ['recharge', 'extract', 'promotion']:
            permission_classes = [IsSuperAdminUser]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if not user.is_superuser and not user.is_staff:
            queryset = Transaction.objects.filter(Q(from_user__id = user.id) | Q(to_user__id = user.id)).order_by("-time")
        else:
            queryset = Transaction.objects.all().exclude(type__in = [2,3,4]).order_by("-time")
        if self.action in ["select", "confirm", "cancel"]:
            queryset.exclude(type__in = [2,3,4] )
        return queryset 
    
    def get_serializer_class(self):
        user = self.request.user
        if not user.is_superuser and not user.is_staff:
            serializer_class = ListTransactionsSerializer
        else:
            serializer_class = ListTransactionsAdminSerializer
        return serializer_class
    
    @extend_schema(
            operation_id="payments_recharge",
            request = inline_serializer(
                    name="Payments Recharge Request",
                    fields={
                        "amount" : DecimalField(max_digits=11,decimal_places=2,required=True),
                        "user_id": IntegerField(required=True),
                        "paymentmethod": CharField(required=False, help_text="Efectivo, Transferencia")
                    }
                ),
            responses={
            200: inline_serializer(
                name="Payments Recharge Response",
                fields={
                    'user': CharField(required=False),
                    "amount": DecimalField(max_digits=11,decimal_places=2,required=True),
                    "pay": DecimalField(max_digits=11,decimal_places=2,required=True),
                    "paymentmethod": CharField(required=False)
                    },
            ),
            401: inline_serializer(
                    name="Error Response",
                    fields={
                        "detail": CharField()
                        },
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
    @action(detail=False, methods=["post"])
    def recharge(self, request, pk = None):

        validate_request = ReloadRequest(request)
        if not validate_request.is_valid:
            return validate_request.error_response
        
        return PaymentService.process_recharge(request)
   
    @extend_schema(
            operation_id="payments_extract",
            request = inline_serializer(
                    name="Payments Extract Request",
                    fields={
                        "amount" : DecimalField(max_digits=11,decimal_places=2,required=True),
                        "user_id": IntegerField(required=True)
                    }
                ),
            responses={
            204: None,
            401: inline_serializer(
                name="Error Response",
                fields={
                    "detail": CharField()
                },
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
    @action(detail=False, methods=["post"])
    def extract(self, request, pk = None):

        validate_request = ReloadRequest(request)
        
        if not validate_request.is_valid:
            return validate_request.error_response
        
        return PaymentService.process_extract(request)

    @extend_schema(
            operation_id="payments_request_recharge",
            request = inline_serializer(
                    name="Payments Request Recharge",
                    fields={
                        "amount" : DecimalField(max_digits=11,decimal_places=2,required=True),
                        "paymentmethod": CharField(required=False, help_text="Efectivo, Transferencia")
                    }
                ),
            responses={
            200: inline_serializer(
                name="Payments Request Recharge Response",
                fields={
                    'transaction_id': CharField(max_length=6, min_length=6)
                    },
            ),
            401: inline_serializer(
                    name="Error Response",
                    fields={
                        "detail": CharField()
                        },
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
    @action(detail=False, methods=["post"])
    def request_recharge(self, request, pk = None):

        validate_request = RequestRechargeRequest(request)
        if not validate_request.is_valid:
            return validate_request.error_response 
        
        return PaymentService.process_request_recharge(request)
    
    @extend_schema(
            operation_id="payments_promotion",
            request = inline_serializer(
                    name="Payments Promotion Request",
                    fields={
                        "amount" : DecimalField(max_digits=11,decimal_places=2,required=True),
                        "user_id": IntegerField(required=True)
                    }
                ),
            responses={
            204:None,
            401: inline_serializer(
                    name="Error Response",
                    fields={
                        "detail": CharField()
                        },
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
    @action(detail=False, methods=["post"])
    def promotion(self, request, pk = None):

        validate_request = ReloadRequest(request)
        if not validate_request.is_valid:
            return validate_request.error_response 
        
        return PaymentService.process_promotions(request)

    @extend_schema(
            operation_id="payments_transfer",
            request = inline_serializer(
                    name="Payments Transfer Request",
                    fields={
                        "amount" : DecimalField(max_digits=11,decimal_places=2,required=True),
                        "user_id": IntegerField(required=True),
                    }
                ),
            responses={
            204: None,
            401: inline_serializer(
                name="Error Response",
                fields={
                    "detail": CharField()
                    },
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
    @action(detail=False, methods=["post"])
    def transfer(self, request, pk = None):

        validate_request = ReloadRequest(request)
        if not validate_request.is_valid:
            return validate_request.error_response
        
        return PaymentService.process_transfer(request)
    
    @extend_schema(
            operation_id="payments_list",
            request = None,
            responses={
            200: ListTransactionsSerializer(many=True),            
        }
    )
    def list(self, request, pk = None):
        return mixins.ListModelMixin.list(self, request)
    
    @extend_schema(
            operation_id="payments_select",
            request = None,
            responses={
            204: None,
            401: inline_serializer(
                    name="Error Response",
                    fields={
                        "detail": CharField()
                        },
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
            )
        }
    )
    @action(detail=True, methods=["post"])
    def select(self, request, pk = None):
        return PaymentService.process_select(request, pk)
    
    @extend_schema(
            operation_id="payments_confirm",
            request = None,
            responses={
            204: None,
            401: inline_serializer(
                    name="Error Response",
                    fields={
                        "detail": CharField()
                        },
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
            )  
        }
    )
    @action(detail=True, methods=["post"])
    def confirm(self, request, pk = None):
        return PaymentService.process_confirm(request, pk)
    
    @extend_schema(
            operation_id="payments_cancel",
            request = None,
            responses={
            204: None,
            401: inline_serializer(
                    name="Error Response",
                    fields={
                        "detail": CharField()
                        },
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
            )  
        }
    )
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk = None):
        return PaymentService.process_cancel(request, pk)
  