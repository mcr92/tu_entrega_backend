from django.contrib import admin
from tu_entrega_app.models import User

admin.site.site_title = "TuEntrega site admin"
admin.site.site_header = "TuEntrega administration"
admin.site.index_title = "Site administration"

# Register your models here.
admin.site.register(User)

