import os
from datetime import datetime
from decimal import Decimal
from tu_entrega_app.models import User, Transaction
from tu_entrega_app.utils.constants import ApiConstants

def validate_tranfer(from_user: User, to_user: User, amount:Decimal):
    """Verificar si se puede hacer la transferencia o no. Requisitos:\n
    1- El maximo a transferir es de 500 pesos.\n
    2- El minimo a transferir es de 20 pesos.\n
    3- to_user no puede tener mas de 100 pesos.\n
    4- El Maximo de transferencias en un dia es 2.
    
    
    Args:
        from_user (Player): PLayer que envia el dinero
        to_user (Player): PLayer que recive el dinero
        amount (int): Cantidad de monedas a transferir

    Returns:
        _type_: Tuple[bool, str]
    """
    MIN_TRANSFER = os.getenv("MIN_TRANSFER",20)
    MAX_TRANSFER = os.getenv("MAX_TRANSFER", 500)
    TRANSFER_PER_DAY = os.getenv("TRANSFER_PER_DAY", 2)
    TO_USER_COINS_TRANSFER = os.getenv("TO_USER_COINS_TRANSFER", 100)
    
    
    if to_user.coins > int(TO_USER_COINS_TRANSFER):
        return False, f"Al usuario que intentas transferir tinene más de {TO_USER_COINS_TRANSFER} pesos en su cuenta."
    
    if amount< int(MIN_TRANSFER):
        return False, f"La transferencia debe ser superior a {MIN_TRANSFER} pesos."
    
    if amount> int(MAX_TRANSFER):
        return False, f"La transferencia no puede exceder los {MAX_TRANSFER} pesos."
    
    to_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    total_transaction = Transaction.objects.filter(from_user__id = from_user.id, type=ApiConstants.TransactionType.TRANSACTION_TRANSFER.value[0], time__gte = to_day).count()
    
    if total_transaction >= int(TRANSFER_PER_DAY):
        return False, f"Haz excedido el máximo de {TRANSFER_PER_DAY} transferencias por día."
    
    return True, None