from django.urls import path, include
from rest_framework.routers import DefaultRouter
from tu_entrega_app.views import auth_view, user_view, messenger_view, shop_view, ticket_view, payments_view


router = DefaultRouter()

router.register(r"users", user_view.UserView)
router.register(r"messenger", messenger_view.MessengerView)
router.register(r"shop", shop_view.ShopView)
router.register(r"ticket", ticket_view.TicketView)
router.register(r"payment", payments_view.PaymentView)


urlpatterns = [
    path("", include(router.urls)),
    path("login/", include(auth_view))    
]