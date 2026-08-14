from tu_entrega_app.models import User, Status_Transaction, Transaction
from tu_entrega_app.utils.constants import ApiConstants
import logging
logger = logging.getLogger('django')
logger_api = logging.getLogger(__name__)

def create_transactions(amount, type, from_user:User=None, to_user:User=None, status=None, descriptions=None, admin:User=None):
    
    try:
        if not from_user and not to_user:
            logger.error(f"Transaction of {amount} pesos failed of {from_user} for {to_user}, error: At least one of the from_user or to_user fields should not be empty")
            return None    
        if not amount>0:
            logger.error(f"Transaction of {amount} pesos failed of {from_user} for {to_user}, error: The amount must greater than 0")
            return None
        if not status in [value[0] for value in ApiConstants.TransactionStatus.choices()]:
            logger.error(f"Transaction of {amount} pesos failed of {from_user} for {to_user}, error: status is not correct")
            return None
        if not type in [value[0] for value in ApiConstants.TransactionType.choices()]:
            logger.error(f"Transaction of {amount} pesos failed of {from_user} for {to_user}, error: type is not correct")
            return None
        
        new_status = Status_Transaction.objects.create(status = ApiConstants.TransactionStatus.TRANSACTION_PENDING.value[0] if status==None else status)
        new_transaction = Transaction.objects.create(
            from_user = from_user if from_user else None,
            to_user = to_user if to_user else None,
            amount = amount,
            type=type,
            descriptions = descriptions if descriptions else None,
            admin = admin if admin else None
        )
        
        new_transaction.status_list.add(new_status)
        
        logger_api.info(f"Transaction of {amount} pesos satisfactory of {from_user} for {to_user}")
        return new_transaction
    except Exception as e:
        print(f"error: {e}")
        logger.critical(f"Transaction of {amount} pesos failed of {from_user} for {to_user}, error: {e}")
        return None

def create_reload_transactions(amount, from_user:User=None, to_user:User=None, status=None, admin:User=None, external_id=None, payment=None, descriptions=None, whatsapp_url=None):
    if not from_user and not to_user:
        logger.error(f"Transaction of {amount} pesos failed of {from_user} for {to_user}, error: At least one of the from_user or to_user fields should not be empty")
        return None    
    if not  amount>0:
        logger.error(f"Transaction of {amount} pesos failed of {from_user} for {to_user}, error: The amount must greater than 0")
        return None
    
    if status and not status in [value[0] for value in ApiConstants.TransactionStatus.choices()]:
        logger.error(f"Transaction of {amount} pesos failed of {from_user} for {to_user}, error: status is not correct")
        return None
    
    try:        
        new_status = Status_Transaction.objects.create(status = ApiConstants.TransactionStatus.TRANSACTION_PENDING.value[0] if status==None else status)
        new_transaction = Transaction.objects.create(
            from_user = from_user if from_user else None,
            to_user = to_user if to_user else None,
            amount = amount,
            type=ApiConstants.TransactionType.TRANSACTION_RELOAD.value[0], 
            admin = admin if admin else None,
            external_id = external_id if external_id else None,
            payment = payment if payment else None,
            descriptions = descriptions if descriptions else None,
            whatsapp_url = whatsapp_url if whatsapp_url else None
        )
        
        new_transaction.status_list.add(new_status)
    
        logger_api.info(f"Transaction of {amount} pesos satisfactory of {from_user} for {to_user}")
        return new_transaction
    except Exception as e:
        print("error: ", str(e))
        logger.critical(f"Transaction of {amount} pesos failed of {from_user} for {to_user}, error: {e}")
        return None
    
def create_promotion_transactions(amount, from_user:User=None, to_user:User=None, status=None, admin:User=None, descriptions=None):
    
    try:
        if not from_user and not to_user:
            logger.error(f"Transaction of {amount} pesos failed of {from_user} for {to_user}, error: At least one of the from_user or to_user fields should not be empty")
            return False    
        if not  amount>0:
            logger.error(f"Transaction of {amount} pesos failed of {from_user} for {to_user}, error: The amount must greater than 0")
            return False
        if not status in [value[0] for value in ApiConstants.TransactionStatus.choices()]:
            logger.error(f"Transaction of {amount} pesos failed of {from_user} for {to_user}, error: status is not correct")
            return False
        
        new_status = Status_Transaction.objects.create(status = ApiConstants.TransactionStatus.TRANSACTION_PENDING.value[0] if status==None else status)
        new_transaction = Transaction.objects.create(
            from_user = from_user if from_user else None,
            to_user = to_user if to_user else None,
            amount = amount,
            type=ApiConstants.TransactionType.TRANSACTION_PROMOTION.value[0], 
            admin = admin if admin else None,
            descriptions = descriptions if descriptions else None
        )
        
        new_transaction.status_list.add(new_status)
    
        logger_api.info(f"Promotion of {amount} pesos satisfactory for {to_user} make a refer to {from_user}.")
        return True
    except Exception as e:
        logger.critical(f"Promotion of {amount} pesos failed of {from_user} for {to_user}, error: {e}")
        return False

def create_transfer_transactions(amount, from_user:User=None, to_user:User=None, status=None, descriptions=None):
    
    try:
        if not from_user and not to_user:
            logger.error(f"Transaction of {amount} pesos failed of {from_user} for {to_user}, error: At least one of the from_user or to_user fields should not be empty")
            return False    
        if not  amount>0:
            logger.error(f"Transaction of {amount} pesos failed of {from_user} for {to_user}, error: The amount must greater than 0")
            return False
        if not status in [value[0] for value in ApiConstants.TransactionStatus.choices()]:
            logger.error(f"Transaction of {amount} pesos failed of {from_user} for {to_user}, error: status is not correct")
            return False
        
        new_status = Status_Transaction.objects.create(status = ApiConstants.TransactionStatus.TRANSACTION_PENDING.value[0] if status==None else status)
        new_transaction = Transaction.objects.create(
            from_user = from_user if from_user else None,
            to_user = to_user if to_user else None,
            amount = amount,
            type=ApiConstants.TransactionType.TRANSACTION_TRANSFER.value[0], 
            descriptions = descriptions if descriptions else None            
        )
        
        new_transaction.status_list.add(new_status)
    
        logger_api.info(f"Transaction of {amount} pesos satisfactory of {from_user} for {to_user}")
        return True
    except Exception as e:
        print(f"error: {e}")
        logger.critical(f"Transaction of {amount} pesos failed of {from_user} for {to_user}, error: {e}")
        return False
 