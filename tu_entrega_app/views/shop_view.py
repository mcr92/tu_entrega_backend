from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from tu_entrega_app.models import Shop
from tu_entrega_app.services.serializers.shop_serializer import ShopSerializer


class ShopView(viewsets.ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [IsAuthenticated]


    filterset_fields = ["owner__name", "owner__phone", "name"]
    search_fields = [
        "owner__name", "owner__phone", "name"
    ]

    filter_backends = [
        SearchFilter,
        OrderingFilter
    ]