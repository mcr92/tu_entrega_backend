import logging
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.serializers import CharField
from tu_entrega_app.views.requests.auth_request import LoginRequest, FCMRegisterRequest
from tu_entrega_app.services.auth_service import AuthService
from tu_entrega_app.services.serializers.user_serializer import UserLoginSerializer
from tu_entrega_app.utils.api_http import ErrorResponse

logger = logging.getLogger('django')

@extend_schema(
            operation_id="login",
            request = {
            "application/json": inline_serializer(
                name="Login Request",
                fields={
                    'phone': CharField(required=True, max_length=20),
                    'password': CharField(required=True),
                    "fcm_token": CharField(required=False)
                    },
            )},
            responses={
            200: inline_serializer(
                name="Login Response",
                fields={
                    "user": UserLoginSerializer(),
                    "access": CharField(required=True),
                    "refresh": CharField(required=True)
                    },
            ),
            401: inline_serializer(
                name="Error Response",
                fields={
                    "message": CharField()
                    },
            ),
            404: inline_serializer(
                name="Error Response",
                fields={
                    "message": CharField()
                    },
            ),
            409: inline_serializer(
                name="Error Response",
                fields={
                    "message": CharField()
                    },
            ),
            
        }
    )
@api_view(['POST'])
@csrf_exempt
def login(request):
    try:
        validator = LoginRequest(request)
        if not validator.is_valid:
            return validator.error_response
        return AuthService.process_login(request)
    except BaseException as e:
        logger.critical(f"Error created user. Error => {str(e)}")(exception=e, request=request)
        return ErrorResponse()

@extend_schema(
            operation_id="fcm-register",
            request = {
            "application/json": inline_serializer(
                name="FCM Request",
                fields={
                    "fcm_token": CharField(required=True)
                    },
            )},
            responses={
            204:None            
        }
    )
@api_view(['POST'])
@csrf_exempt
@permission_classes([IsAuthenticated])
def fcm_register(request):               
    try:
        validator = FCMRegisterRequest(request)
        if not validator.is_valid:
            return validator.error_response
        return AuthService.process_fcm_register(request)
    except BaseException as e:
        logger.critical(f"Error created fcm register. Error => {str(e)}")(exception=e, request=request)
        return ErrorResponse()

urlpatterns = [
    path('', login, name='auth_login'),
    path('fcm', fcm_register, name='fcm_register'),
]