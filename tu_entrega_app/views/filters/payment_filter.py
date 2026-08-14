from rest_framework.filters import SearchFilter
from django.db.models import Subquery, OuterRef
from tu_entrega_app.utils.constants import ApiConstants
from tu_entrega_app.utils.api_http import RequestValidator
from tu_entrega_app.models import Status_Transaction

class PaymentSearchFilter(SearchFilter):
    def filter_queryset(self, request, queryset, view):
        search_term = request.query_params.get('search', '').lower()        

        if RequestValidator.validate_in_array(search_term, ApiConstants.TransactionStatus.choices()):
            return queryset.annotate(
                    latest_status_name=Subquery(
                        Status_Transaction.objects.filter(status_transaction=OuterRef('pk')
                ).order_by('-created_at').values('status')[:1])
                ).filter(latest_status_name= search_term)
        
        # Si no, usar el comportamiento original
        return super().filter_queryset(request, queryset, view)