import logging
from rest_framework import status
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from fcm_django.models import FCMDevice
from tu_entrega_app.models import User, BlockPlayer
from tu_entrega_app.services.serializers.user_serializer import UserLoginSerializer
from tu_entrega_app.connectors.discord_connector import DiscordConnector
from tu_entrega_app.utils.constants import ApiConstants
logger = logging.getLogger('django')

class AuthService:

    @staticmethod
    def process_login(request):
        phone = request.data.get("phone")

        is_block = BlockPlayer.objects.filter(player_blocked__phone=phone).exists()
        if is_block:
            return Response({"message":"Este usuario esta bloqueado, contacta a los administradores."}, status=status.HTTP_409_CONFLICT)
        
        exist = User.objects.filter(phone=phone).exists()

        password = request.data.get("password")
        with transaction.atomic():
            
            if not exist:
                # Busca o crea el usuario
                user, created = User.objects.get_or_create(
                        phone=phone,
                        password= password,
                        defaults={
                            'is_active': True
                        }
                    )

                user.set_password(password)
                user.save(update_fields=['password']) 
                
                DiscordConnector.send_event(
                    ApiConstants.AdminNotifyEvents.ADMIN_EVENT_NEW_USER.key,
                    {
                        "phone": phone
                    }
                )
                                
            else:
                user = User.objects.get(phone=phone)

                check = check_password(password, user.password)
                if not check:
                    return Response(data={
                        "message":"Contraseña incorrecta. Vuelva a intentar."
                        }, status=status.HTTP_401_UNAUTHORIZED)    

                user_auth = authenticate(phone=phone, password=password)
                if not user_auth:
                    return Response(data={
                        "message":"Contraseña incorrecta. Vuelva a intentar."
                        }, status=status.HTTP_401_UNAUTHORIZED)

            user.lastTimeInSystem = timezone.now()
            user.inactive_player = False
            user.save(update_fields=['lastTimeInSystem','inactive_player'])

            # Para registrar un dispositivo
            try:
                fcm_token = request.data.get("fcm_token")
                if fcm_token:
                    FCMDevice.objects.update_or_create(
                        registration_id = fcm_token,
                        defaults={
                            "user": user,  # asociar a un usuario
                            "type": "android",  # o "ios", "web"
                        }
                    )
            except Exception as error:
                logger.error(f"Error al registar el dispositivo FCM para el usuario {user.phone}. Error: {error}")


            # Genera tokens JWT usando simplejwt
            refresh = RefreshToken.for_user(user)

            player_data = UserLoginSerializer(user).data            
            player_data["is_new"] = (not exist)

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': player_data
            })
    
    @staticmethod
    def process_fcm_register(request):
        try:
            fcm_token = request.data.get("fcm_token")
            if str(fcm_token).strip() == "":
                return Response(
                    {"status":'error',
                     "message": "El token es requerido"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            FCMDevice.objects.update_or_create(
                registration_id = fcm_token,
                defaults={
                    "user": request.user,  # asociar a un usuario
                    "type": "android",  # o "ios", "web"
                }
            )
        except Exception as error:
            logger.error(f"Error creating FCM Device for user {request.user.phone}. Error->: {str(error)}")
            
        return Response(status=status.HTTP_204_NO_CONTENT)