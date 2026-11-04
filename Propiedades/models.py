from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class TipoPropiedad(models.Model):
    nombre = models.CharField(max_length=60, unique=True)

    class Meta:
        verbose_name = "tipo de propiedad"
        verbose_name_plural = "tipos de propiedad"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Caracteristica(models.Model):
    nombre = models.CharField(max_length=60, unique=True)

    class Meta:
        verbose_name = "característica"
        verbose_name_plural = "características"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Propiedad(models.Model):
    DISPONIBLE = "disponible"
    RESERVADA = "reservada"
    VENDIDA = "vendida"
    ESTADOS = [
        (DISPONIBLE, "Disponible"),
        (RESERVADA, "Reservada"),
        (VENDIDA, "Vendida"),
    ]

    corredor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="propiedades",
    )

    tipo = models.ForeignKey(
        "TipoPropiedad",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="propiedades",
    )
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField()
    precio = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    metros_cuadrados = models.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    estado = models.CharField(max_length=12, choices=ESTADOS, default=DISPONIBLE)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    caracteristicas = models.ManyToManyField(
        "Caracteristica",
        through="PropiedadCaracteristica",
        related_name="propiedades",
        blank=True,
    )

    class Meta:
        verbose_name = "propiedad"
        verbose_name_plural = "propiedades"
        ordering = ["-fecha_publicacion"]
        constraints = [
            models.CheckConstraint(condition=Q(precio__gt=0), name="propiedad_precio_mayor_cero"),
            models.CheckConstraint(condition=Q(metros_cuadrados__gt=0), name="propiedad_metros_mayor_cero"),
        ]

    def __str__(self):
        return self.titulo


class PropiedadCaracteristica(models.Model):
    MAX_ETIQUETAS = 5

    propiedad = models.ForeignKey(
        "Propiedad", on_delete=models.CASCADE, related_name="propiedad_caracteristicas"
    )
    caracteristica = models.ForeignKey(
        "Caracteristica", on_delete=models.CASCADE, related_name="propiedad_caracteristicas"
    )

    class Meta:
        verbose_name = "característica de propiedad"
        verbose_name_plural = "características de propiedades"
        constraints = [
            models.UniqueConstraint(
                fields=["propiedad", "caracteristica"],
                name="unica_caracteristica_por_propiedad",
            )
        ]

    def clean(self):
        if self.propiedad_id:
            otras = PropiedadCaracteristica.objects.filter(propiedad_id=self.propiedad_id)
            if self.pk:
                otras = otras.exclude(pk=self.pk)
            if otras.count() >= self.MAX_ETIQUETAS:
                raise ValidationError(
                    f"Una propiedad puede tener como máximo {self.MAX_ETIQUETAS} características."
                )

    def __str__(self):
        return f"{self.propiedad} - {self.caracteristica}"


class Consulta(models.Model):
    NUEVA = "nueva"
    RESPONDIDA = "respondida"
    CERRADA = "cerrada"
    ESTADOS = [
        (NUEVA, "Nueva"),
        (RESPONDIDA, "Respondida"),
        (CERRADA, "Cerrada"),
    ]
    ESTADOS_ABIERTOS = (NUEVA, RESPONDIDA)

    propiedad = models.ForeignKey(
        "Propiedad", on_delete=models.CASCADE, related_name="consultas"
    )
    interesado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="consultas_enviadas",
    )
    mensaje = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=12, choices=ESTADOS, default=NUEVA)

    class Meta:
        verbose_name = "consulta"
        verbose_name_plural = "consultas"
        ordering = ["-fecha"]

    def clean(self):
        if not (self.propiedad_id and self.interesado_id):
            return

        if self.propiedad.corredor_id == self.interesado_id:
            raise ValidationError("No puedes consultar por una propiedad tuya.")

        if self._state.adding:
            if self.propiedad.estado == self.propiedad.VENDIDA:
                raise ValidationError("No se aceptan consultas sobre propiedades vendidas.")

            if Consulta.objects.filter(
                propiedad_id=self.propiedad_id,
                interesado_id=self.interesado_id,
                estado__in=self.ESTADOS_ABIERTOS,
            ).exists():
                raise ValidationError("Ya tienes una consulta abierta sobre esta propiedad.")

    def __str__(self):
        return f"Consulta de {self.interesado} sobre {self.propiedad}"