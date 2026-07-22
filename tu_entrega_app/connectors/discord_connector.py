import logging
import os
import requests
from tu_entrega_app.utils.constants import ApiConstants
import urllib.parse


class DiscordConnector:
    errors_url = os.environ.get('DISCORD_ERRORS_URL', '')
    events_url = os.environ.get('DISCORD_EVENTS_URL', '')
    environment = (os.environ.get('PRODUCTION', "True")=="True")
    
    @staticmethod
    def _make_request(url, payload):
        logger = logging.getLogger(__name__)
        try:
            res = requests.post(url, json=payload)
            if res.status_code != 204:
                logger.error(f'Failed to send message to Discord with status {res.status_code}. Payload: {payload}')
                return False
            return True
        except requests.RequestException as e:
            logger.error(f'DiscordConnector => {str(e)}')
            return False

    @staticmethod
    def send_error(message):
        if DiscordConnector.errors_url:
            start = "### 🚨 Oops! Something went wrong. 🚨\n```bash\n"
            end = "```"
            max_length = 2000 - (len(start) + len(end))
            content = message if len(message) <= max_length else f'{message[:max_length - 4]}\n...'

            payload = {
                "username": f'BACKEND API ({"Production" if DiscordConnector.environment else "Development"})',
                "content": f'{start}{content}{end}',
                "allowed_mentions": {"parse": ["everyone"]}
            }

            DiscordConnector._make_request(DiscordConnector.errors_url, payload)

    @staticmethod
    def send_event(event_type, params):
        if DiscordConnector.events_url:
            if event_type == ApiConstants.AdminNotifyEvents.ADMIN_EVENT_NEW_USER.key:
                content = f"🎉 New User Alert! 🎉 \n We have a new user: {params.get('phone')}!"
            elif event_type == ApiConstants.AdminNotifyEvents.ADMIN_EVENT_NEW_RELOAD.key:
                content = f"🎉 Nueva Recarga, Alerta! 🎉 \n Hemos recibido una recarga de {params.get('player')} con un monto de {params.get('amount')} pesos!\n  Administrador: {params.get('admin')}"
            else:
                content = f"🚨 New Event! 🚨 Type: {event_type} - Details: {params}"

            payload = {
                "username": f'Tu Entrega ({"Production" if DiscordConnector.environment else "Development"})',
                "content": content,
                "allowed_mentions": {"parse": ["everyone"]}
            }

            DiscordConnector._make_request(DiscordConnector.events_url, payload)
            
    
    