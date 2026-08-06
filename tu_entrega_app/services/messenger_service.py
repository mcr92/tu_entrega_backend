import logging
from rest_framework import status
from rest_framework.response import Response
from django.db import transaction
from tu_entrega_app.models import User, Messenger
from tu_entrega_app.services.serializers.messenger_serializer import MessengerResponseSerializer, MessengerCreateUpdateSerializer

logger = logging.getLogger('django')

class MessengerService:

    @staticmethod
    def process_update(request):

        user_authenticated = request.user

        try:
            user = User.objects.get(id=user_authenticated.id)
        except:
            return Response({"detail":"Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if user.is_block:
            return Response({"detail":"Este usuario esta bloqueado, contacta a los administradores."}, status=status.HTTP_409_CONFLICT)

        try:
            messenger = Messenger.objects.get(user__id = user.id)
        except:
            messenger = None
        
        data = request.data.copy()
        
        try:
            with transaction.atomic():
                if messenger is None:
                    data["user"] = user.id
                    serializer = MessengerCreateUpdateSerializer(data=data)
                    if serializer.is_valid(raise_exception=True):
                        # Pasa el usuario explícitamente al guardar
                        messenger_new = serializer.save()
                        reponse_serializer = MessengerResponseSerializer(messenger_new)
                        return Response(data= reponse_serializer.data, status=status.HTTP_201_CREATED)
                else:
                    serializer = MessengerCreateUpdateSerializer(messenger, data=data, partial=True)

                    if serializer.is_valid(raise_exception=True):
                        messenger_update = serializer.save()
                        reponse_serializer = MessengerResponseSerializer(messenger_update)
                                                
                        return Response(data= reponse_serializer.data, status=status.HTTP_200_OK)
                
        except Exception as error:
            return Response({"detail": f"Error al actualizar el mensagero: {str(error)}"}, status=status.HTTP_409_CONFLICT)

    