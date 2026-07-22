from django.urls import path, include
from rest_framework.routers import DefaultRouter
from tu_entrega_app.views import auth_view


router = DefaultRouter()


urlpatterns = [
    path("", include(router.urls)),
    path("login/", include(auth_view))    
]