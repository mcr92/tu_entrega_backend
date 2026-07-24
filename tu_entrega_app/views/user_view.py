from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from tu_entrega_app.models import User
from tu_entrega_app.services.serializers.user_serializer import UserSerializer, UserUpdateSerializer


class UserView(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


    filterset_fields = ["name", "phone"]
    search_fields = [
        "name", "phone"
    ]

    filter_backends = [
        SearchFilter,
        OrderingFilter
    ]

    def get_serializer_class(self):
        if self.action in ["list", "update", "partial_update"]:
            serializer_class = UserUpdateSerializer
        else:
            serializer_class = UserSerializer
        
        return serializer_class
    