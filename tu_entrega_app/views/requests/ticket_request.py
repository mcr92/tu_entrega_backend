from tu_entrega_app.utils.api_http import RequestValidator
from tu_entrega_app.utils.constants import ApiConstants


class CreateRequest(RequestValidator):
    def __init__(self, request):
        self.required_keys = {
            "product",
            "price",
            "delivery_contact",
            "collection_contact",
            }
        self.allow_empty = False
        self.validators = {
            'product': super().validate_string,
            'price': super().validate_decimal,
            'currency': (super().validate_in_array, ApiConstants.Currency.choices()),
            'payment_method': (super().validate_in_array, ApiConstants.Payment_Method.choices()),
            'price_save': super().validate_decimal,
            'delivery_contact': super().validate_json,
            'collection_contact': super().validate_json,
        }
        super().__init__(request, self.allow_empty, self.required_keys, self.validators)


