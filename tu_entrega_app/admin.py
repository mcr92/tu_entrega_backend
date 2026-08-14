from django.contrib import admin
from tu_entrega_app.models import User, Ticket, Contact, Messenger, Shop, BlockPlayer, Transaction, Payment

admin.site.site_title = "TuEntrega site admin"
admin.site.site_header = "TuEntrega administration"
admin.site.index_title = "Site administration"

# Register your models here.
admin.site.register(User)
admin.site.register(Ticket)
admin.site.register(Contact)
admin.site.register(Messenger)
admin.site.register(Shop)
admin.site.register(BlockPlayer)
admin.site.register(Transaction)
admin.site.register(Payment)
