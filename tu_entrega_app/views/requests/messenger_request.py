from tu_entrega_app.utils.api_http import RequestValidator
from tu_entrega_app.utils.constants import ApiConstants


class PartialUpdateRequest(RequestValidator):
    def __init__(self, request):
        self.required_keys = {
            }
        self.allow_empty = True
        self.validators = {
            'lng': super().validate_decimal,
            'lat': super().validate_decimal,
            'is_active': super().validate_boolean,
            'km_rate': super().validate_decimal
        }
        super().__init__(request, self.allow_empty, self.required_keys, self.validators)




