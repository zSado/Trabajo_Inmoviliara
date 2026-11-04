from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Propiedad, TipoPropiedad, Caracteristica, Consulta

class PropiedadForm(forms.ModelForm):
    caracteristicas = forms.ModelMultipleChoiceField(
        queryset=Caracteristica.objects.order_by("nombre"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Características",
    )

    class Meta:
        model = Propiedad
        fields = ["titulo", "descripcion", "precio", "metros_cuadrados", "estado", "tipo", "caracteristicas"]
        labels = {
            "titulo": "Título de la propiedad",
            "descripcion": "Descripción",
            "precio": "Precio (CLP)",
            "metros_cuadrados": "Metros cuadrados",
            "estado": "Estado",
            "tipo": "Tipo de propiedad",
        }
        help_texts = {
            "titulo": "Mínimo 5 caracteres.",
            "precio": "Debe ser mayor que cero.",
            "metros_cuadrados": "Debe ser mayor que cero.",
        }
        widgets = {
            "titulo": forms.TextInput(attrs={"placeholder": "Ej: Casa en Ñuñoa"}),
            "descripcion": forms.Textarea(attrs={"rows": 4}),
            "precio": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
            "metros_cuadrados": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tipo"].queryset = TipoPropiedad.objects.order_by("nombre")
        self.fields["tipo"].empty_label = "— Sin tipo —"

    def clean_titulo(self):
        titulo = self.cleaned_data["titulo"].strip()
        if len(titulo) < 5:
            raise forms.ValidationError("El título debe tener al menos 5 caracteres.")
        return titulo

    def clean(self):
        cleaned = super().clean()
        precio = cleaned.get("precio")
        metros = cleaned.get("metros_cuadrados")
        if precio is not None and precio <= 0:
            self.add_error("precio", "El precio debe ser mayor que cero.")
        if metros is not None and metros <= 0:
            self.add_error("metros_cuadrados", "Los metros cuadrados deben ser mayores que cero.")
        caracteristicas = cleaned.get("caracteristicas")
        if caracteristicas and caracteristicas.count() > 5:
            self.add_error("caracteristicas", "Puedes seleccionar como máximo 5 características.")
        return cleaned

class ConsultaForm(forms.ModelForm):
    class Meta:
        model = Consulta
        fields = ["mensaje"]
        labels = {"mensaje": "Tu consulta"}
        widgets = {"mensaje": forms.Textarea(attrs={"rows": 4, "placeholder": "Escribe tu pregunta..."})}

class RegistroForm(UserCreationForm):
    email = forms.EmailField(label="Correo electrónico", required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")
        labels = {"username": "Nombre de usuario"} # <-- Traducido

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este correo ya está registrado.")
        return email

class PerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        labels = {"first_name": "Nombre", "last_name": "Apellido", "email": "Correo"}

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Este correo ya pertenece a otra cuenta.")
        return email

class TipoPropiedadForm(forms.ModelForm):
    class Meta:
        model = TipoPropiedad
        fields = ["nombre"]
        labels = {"nombre": "Nombre del tipo"}