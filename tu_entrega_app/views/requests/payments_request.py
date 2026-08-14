from tu_entrega_app.utils.api_http import RequestValidator
from tu_entrega_app.utils.constants import ApiConstants


class ReloadRequest(RequestValidator):

    def __init__(self, request):
            self.required_keys = {
                'amount',
                'user_id'
                }
            self.allow_empty = True
            self.validators = {
                'amount': super().validate_decimal,
                'user_id': super().validate_integer,
                'paymentmethod': [super().allow_empty_value, (super().validate_in_array, ApiConstants.Payment_Method.choices())],
            }
            super().__init__(request, self.allow_empty, self.required_keys, self.validators)

class RequestRechargeRequest(RequestValidator):

    def __init__(self, request):
            self.required_keys = {
                'amount'
                }
            self.allow_empty = True
            self.validators = {
                'amount': [super().validate_decimal, (super().validate_double_range,float(0),float(1000000))],
                'paymentmethod': [super().allow_empty_value, (super().validate_in_array, ApiConstants.Payment_Method.choices())],
            }
            super().__init__(request, self.allow_empty, self.required_keys, self.validators)

