import logging
from rest_framework import status
from rest_framework.response import Response
from django.db import transaction
from fcm_django.models import FCMDevice
from tu_entrega_app.models import User, Ticket, Status_Ticket, Messenger, MessengerAvailable
from tu_entrega_app.services.serializers.ticket_serializer import TicketCreateSerializer
from tu_entrega_app.utils.constants import ApiConstants
logger = logging.getLogger('django')

class TicketService:

    @staticmethod
    def process_create(request):

        user_authenticated = request.user

        try:
            user = User.objects.get(id=user_authenticated.id)
        except:
            return Response({"detail":"Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if user.is_block:
            return Response({"detail":"Este usuario esta bloqueado, contacta a los administradores."}, status=status.HTTP_409_CONFLICT)
        
        data = request.data.copy()

        data['owner'] = user.id
        
        try:
            with transaction.atomic():
                serializer = TicketCreateSerializer(data=data)
                if serializer.is_valid(raise_exception=True):
                    ticket = serializer.save()
                    status_ticket = Status_Ticket.objects.create(status=ApiConstants.Status_Ticket.PENDIENTE.value[0])
                    ticket.status.add(status_ticket)
                    return Response(data= serializer.data, status=status.HTTP_201_CREATED)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            return Response({"detail": f"Error al crear el ticket: {str(error)}"}, status=status.HTTP_409_CONFLICT)

    @staticmethod
    def process_accept(request, ticket_id):

        try:
            user = User.objects.get(id = request.user.id)
        except:
            return Response({"detail": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if user.is_block:
            return Response({"detail":"Este usuario esta bloqueado, contacta a los administradores."}, status=status.HTTP_409_CONFLICT)

        try:
            messenger = Messenger.objects.get(user__id = user.id)
        except:
            return Response({"detail":"Debes actualizar el perfil de mensajero."}, status=status.HTTP_409_CONFLICT)

        try:
            ticket = Ticket.objects.get(id = ticket_id)
        except:
            return Response({"detail": "Factura no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        if ticket.last_status != ApiConstants.Status_Ticket.PENDIENTE.value[1]:
            return Response({"detail": "Esta factura ya no esta disponible."}, status=status.HTTP_409_CONFLICT)

        try:
            with transaction.atomic():
                messenger = MessengerAvailable.objects.create(
                    messenger = messenger,
                    amount = request.data.get('amount')
                )

                ticket.messenger_available_list.add(messenger)

                return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception:
            return Response({"detail": "No se pudo seleccionar esta factura. Vuelva a intentar."}, status=status.HTTP_409_CONFLICT)
