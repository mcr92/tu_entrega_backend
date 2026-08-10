import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
from fcm_django.models import FCMDevice
from firebase_admin.messaging import Message, Notification
from tu_entrega_app.models import User, Ticket, Status_Ticket, Messenger, MessengerAvailable
from tu_entrega_app.services.serializers.ticket_serializer import TicketCreateSerializer
from tu_entrega_app.services.serializers.messenger_available_serializaer import MessengerAvailableSerializer
from tu_entrega_app.utils.constants import ApiConstants
from tu_entrega_app.utils.tickets_utils import find_nearby_messengers
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

                    if ticket.collection_contact.lat and ticket.collection_contact.lng:
                        try:
                            messenger_nearby = find_nearby_messengers(ticket.collection_contact.lat, ticket.collection_contact.lng)
                            FCMDevice.objects.filter(user__id__in=[messenger.user.id for messenger in messenger_nearby]).send_message(
                                Message(
                                    notification= Notification(
                                        title="Nueva factura disponible",
                                        body=f"Se ha creado una nueva factura para el producto {ticket.product}.",
                                    ),
                                    data={"ticket_id": ticket.id}
                                )
                            )
                        except Exception as error:
                            logger.error(f"Error al enviar notificación push al crear ticket. Error: {str(error)}")

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

                try:
                    FCMDevice.objects.filter(user__id = ticket.owner.id).send_message(
                        Message(
                            notification= Notification(
                                title="Factura aceptada",
                                body=f"El mensajero {messenger.messenger.user.name} ha aceptado la factura {ticket.product}.",
                            ),
                            data={"ticket_id": ticket.id}
                        )
                    )
                except Exception as error:
                    logger.error(f"Error al enviar notificación push al acceptar ticket. Error: {str(error)}")

                return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception:
            return Response({"detail": "No se pudo seleccionar esta factura. Vuelva a intentar."}, status=status.HTTP_409_CONFLICT)

    @staticmethod
    def process_canceled(request,ticket_id):

        try:
            user = User.objects.get(id = request.user.id)
        except:
            return Response({"detail": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if user.is_block:
            return Response({"detail":"Este usuario esta bloqueado, contacta a los administradores."}, status=status.HTTP_409_CONFLICT)

        try:
            ticket = Ticket.objects.get(id = ticket_id)
        except:
            return Response({"detail": "Factura no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        if ticket.owner.id != user.id:
            return Response({"detail": "No tienes permisos para realizar esta operación."}, status=status.HTTP_409_CONFLICT)

        if ticket.last_status != ApiConstants.Status_Ticket.PENDIENTE.value[1]:
            return Response({"detail": "No es posible cancelar esta orden."}, status=status.HTTP_409_CONFLICT)

        if ticket.messenger:
            return Response({"detail": "Esta factura ya se le asignó a un mensajero."}, status=status.HTTP_409_CONFLICT)

        try:
            with transaction.atomic():
                status_ticket = Status_Ticket.objects.create(status=ApiConstants.Status_Ticket.CANCELADO.value[0])
                ticket.status.add(status_ticket)

                return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as error:
            return Response({"detail": "No se pudo cancelar esta factura. Vuelva a intentar."}, status=status.HTTP_409_CONFLICT)



    @staticmethod
    def process_confirm_messenger(request,ticket_id, messenger_id):

        try:
            user = User.objects.get(id = request.user.id)
        except:
            return Response({"detail": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if user.is_block:
            return Response({"detail":"Este usuario esta bloqueado, contacta a los administradores."}, status=status.HTTP_409_CONFLICT)

        try:
            ticket = Ticket.objects.get(id = ticket_id)
        except:
            return Response({"detail": "Factura no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        if ticket.owner.id != user.id:
            return Response({"detail": "No tienes permisos para realizar esta operación."}, status=status.HTTP_409_CONFLICT)

        try:
            messenger_available = MessengerAvailable.objects.get(id = messenger_id)
        except:
            return Response({"detail":"No se pudo encontrar este mensajero."}, status=status.HTTP_404_NOT_FOUND)

        if ticket.messenger:
            return Response({"detail": "Esta factura ya se le asignó a un mensajero."}, status=status.HTTP_409_CONFLICT)

        try:
            with transaction.atomic():
                ticket.messenger = messenger_available.messenger
                ticket.save(update_fields=["messenger"])

                status_ticket = Status_Ticket.objects.create(status=ApiConstants.Status_Ticket.ACEPTADO.value[0])
                ticket.status.add(status_ticket)

                try:
                    FCMDevice.objects.filter(user__id = messenger_available.messenger.user.id).send_message(
                        Message(
                            notification= Notification(
                                title="Mensajero seleccionado",
                                body=f"Ha sido seleccionado para realizar la entrega de la factura {ticket.product}.",
                            ),
                            data={"ticket_id": ticket.id}
                        )
                    )
                except Exception as error:
                    logger.error(f"Error al enviar notificación push al confirmar mensajero. Error: {str(error)}")

                return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as error:
            return Response({"detail": "No se pudo seleccionar esta factura. Vuelva a intentar."}, status=status.HTTP_409_CONFLICT)


    @staticmethod
    def process_messenger_list(request,ticket_id):

        try:
            user = User.objects.get(id = request.user.id)
        except:
            return Response({"detail": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if user.is_block:
            return Response({"detail":"Este usuario esta bloqueado, contacta a los administradores."}, status=status.HTTP_409_CONFLICT)

        try:
            ticket = Ticket.objects.get(id = ticket_id)
        except:
            return Response({"detail": "Factura no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        if ticket.owner.id != user.id:
            return Response({"detail": "No tienes permisos para realizar esta operación."}, status=status.HTTP_409_CONFLICT)

        paginator = PageNumberPagination()
        page_size = request.query_params.get("page_size", 10)
        paginator.page_size = page_size

        try:
            messenger_list = ticket.messenger_available_list.all()
            result_page = paginator.paginate_queryset(messenger_list, request)

            response_serialiser = MessengerAvailableSerializer(result_page, many=True)

            return paginator.get_paginated_response(response_serialiser.data)
        except Exception as error:
            return Response({"detail": "No se pudo seleccionar esta factura. Vuelva a intentar."}, status=status.HTTP_409_CONFLICT)
    
