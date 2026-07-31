import base64
import datetime
import os
import re
import uuid
from http import HTTPStatus

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.core.validators import URLValidator, EmailValidator
from django.http import JsonResponse, QueryDict, HttpResponse

from tu_entrega_app.utils.constants import ApiError


class ApiResponse:
    def __new__(cls, data=None, status_code=HTTPStatus.OK):
        if status_code == HTTPStatus.NO_CONTENT:
            return HttpResponse(status=status_code)
        if data is None:
            data = None
        return JsonResponse(data=data, status=status_code, safe=False)


class ErrorResponse(JsonResponse):
    def __init__(self, http_code=None, internal_code=None, message=None, field=None):
        http_code = http_code or HTTPStatus.INTERNAL_SERVER_ERROR.value
        error_response_data = {
            'code': internal_code or ApiError.CODE_INTERNAL_ERROR.value,
            'detail': message or ApiError.CODE_INTERNAL_ERROR.description,
            'param': field or '',
        }
        super().__init__(error_response_data, status=http_code)
        self.internal_code = internal_code
        self.message = message
        self.field = field


class RequestValidator:

    def __init__(self, request, allow_empty, required_keys, validators, basic_auth = False):
        self.request = request
        self.is_valid = True
        self.error_response = ErrorResponse()
        params = {}
        if isinstance(request.query_params, QueryDict):
            params.update(self.query_to_dict(request.query_params))
        if isinstance(request.data, (QueryDict, dict)):
            params.update(self.query_to_dict(request.data) if isinstance(request.data, QueryDict) else request.data)
        if hasattr(request, 'FILES'):
            for key, files in request.FILES.lists():
                is_list_key = key.endswith('[]')
                normalized_key = key.rstrip('[]')
                if is_list_key:
                    params[normalized_key] = files
                else:
                    params[normalized_key] = files[0]

        self.params = self.normalize_keys(params)
        request.data_sent = self.params
        self._basic_auth = basic_auth
        self._allow_empty = allow_empty
        self._required_keys = required_keys or {}
        self._validators = validators or {}
        self.validate()

    @staticmethod
    def normalize_keys(params):
        normalized_params = {}
        for key, value in params.items():
            is_list_key = key.endswith('[]')
            normalized_key = key.rstrip('[]')
            if is_list_key and not isinstance(value, list):
                value = [value]
            normalized_params[normalized_key] = value
        return normalized_params

    @staticmethod
    def query_to_dict(query_dict):
        result = {}
        for key, value_list in query_dict.lists():
            if len(value_list) == 1:
                result[key] = value_list[0]
            else:
                result[key] = value_list
        return result

    @staticmethod
    def _check_token(request) -> bool:
        expected_token = os.environ['EXTERNAL_API_TOKEN']
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header:
            try:
                auth_type, encoded_auth_token = auth_header.split(' ', 1)
                if auth_type.lower() != 'basic':
                    return False
                decoded_auth_token = base64.b64decode(encoded_auth_token).decode()
                if decoded_auth_token.startswith(':'):
                    decoded_auth_token = decoded_auth_token[1:]
                return decoded_auth_token == expected_token
            except ValueError:
                return False
        return False

    def validate(self):
        if self._basic_auth and not self._check_token(self.request):
            self.error_response = ErrorResponse(
                http_code=HTTPStatus.UNAUTHORIZED,
                internal_code=ApiError.CODE_AUTHENTICATION_FAILED.value,
                message=ApiError.CODE_AUTHENTICATION_FAILED.description
            )
            self.is_valid = False
            return
        if len(self.params) == 0 and not self._allow_empty:
            self.error_response = ErrorResponse(
                http_code=HTTPStatus.BAD_REQUEST,
                internal_code=ApiError.CODE_FORBIDDEN_EMPTY_REQUEST.value,
                message=ApiError.CODE_FORBIDDEN_EMPTY_REQUEST.description)
            self.is_valid = False
            return

        # check all required keys are present
        for required_key in self._required_keys:
            if required_key not in self.params:
                self.error_response = ErrorResponse(
                    http_code=HTTPStatus.BAD_REQUEST,
                    internal_code=ApiError.CODE_MISSING_PARAM.value,
                    message=ApiError.CODE_MISSING_PARAM.description,
                    field=required_key
                )
                self.is_valid = False
                break
        
        for key, validator_data in self._validators.items():
            if isinstance(validator_data, list):
                for validator_tuple in validator_data:
                    if validator_tuple == self.allow_empty_value:
                        if self.apply_validator(key, validator_tuple):
                            break
                        continue
                    if not self.apply_validator(key, validator_tuple):
                        return False
            else:
                if not self.apply_validator(key, validator_data):
                    return False
        
        # check no extra field was sent
        for param in self.params:
            if param not in self._validators:
                self.error_response = ErrorResponse(
                    http_code=HTTPStatus.BAD_REQUEST,
                    internal_code=ApiError.CODE_UNRECOGNIZED_PARAMETER.value,
                    message=ApiError.CODE_UNRECOGNIZED_PARAMETER.description,
                    field=param
                )
                self.is_valid = False
                break

    def apply_validator(self, key, validator_tuple):
        if callable(validator_tuple):
            validator, validator_args, custom_message = validator_tuple, [], None
        elif isinstance(validator_tuple, (tuple, list)) and validator_tuple and callable(validator_tuple[0]):
            validator = validator_tuple[0]
            validator_args = list(validator_tuple[1:])
            if len(validator_args) >= 2 and isinstance(validator_args[-1], str):
                custom_message = validator_args.pop()
            else:
                custom_message = None
        else:
            raise TypeError("Validator must be a callable or a tuple of (callable, *args [, optional message])")

        if key in self.params:
            validation_result = validator(self.params[key], *validator_args)

            if isinstance(validation_result, tuple):
                is_valid, error_message = validation_result
            else:
                is_valid = validation_result
                error_message = None

            if not is_valid:
                self.error_response = ErrorResponse(
                    http_code=HTTPStatus.BAD_REQUEST,
                    internal_code=ApiError.CODE_INVALID_PARAM.value,
                    message=error_message or custom_message or ApiError.CODE_INVALID_PARAM.description,
                    field=key
                )
                if validator_tuple != self.allow_empty_value:
                    self.is_valid = False
                return False

        return True

    # @staticmethod
    # def validate_currency(value):
    #     return is_currency(value.upper())
    #     return True

    @staticmethod
    def validate_string(value):
        if not isinstance(value, str):
            return False
        safe_pattern = re.compile(r'^[\w \-._ñ@*,]+$', re.UNICODE)
        if safe_pattern.match(value):
            return True
        else:
            return False

    @staticmethod
    def validate_phone_number(value):
        if not isinstance(value, str):
            return False
        safe_pattern = re.compile(r'^\+?\s*(\d\s*){8,15}$')
        if safe_pattern.match(value):
            return True
        else:
            return False

    @staticmethod
    def validate_text(value):
        if value == "":
            return True
        pattern = r'^[^\n<>]+$'
        if not isinstance(value, str):
            return False
        regex = re.compile(pattern, re.MULTILINE)
        return bool(regex.match(value))

    @staticmethod
    def allow_empty_string(value):
        return value == ""

    @staticmethod
    def allow_empty_value(value):
        return value == "" or value is None
    
    @staticmethod
    def validate_json(value):
        return isinstance(value, dict)

    @staticmethod
    def validate_password(value):
        return isinstance(value, str) and len(value) >= 8

    @staticmethod
    def validate_integer(value):
        return isinstance(value, int)

    @staticmethod
    def validate_numeric(value):
        if isinstance(value, int) and not isinstance(value, bool):
            return True
        if isinstance(value, str):
            try:
                int(value)
                return True
            except ValueError:
                return False
        return False

    @staticmethod
    def validate_range(value, min_allowed=None, max_allowed=None):
        if not RequestValidator.validate_numeric(value):
            return False, "el valor debe ser un entero"
        value = int(value)
        if min_allowed is not None and value < min_allowed:
            return False, f"El valor debe ser mayor o igual que {min_allowed}"
        if max_allowed is not None and value > max_allowed:
            return False, f"El valor debe ser menor o igual que {max_allowed}"
        return True

    # @staticmethod
    # def validate_timezone(value):
    #     try:
    #         pytz.timezone(value)
    #         return True
    #     except UnknownTimeZoneError:
    #         return False

    @staticmethod
    def validate_boolean(value):
        try:
            if isinstance(value, bool):
                return True
            if isinstance(value, str):
                value = value.strip().lower()
                if value in ["true", "false"]:
                    return True
            return False
        except ValueError:
            return False

    @staticmethod
    def validate_uuid(value):
        try:
            uuid_test = uuid.UUID(value, version=4)
            return str(uuid_test) == value
        except ValueError:
            return False

    @staticmethod
    def validate_url(value):
        url_validator = URLValidator(schemes=['http', 'https', 'ftp', 'ftps', 'trinc'])
        try:
            url_validator(value)
            return True
        except ValidationError:
            return False

    @staticmethod
    def validate_email(value):
        email_validator = EmailValidator()
        try:
            email_validator(value)
            return True
        except ValidationError:
            return False

    @staticmethod
    def validate_in_array(value, target_array):
        return value.lower() in [item[1].lower() for item in target_array]

    @staticmethod
    def validate_double(value):
        pattern = re.compile(r'^\d+(\.\d{1,2})?$')
        return bool(re.match(pattern, str(value)))

    @staticmethod
    def validate_double_range(value, min_allowed, max_allowed):
        value = float(value)
        pattern = re.compile(r'^\d+(\.\d{1,2})?$')
        if not bool(re.match(pattern, str(value))):
            return False
        return min_allowed <= value <= max_allowed
    
    @staticmethod
    def validate_decimal(value):
        pattern = re.compile(r'^-?\d+(\.\d+)?$')
        return bool(re.match(pattern, str(value)))

    @staticmethod
    def validate_list_length(value, min_length=None, max_length=None):
        if not isinstance(value, list):
            return False, "El valor debe ser una lista"
        if min_length is not None and len(value) < min_length:
            return False, f"La lista debe contener al menos {min_length} elementos"
        if max_length is not None and len(value) > max_length:
            return False, f"La lista no debe contener más de {max_length} elementos"
        return True

    @staticmethod
    def validate_list(element_validator):
        def validate(value):
            if not isinstance(value, list):
                return False
            return all(element_validator(item) for item in value)

        return validate

    @staticmethod
    def validate_image(value):
        if not isinstance(value, UploadedFile):
            return False

        content_type = getattr(value, 'content_type', '')
        if not content_type.startswith('image/'):
            return False
        return True

    # @staticmethod
    # def validate_country_iso2_code(code):
    #     try:
    #         return pycountry.countries.get(alpha_2=code) is not None
    #     except KeyError:
    #         return False

    @staticmethod
    def validate_min_length(value, min_length):
        if len(value) == 0:
            return True
        if not isinstance(value, str):
            return False, f"El parámetro debe ser un texto."
        if min_length is not None and len(value) < min_length:
            return False, f"El parámetro debe tener como mínimo {min_length} caracteres."
        return True

    @staticmethod
    def validate_pattern(value, pattern):
        if not isinstance(value, str):
            return False
        regex = re.compile(pattern)
        return bool(regex.match(value))

    @staticmethod
    def validate_datetime(value):
        if not isinstance(value, str):
            return False
        # Lista de formatos admitidos (en orden de prioridad)
        formats = [
            "%d-%m-%Y %H:%M:%S",  # 12-06-2025 11:47:10
            "%d-%m-%Y %H:%M",       # 12-06-2025 11:47
            "%d-%m-%Y %H",          # 12-06-2025 11
            "%d-%m-%Y",             # 12-06-2025
        ]
        for fmt in formats:
            try:
                # Convertir el string a datetime usando el formato esperado
                datetime.datetime.strptime(value, fmt)
                return True
            except ValueError as e:
                continue
        return False

    @staticmethod
    def validate_text_html(value):
        return isinstance(value, str) and len(value.strip()) > 0

    @staticmethod
    def _run_validator_callable(value, validator_tuple):
        if callable(validator_tuple):
            validator, validator_args, custom_message = validator_tuple, [], None
        elif isinstance(validator_tuple, (tuple, list)) and validator_tuple and callable(validator_tuple[0]):
            validator = validator_tuple[0]
            validator_args = list(validator_tuple[1:])
            if len(validator_args) >= 2 and isinstance(validator_args[-1], str):
                custom_message = validator_args.pop()
            else:
                custom_message = None
        else:
            raise TypeError("Validator must be a callable or a tuple of (callable, *args [, optional message])")

        result = validator(value, *validator_args)
        if isinstance(result, tuple):
            ok, msg = result
        else:
            ok, msg = bool(result), None
        return ok, (msg or custom_message)

    @staticmethod
    def validate_list_of_objects(value, schema, required_keys=None, allow_extra=False, per_item=None, per_list=None):
        if not isinstance(value, list):
            return False, "Must be a list of objects"
        required_keys = set(required_keys or [])

        for idx, item in enumerate(value):
            if not isinstance(item, dict):
                return False, f"list[{idx}] must be an object"

            missing = [k for k in required_keys if k not in item]
            if missing:
                return False, f"list[{idx}] missing required field(s): {', '.join(missing)}"

            if not allow_extra:
                extras = [k for k in item.keys() if k not in schema]
                if extras:
                    return False, f"list[{idx}] has unrecognized field(s): {', '.join(extras)}"

            for field, validators in schema.items():
                if field not in item:
                    continue
                field_value = item[field]
                validators_seq = validators if isinstance(validators, list) else [validators]

                for vt in validators_seq:
                    if vt == RequestValidator.allow_empty_value:
                        if RequestValidator.allow_empty_value(field_value):
                            break
                        else:
                            continue

                    ok, msg = RequestValidator._run_validator_callable(field_value, vt)
                    if not ok:
                        path = f"list[{idx}].{field}"
                        return False, f"{path}: {msg or 'Invalid value'}"

            if per_item:
                ok, msg = RequestValidator._run_validator_callable(item, per_item)
                if not ok:
                    path = f"list[{idx}]"
                    return False, f"{path}: {msg or 'Invalid combination of fields'}"

        if per_list:
            ok, msg = RequestValidator._run_validator_callable(value, per_list)
            if not ok:
                return False, msg or "Invalid list"

        return True

