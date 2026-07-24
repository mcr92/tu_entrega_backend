import os
from enum import Enum

__all__ = ['ApiError', 'ApiConstants']

class ApiError(Enum):
    def __init__(self, value, description=''):
        self._value_ = value
        self.description = description

    # AUTH
    CODE_INVALID_TOKEN = ('invalid_token', 'The token is invalid.')
    CODE_INVALID_CREDENTIALS = ('invalid_credentials', 'Credentials are invalid.')
    CODE_REQUIRE_ACTIVATION = ('require_activation', 'The activation of the resource is mandatory.')
    CODE_AUTHENTICATION_FAILED = ('bad_credentials', 'Invalid credentials.')
    # DATABASE
    CODE_NOT_FOUND = ('not_found', 'Resource not found.')
    CODE_HAS_ALREADY = ('already_have_resource', 'The target entity already has the resource.')
    CODE_MULTI_ROW = ('multi_row', 'The target entity has more than one object.')
    CODE_ROW_EXISTS = ('row_exists', 'There is already a row with that value.')
    CODE_ROW_DEPENDENCY = ('row_dependency', 'The resource can not be deleted due objects dependency..')
    CODE_CONFIGURATION_NEEDED = ('configuration_needed', 'Configuration is needed for this endpoint.')
    # FIELDS
    CODE_MISSING_PARAM = ('missing_param', 'Required param was not present in the request.')
    CODE_FORBIDDEN_EMPTY_REQUEST = ('forbidden_empty_request', 'Empty request is not allowed.')
    CODE_UNRECOGNIZED_PARAMETER = ('unrecognized_parameter', 'Parameter not recognized.')
    CODE_INVALID_PARAM = ('invalid_param', 'El parámentro tiene un valor incorrecto')
    # EXCEPTIONS
    CODE_INTERNAL_ERROR = ('internal_error', 'Opps something went wrong.')
    CODE_DENIED_PARAM = ('denied_param', 'Resource has unprocessable status.')
    CODE_ACCOUNT_SUSPENDED = ('account_suspended', 'The account is suspended.')
    CODE_SERVICE_SUSPENDED = ('service_suspended', 'The service is suspended.')
    CODE_SERVICE_NOT_VERIFIED = ('service_not_verified', 'The service is not verified.')
    CODE_SERVICE_UNAVAILABLE = ('service_unavailable', 'The endpoint depends of external services who failed.')
    CODE_FORBIDDEN_RESOURCE = ('forbidden_resource', 'User can not access to this resource.')
    CODE_NEXT_PLAN_WAITING = ('next_plan_waiting', 'Next plan will start at the end of current period.')
    CODE_PAYMENT_NOT_REQUIRED = ('payment_not_required', 'Payment is not required after this operation.')
    CODE_PAYMENT_REQUIRED = ('payment_required', 'Payment is not required after this operation.')
    CODE_PLAN_DENIED = ('plan_denied', 'Your plan is too low for this operation.')
    CODE_INSUFFICIENT_BALANCE = ('balance_insufficient', 'You have insufficient funds in your Balance for this transfer.')
    CODE_PRECONDITION_REQUIRED = ('precondition_required', 'Request can not continue due important precondition is required and not meet.')
    CODE_NOT_IMPLEMENTED = ('not_implemented', 'This functionality is not yet implemented.')
    # SUBSCRIPTION
    CODE_NON_UPGRADABLE = ('non_upgradable', 'You can not upgrade to that resource.')
    CODE_NON_PROCESSABLE = ('non_processable', 'You can not process to that resource.')


class EnumBehavior:
    @staticmethod
    def set_enum(cls):
        setattr(cls, "text", classmethod(EnumBehavior.choices))
        setattr(cls, "choices", classmethod(EnumBehavior.choices))
        setattr(cls, "items", classmethod(EnumBehavior.items))
        setattr(cls, "get", classmethod(EnumBehavior.get))
        setattr(cls, "from_string", classmethod(EnumBehavior.from_string))

        for name, member in cls.__members__.items():
            setattr(member, 'text', member.value[1])
            setattr(member, 'key', member.value[0])

        return cls

    @staticmethod
    def from_string(cls, text):
        for member in cls:
            if member.value[1] == text:
                return member.value[0]
        raise ValueError(f"{text} is not a valid {cls.__name__} value")

    @staticmethod
    def get(cls, value):
        for member in cls:
            if member.value[0] == value:
                return member.value[1]
        raise ValueError(f"{value} is not a valid text for {cls.__name__}")

    @staticmethod
    def choices(cls):
        return [(member.value[0], member.value[1]) for member in cls]
    
    @staticmethod
    def items(cls):
        return [member.value[1] for member in cls]

class LanguagesSupported(Enum):
    SPANISH =  'es', 'es'
    ENGLISH =  'en', 'en'

class AdminNotifyEvents(Enum):
    ADMIN_EVENT_NEW_USER = 'new_user', 'New user'
    ADMIN_EVENT_NEW_RELOAD = ('new_reload', 'New Reload')

class Currency(Enum):
    USD_CURRENCY = 1, 'USD'
    CUP_CURRENCY = 2 , 'CUP'

class Payment_Method(Enum):
    EFECTIVO = 1, 'Efectivo'
    TRANSFERENCIA = 2 , 'CUP'

class ApiConstants:
    DEFAULT_CURRENCY = 'usd'
    DEFAULT_LANGUAGE = 'es'
    # ADMIN_PHONE = os.getenv("ADMIN_PHONE")
    # URL_FACEBOOK = os.getenv("URL_FACEBOOK")
    # URL_TELEGRAM = os.getenv("URL_TELEGRAM")
    # URL_WHATSAPP = os.getenv("URL_WHATSAPP")
    # ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
    AdminNotifyEvents = EnumBehavior.set_enum(AdminNotifyEvents)
    Currency = EnumBehavior.set_enum(Currency)
    Payment_Method = EnumBehavior.set_enum(Payment_Method)