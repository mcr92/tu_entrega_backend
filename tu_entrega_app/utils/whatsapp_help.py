import urllib.parse
from tu_entrega_app.models import User

def get_whatsapp_reload_text(player: User, amount: float, transaction_id:str, player_phone:str, paymentmethod:str=None):
    texto_original = f"""
    Hola *{player.name}*, tu solicitud de recarga de {amount} pesos para la cuenta **{player.phone}** fue recibida.
    """
    if paymentmethod:
        if paymentmethod == "efectivo":
            method = "💵 Efectivo"
        else:
            method = "💳 Transferencia Bancaria"
            
        texto_original += f"""
    Metodo de Pago: {method}
    """
    else:
        texto_original += f"""
Por favor, elige tu método de pago:
    💵 Efectivo
    💳 Transferencia Bancaria
    """
    texto_original += f"""
    *ID de tu solicitud*: {transaction_id}
¿Le envío los datos?
    """
    
    texto_codificado = urllib.parse.quote(texto_original)
    
    return f"https://wa.me/{player_phone}/?text={texto_codificado}"
