import shortuuid
import os
import logging
from rest_framework import status
from rest_framework.response import Response
from django.db.models import Q, Sum, OuterRef, Subquery
from datetime import datetime, timedelta
from decimal import Decimal
from tu_entrega_app.models import User, Transaction, Payment, Status_Payment, Status_Transaction
from tu_entrega_app.utils.transactions_utils import create_reload_transactions, create_promotion_transactions, create_transfer_transactions, create_transactions
from tu_entrega_app.utils.constants import ApiConstants
from tu_entrega_app.utils.fcm_message import FCM_NOTIFICATION
from tu_entrega_app.utils.payment_utils import validate_tranfer
from tu_entrega_app.utils.whatsapp_help import get_whatsapp_reload_text
from tu_entrega_app.connectors.discord_connector import DiscordConnector
logger = logging.getLogger('django')


class PaymentService:

    @staticmethod
    def process_recharge(request):

        try:
            admin = User.objects.get(id = request.user.id, is_superuser = True)
        except:
            return Response(data={"detail": "No tienes permisos para realizar esta operación."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = User.objects.get(id=request.data["user_id"])
        except:
            return Response(data={"detail": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        recharged_coins = request.data.get("amount", 0)
        if Decimal(recharged_coins) <= 0:
            return Response(data={"detail": "El monto a recargar debe ser mayor que 0."}, status=status.HTTP_409_CONFLICT)

        user.coins += Decimal(recharged_coins)
        user.save(update_fields=["coins"])

        payment_method = request.data.get('paymentmethod', None)
        if payment_method:
            paymentmethod = ApiConstants.Payment_Method.from_string(payment_method)
        else:
            paymentmethod = ApiConstants.Payment_Method.EFECTIVO.value[0]

        payment = Payment.objects.create(
            user = user,
            amount = Decimal(recharged_coins),
            paymentmethod = paymentmethod,
            paid_time = datetime.now(),
            currency = ApiConstants.Currency.CUP_CURRENCY.value[0]
        )
        payment_status = Status_Payment.objects.create(status = ApiConstants.PaymentStatus.Payment_PAID.value[0])
        payment.status_list.add(payment_status)
        
        transaction = create_reload_transactions(
            to_user=user, amount=Decimal(recharged_coins), status=ApiConstants.TransactionStatus.TRANSACTION_COMPLETED.value[0], 
            admin=admin,
            payment=payment
            )        

        DiscordConnector.send_event(
            ApiConstants.AdminNotifyEvents.ADMIN_EVENT_NEW_RELOAD.key,
            {
                'player': user.phone,
                "amount": str(recharged_coins),
                "pay": str(recharged_coins),
                "paymentmethod": request.data.get('paymentmethod', None),
                'admin': user.name
            }
        )

        body_text = f"Usted ha recargado su cuenta en Tu Entrega con {recharged_coins} pesos."
        if user.name:
            body_text = f"{user.name} usted ha recargado su cuenta en Tu Entrega con {recharged_coins} pesos."
        
        FCM_NOTIFICATION.send_fcm_message(
            user = user,
            title = "Nueva Recarga",
            body = body_text,
            data={
                "transaction_id" : transaction.id
            }
            )

        return Response({
                        'user': user.name,
                        "amount": str(recharged_coins),
                        "pay": request.data["amount"],
                        "paymentmethod": request.data.get('paymentmethod', " "),  
                         }, status=status.HTTP_200_OK)
    
    @staticmethod
    def process_request_recharge(request):
        try:
            player = User.objects.get(id=request.user.id)
        except:
            return Response(data={"detail":"Debe autenticarse."}, status=status.HTTP_401_UNAUTHORIZED)
        
        if player.is_block:
            return Response(data={"detail":'El usuario esta bloqueado, contacta a los administradores.'}, status=status.HTTP_409_CONFLICT)
        
        min_20 = datetime.now() - timedelta(minutes=20)
        
        transactions = Transaction.objects.filter(
            to_user__id=player.id, type=ApiConstants.TransactionType.TRANSACTION_RELOAD.value[0]
        ).annotate(
            latest_status_name=Subquery(
                Status_Transaction.objects.filter(status_transaction=OuterRef('pk')
        ).order_by('-created_at').values('status')[:1])
        ).filter(
            latest_status_name__in=[ApiConstants.TransactionStatus.TRANSACTION_PENDING.value[0], ApiConstants.TransactionStatus.TRANSACTION_IN_PROCESS.value[0]]
            ).filter(time__gte = min_20).order_by("-time")
        
        transactions_exist = transactions.exists()    
        print("transactions_exist: ", transactions_exist)
        send_request = False
        if not transactions_exist:
            
            transaction_id= shortuuid.random(length=6)

            payment_method = ApiConstants.Payment_Method.EFECTIVO.value[0]
            if request.data.get('paymentmethod', None):
                payment_method = ApiConstants.Payment_Method.from_string(request.data.get('paymentmethod', None))

            whatsapp_url = get_whatsapp_reload_text(
                player= player,
                amount= float(request.data["amount"]),
                transaction_id= transaction_id,
                player_phone= player.phone,
                paymentmethod= payment_method
            )

            payment = Payment.objects.create(
                user = player,
                amount = float(request.data["amount"]),
                external_id = transaction_id,
                paymentmethod = payment_method
            )
            payment_status = Status_Payment.objects.create(status=ApiConstants.PaymentStatus.Payment_PENDING.value[0])
            payment.status_list.add(payment_status)

            new_transaction = create_reload_transactions(
                to_user=player, amount=float(request.data["amount"]),
                external_id=transaction_id,
                whatsapp_url=whatsapp_url,
                payment= payment
                )
            if not new_transaction:
                return Response({"detail":'Tu solicitud no se pudo procesar. Vuelva a intentar.'}, status=status.HTTP_409_CONFLICT)
            
            body_text = f"El usuario {player.phone} solicita recargar {request.data['amount']} pesos 💰."
            if player.name:
                body_text = f"{player.name} solicita recargar {request.data['amount']} pesos 💰."
            admins_id = User.objects.filter(is_staff=True).values_list('id', flat=True)
            FCM_NOTIFICATION.send_fcm_message_by_users_list(
                users = admins_id,
                title = "🚨Solicitud de Recarga🚨",
                body = body_text,
                data= {
                    "transaction_id" : new_transaction.id 
                }
                )
            send_request = True
        
        if send_request or transactions_exist:            
            return Response({
                "transaction_id": transaction_id if send_request else transactions.first().external_id
            }, status=status.HTTP_200_OK)

        return Response({"detail":'Tu solicitud no se pudo procesar. Vuelva a intentar.'}, status=status.HTTP_409_CONFLICT)
    
    @staticmethod
    def process_promotions(request):

        try:
            admin = User.objects.get(id = request.user.id, is_superuser = True)
        except:
            return Response(data={"detail": "No tienes permisos para realizar esta operación."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = User.objects.get(id=request.data["user_id"])
        except:
            return Response(data={"detail": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        user.coins += float(request.data["amount"])
        user.save(update_fields=["coins"])
        
        create_promotion_transactions(
            amount= float(request.data["amount"]),
            to_user= user,
            status=ApiConstants.TransactionStatus.TRANSACTION_COMPLETED.value[0],
            admin=admin
        )
                
        DiscordConnector.send_event(
            "Promoción",
            {
                'user': user.name if user.name else user.phone,
                "amount": request.data["amount"],
                'admin': admin.name
            }
        )
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @staticmethod
    def process_extract(request):

        try:
            admin = User.objects.get(id = request.user.id, is_superuser = True)
        except:
            return Response(data={"detail": "No tienes permisos para realizar esta operación."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = User.objects.get(id=request.data["user_id"])
        except:
            return Response(data={"detail": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        
        if user.coins < Decimal(request.data["amount"]):
            return Response(data={"detail":"Este usuario no tiene suficiente dinero"}, status=status.HTTP_409_CONFLICT)
       
    
        user.coins -= Decimal(request.data["amount"])
        user.save(update_fields=['coins'])
        
        create_transactions(
            from_user=user, amount=Decimal(request.data["amount"]), 
            status=ApiConstants.TransactionStatus.TRANSACTION_COMPLETED.value[0],
            type= ApiConstants.TransactionType.TRANSACTION_EXTRACTION.value[0],
            admin=admin
        )
        
        DiscordConnector.send_event(
            "New Extraction",
            {
                'player': user.name if user.name else user.phone,
                "amount": request.data["amount"],
                'admin': admin.name
            }
        )
             
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def process_transfer(request):

        try:
            from_user = User.objects.get(id = request.user.id)
        except:
            return Response(data={"detail": "No tienes permisos para realizar esta operación."}, status=status.HTTP_401_UNAUTHORIZED)

        transfer_coins = Decimal(request.data["amount"])
        try:
            to_user = User.objects.get(id=request.data["user_id"])
        except:
            return Response(data={"detail": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        
        if from_user.is_block or to_user.is_block:
            return Response(data={"detail":'El usuario esta bloqueado, contacta a los administradores.'}, status=status.HTTP_409_CONFLICT)
        
        # if not to_user.have_recharge:
        #     return Response(data={"detail":'El usuario debe recargar su cuenta primero, contacta a los administradores.'}, status=status.HTTP_403_FORBIDDEN)
        
        check, message = validate_tranfer(from_user, to_user, transfer_coins)
        if not check:
            return Response(data={"detail":message}, status=status.HTTP_409_CONFLICT)

        TRANSFER_PERCENT = os.getenv("TRANSFER_PERCENT", 0)
        bank_amount = Decimal(transfer_coins*int(TRANSFER_PERCENT)/100)
        transfer_amount = transfer_coins + bank_amount
        if from_user.coins< transfer_amount:
            return Response(data={"detail":"No tienes suficiente dinero para realizar esta operación."}, status=status.HTTP_409_CONFLICT)
        
        PaymentService.make_transfer(from_user, to_user, transfer_coins, transfer_amount)

        create_transfer_transactions(
            amount= transfer_coins,
            to_user=to_user, 
            status=ApiConstants.TransactionStatus.TRANSACTION_COMPLETED.value[0],
            descriptions= f"El player {from_user.name if from_user.name else from_user.phone} le ha realizado una transferencia de {transfer_coins} pesos."
            )

        body_text= f"Usted ha recibido una transferencia de {transfer_coins} pesos." 
        if to_user.name:
            f"{to_user.name} usted ha recibido una transferencia de {transfer_coins} pesos."
        
        FCM_NOTIFICATION.send_fcm_message(
            user = to_user,
            title = "Transferencia realizada",
            body = body_text
            )

        create_transfer_transactions(
            amount= transfer_amount,
            from_user=from_user, 
            status=ApiConstants.TransactionStatus.TRANSACTION_COMPLETED.value[0],
            descriptions= f"Le ha realizado una transferencia de {transfer_coins} pesos a {to_user.name if to_user.name else to_user.phone}."
            )
        usuario_text = f"de telefono {to_user.phone}"
        if to_user.name:
            usuario_text = f"{to_user.name}"
        body_text = f"Usted ha realizado una transferencia de {transfer_coins} pesos al usuario {usuario_text}. Se le descontó de su saldo {transfer_amount} pesos."
        if from_user.name:
            body_text= f"{from_user.name} usted ha realizado una transferencia de {transfer_coins} pesos al usuario {usuario_text}. Se le descontó de su saldo {transfer_amount} pesos."
        FCM_NOTIFICATION.send_fcm_message(
            user = from_user,
            title = "Transferencia realizada",
            body = body_text
            )
                
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @staticmethod
    def make_transfer(from_user: User, to_user: User, coins_to_transfer: Decimal, transfer_amount: Decimal):
        
        to_user.coins += coins_to_transfer
        to_user.save(update_fields=["coins"])
        
        from_user.coins -= transfer_amount
        from_user.save(update_fields=['coins'])
                
        return

    @staticmethod
    def process_select(request, transactions_id):
        try:
            admin = User.objects.get(id = request.user.id, is_staff=True)
        except:
            return Response({'detail': "No tienes permisos para realizar esta operación."}, status=status.HTTP_401_UNAUTHORIZED) 
        
        try:
            transaction = Transaction.objects.get(id = transactions_id)
        except:
            return Response({'detail': "Solicitud no encontrada"}, status=status.HTTP_404_NOT_FOUND) 
    
        if transaction.status_int != ApiConstants.TransactionStatus.TRANSACTION_PENDING.value[0] or transaction.type in [ApiConstants.TransactionType.TRANSACTION_PROMOTION.value[0], ApiConstants.TransactionType.TRANSACTION_TRANSFER.value[0], ApiConstants.TransactionType.TRANSACTION_TRIP.value[0], ApiConstants.TransactionType.TRANSACTION_EXTRACTION.value[0]]:
            return Response({'detail': "Esta solicitud no esta disponible."}, status=status.HTTP_409_CONFLICT)
        
        if transaction.from_user and int(transaction.amount) > float(transaction.from_user.coins):
            return Response(data={"detail":"Este player no tiene suficientes monedas"}, status=status.HTTP_409_CONFLICT)
        
        if transaction.admin is not None and not admin.user.is_superuser and transaction.admin.id != admin.id:
            return Response({'detail': "Esta transacción ya fue seleccionada por otro administrador."}, status=status.HTTP_409_CONFLICT)
       

        transaction.admin = admin
        transaction.save(update_fields=['admin'])
        
        new_status = Status_Transaction.objects.create(status = ApiConstants.TransactionStatus.TRANSACTION_IN_PROCESS.value[0])
        transaction.status_list.add(new_status)
              
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @staticmethod
    def reload_coins(transaction: Transaction):
        
        user = transaction.to_user
        
        recharged_coins = transaction.amount
        
        user.coins+= recharged_coins
        user.save(update_fields=["coins"])

        body_text = f"Usted ha recargado su cuenta con {recharged_coins} pesos."
        if user.name:
            body_text = f"{user.name} usted ha recargado su cuenta con {recharged_coins} pesos."

        FCM_NOTIFICATION.send_fcm_message(
            user = user,
            title = "Nueva Recarga",
            body = body_text
            )
        DiscordConnector.send_event(
            ApiConstants.AdminNotifyEvents.ADMIN_EVENT_NEW_RELOAD.key,
            {
                'player': user.phone,
                "amount": recharged_coins,
                "pay": transaction.amount,
                "paymentmethod": transaction.payment.paymentmethod if transaction.payment else None,
                'admin': transaction.admin.name if transaction.admin else None
            }
        )
        return recharged_coins
    
    @staticmethod
    def extractions_coins(transaction: Transaction):
        
        user = transaction.from_user
        
        user.coins -= transaction.amount
        user.save(update_fields=['coins'])
       
        DiscordConnector.send_event(
            "Extración Realizada",
            {
                'player': user.phone,
                "amount": transaction.amount,
                'admin': transaction.admin.name if transaction.admin else None
            }
        )
    
    @staticmethod
    def process_confirm(request, transactions_id):

        try:
            admin = User.objects.get(id = request.user.id, is_staff=True)
        except:
            return Response({'detail': "No tienes permisos para realizar esta operación."}, status=status.HTTP_401_UNAUTHORIZED) 

        try:
            transaction = Transaction.objects.get(id = transactions_id)
        except:
            return Response({'detail': "Solicitud no encontrada"}, status=status.HTTP_404_NOT_FOUND) 
    
        if transaction.status_int != ApiConstants.TransactionStatus.TRANSACTION_IN_PROCESS.value[0] or transaction.type in [ApiConstants.TransactionType.TRANSACTION_PROMOTION.value[0], ApiConstants.TransactionType.TRANSACTION_TRANSFER.value[0], ApiConstants.TransactionType.TRANSACTION_TRIP.value[0], ApiConstants.TransactionType.TRANSACTION_EXTRACTION.value[0]]:
            return Response({'detail': "Esta solicitud no esta disponible."}, status=status.HTTP_409_CONFLICT)
        
        if transaction.from_user and float(transaction.amount) > float(transaction.from_user.coins):
            return Response(data={"detail":"Este usuario no tiene suficientes monedas."}, status=status.HTTP_409_CONFLICT)
        
        
        if transaction.type == ApiConstants.TransactionType.TRANSACTION_RELOAD.value[0]:
            transaction.admin = admin
            transaction.save(update_fields=['admin'])
            
            new_status = Status_Transaction.objects.create(status = ApiConstants.TransactionStatus.TRANSACTION_COMPLETED.value[0])
            transaction.status_list.add(new_status)

            payment = transaction.payment
            if not payment:
                payment = Payment.objects.create(
                    external_id = transaction.external_id,
                    user = transaction.to_user,
                    amount = transaction.amount
                )
                transaction.payment = payment                
                transaction.save(update_fields=["payment"])

            payment_status = Status_Payment.objects.create(status = ApiConstants.PaymentStatus.Payment_PAID.value[0])
            payment.status_list.add(payment_status)             
            payment.paid_time = datetime.now()
            payment.save(update_fields=["paid_time"])

            recharged_coins = PaymentService.reload_coins(transaction)
        
            transaction.amount = Decimal(recharged_coins)
            transaction.save(update_fields=["amount"])

            return Response({
                    'player': transaction.to_user.name,
                    "amount": str(transaction.amount),
                    "pay": str(payment.amount),
                    "paymentmethod": transaction.payment.paymentmethod_str,
                }, status=status.HTTP_200_OK)
        else:
            return Response({"detail":'No esta disponible. Contacta algun administrador.'}, status=status.HTTP_409_CONFLICT)
        
    @staticmethod
    def process_cancel(request, transactions_id):
        try:
            cancel_by = User.objects.get(id = request.user.id)
        except:
            return Response({'detail': "Fayó la autenticacion, vuelva a intentarlo."}, status=status.HTTP_401_UNAUTHORIZED) 
        
        try:
            transaction = Transaction.objects.get(id = transactions_id)
        except:
            return Response({'detail': "Solicitud no encontrada"}, status=status.HTTP_404_NOT_FOUND) 
    
        if transaction.status_int in [ApiConstants.TransactionStatus.TRANSACTION_COMPLETED.value[0], ApiConstants.TransactionStatus.TRANSACTION_CANCELED.value[0]] or transaction.type in [ApiConstants.TransactionType.TRANSACTION_PROMOTION.value[0], ApiConstants.TransactionType.TRANSACTION_TRANSFER.value[0], ApiConstants.TransactionType.TRANSACTION_TRIP.value[0], ApiConstants.TransactionType.TRANSACTION_EXTRACTION.value[0]] or (not request.user.is_staff and transaction.status_int == ApiConstants.TransactionStatus.TRANSACTION_IN_PROCESS.value[0]):
            return Response({'status': 'error', 'message': "Esta solicitud no esta disponible."}, status=status.HTTP_409_CONFLICT)
        
        
        transaction.admin = cancel_by
        transaction.save(update_fields=['admin'])
        
        new_status = Status_Transaction.objects.create(status = ApiConstants.TransactionStatus.TRANSACTION_CANCELED.value[0])
        transaction.status_list.add(new_status)
                
        return Response(status=status.HTTP_204_NO_CONTENT)
    