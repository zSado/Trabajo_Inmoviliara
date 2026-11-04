from django.contrib import admin
from .models import Propiedad, TipoPropiedad, Caracteristica, Consulta

@admin.register(TipoPropiedad)
class TipoPropiedadAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)

@admin.register(Caracteristica)
class CaracteristicaAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)

@admin.register(Propiedad)
class PropiedadAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "corredor", "precio", "metros_cuadrados", "estado", "fecha_publicacion")
    list_filter = ("estado", "tipo")
    search_fields = ("titulo", "descripcion")

@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ("propiedad", "interesado", "estado", "fecha")
    list_filter = ("estado",)
    search_fields = ("mensaje", "propiedad__titulo", "interesado__username")