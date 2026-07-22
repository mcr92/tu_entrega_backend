from tu_entrega_app.utils.api_http import RequestValidator


class LoginRequest(RequestValidator):
    def __init__(self, request):
        self.required_keys = {
            "phone",
            "password"
            }
        self.allow_empty = False
        self.validators = {
            'phone': super().validate_phone_number,
            'password': super().validate_string,
            'fcm_token': super().validate_text,
        }
        super().__init__(request, self.allow_empty, self.required_keys, self.validators)

class FCMRegisterRequest(RequestValidator):
    def __init__(self, data):
        self.required_keys = {
            "fcm_token"
            }
        self.allow_empty = False
        self.validators = {
            'fcm_token': super().validate_text,
        }
        super().__init__(data, self.allow_empty, self.required_keys, self.validators)
