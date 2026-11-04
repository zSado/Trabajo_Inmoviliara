from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from .forms import PropiedadForm, ConsultaForm, RegistroForm, PerfilForm, TipoPropiedadForm
from .models import Propiedad, TipoPropiedad, Caracteristica, Consulta

def home(request):
    propiedades_recientes = (Propiedad.objects.select_related("tipo", "corredor").prefetch_related("caracteristicas").order_by("-fecha_publicacion")[:4])
    disponibles = Propiedad.objects.filter(estado=Propiedad.DISPONIBLE).count()
    tipos = TipoPropiedad.objects.count()
    consultas = Consulta.objects.count()
    return render(request, "sitios/home.html", {
        "propiedades": propiedades_recientes, "disponibles": disponibles, "tipos": tipos, "consultas": consultas,
    })

def lista_propiedades(request):
    q = request.GET.get("q", "").strip()
    tipo_id = request.GET.get("tipo", "").strip()
    qs = (Propiedad.objects.select_related("tipo", "corredor").prefetch_related("caracteristicas").order_by("titulo"))
    if q:
        qs = qs.filter(Q(titulo__icontains=q) | Q(descripcion__icontains=q))
    if tipo_id.isdigit():
        qs = qs.filter(tipo_id=tipo_id)
    paginator = Paginator(qs, 5)
    page_obj = paginator.get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    querystring = params.urlencode()
    return render(request, "sitios/propiedad_list.html", {
        "page_obj": page_obj, "querystring": querystring, "tipos": TipoPropiedad.objects.order_by("nombre"), "q": q, "tipo_id": tipo_id,
    })

def detalle_propiedad(request, pk):
    propiedad = get_object_or_404(Propiedad.objects.select_related("tipo", "corredor").prefetch_related("caracteristicas"), pk=pk)
    return render(request, "sitios/propiedad_detail.html", {"propiedad": propiedad})

def registro(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Cuenta creada correctamente.")
            return redirect("home")
    else:
        form = RegistroForm()
    return render(request, "sitios/registro.html", {"form": form})

@login_required
def cuenta(request):
    return render(request, "sitios/cuenta.html", {
        "total_propiedades": request.user.propiedades.count(),
        "total_consultas": request.user.consultas_enviadas.count(),
    })

@login_required
def editar_perfil(request):
    if request.method == "POST":
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado.")
            return redirect("cuenta")
    else:
        form = PerfilForm(instance=request.user)
    return render(request, "sitios/perfil_form.html", {"form": form})

class CambiarPasswordView(PasswordChangeView):
    template_name = "sitios/cambiar_password.html"
    success_url = reverse_lazy("cuenta")
    def form_valid(self, form):
        messages.success(self.request, "Contraseña actualizada correctamente.")
        return super().form_valid(form)

@login_required
def crear_propiedad(request):
    if request.method == "POST":
        form = PropiedadForm(request.POST)
        if form.is_valid():
            propiedad = form.save(commit=False)
            propiedad.corredor = request.user
            propiedad.save()
            form.save_m2m()
            messages.success(request, "Propiedad creada correctamente.")
            return redirect("mis_propiedades")
        else:
            messages.error(request, "Revisa los datos del formulario.")
    else:
        form = PropiedadForm()
    return render(request, "sitios/propiedad_form.html", {"form": form, "accion": "Crear"})

@login_required
def editar_propiedad(request, pk):
    propiedad = get_object_or_404(Propiedad, pk=pk)
    if propiedad.corredor != request.user:
        raise PermissionDenied
    if request.method == "POST":
        form = PropiedadForm(request.POST, instance=propiedad)
        if form.is_valid():
            form.save()
            messages.success(request, "Propiedad actualizada.")
            return redirect("mis_propiedades")
        else:
            messages.error(request, "Revisa los datos del formulario.")
    else:
        form = PropiedadForm(instance=propiedad)
    return render(request, "sitios/propiedad_form.html", {"form": form, "accion": "Editar"})

@login_required
def eliminar_propiedad(request, pk):
    propiedad = get_object_or_404(Propiedad, pk=pk)
    if propiedad.corredor != request.user:
        raise PermissionDenied
    if request.method == "POST":
        propiedad.delete()
        messages.success(request, "Propiedad eliminada.")
        return redirect("mis_propiedades")
    return render(request, "sitios/propiedad_confirm_delete.html", {"propiedad": propiedad})

@login_required
def mis_propiedades(request):
    propiedades = (Propiedad.objects.filter(corredor=request.user).select_related("tipo").prefetch_related("caracteristicas").order_by("-fecha_publicacion"))
    return render(request, "sitios/mis_propiedades.html", {"propiedades": propiedades})

@login_required
def crear_tipo(request):
    if request.method == "POST":
        form = TipoPropiedadForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tipo de propiedad creado.")
            return redirect("crear_propiedad")
    else:
        form = TipoPropiedadForm()
    return render(request, "sitios/tipo_form.html", {"form": form})

@login_required
def crear_consulta(request, propiedad_pk):
    propiedad = get_object_or_404(Propiedad, pk=propiedad_pk)
    if request.method == "POST":
        form = ConsultaForm(request.POST)
        if form.is_valid():
            consulta = form.save(commit=False)
            consulta.propiedad = propiedad
            consulta.interesado = request.user
            try:
                consulta.full_clean()
                consulta.save()
                messages.success(request, "Consulta enviada.")
                return redirect("mis_consultas")
            except Exception as error:
                if hasattr(error, "message_dict"):
                    for campo, errores in error.message_dict.items():
                        for e in errores:
                            form.add_error(campo, e)
                else:
                    messages.error(request, str(error))
    else:
        form = ConsultaForm()
    return render(request, "sitios/consulta_form.html", {"form": form, "propiedad": propiedad})

@login_required
def mis_consultas(request):
    consultas = (Consulta.objects.filter(interesado=request.user).select_related("propiedad", "propiedad__corredor").order_by("-fecha"))
    return render(request, "sitios/mis_consultas.html", {"consultas": consultas})

@login_required
@require_POST
def cancelar_consulta(request, pk):
    consulta = get_object_or_404(Consulta, pk=pk, interesado=request.user)
    if consulta.estado != Consulta.NUEVA:
        messages.error(request, "Solo puedes cancelar consultas nuevas.")
    else:
        consulta.estado = Consulta.CERRADA
        consulta.save()
        messages.success(request, "Consulta cancelada.")
    return redirect("mis_consultas")

@login_required
def consultas_recibidas(request):
    consultas = (Consulta.objects.filter(propiedad__corredor=request.user).select_related("propiedad", "interesado").order_by("-fecha"))
    return render(request, "sitios/consultas_recibidas.html", {"consultas": consultas})

@login_required
@require_POST
def responder_consulta(request, pk):
    consulta = get_object_or_404(Consulta, pk=pk)
    if consulta.propiedad.corredor != request.user:
        raise PermissionDenied
    consulta.estado = Consulta.RESPONDIDA
    consulta.save()
    messages.success(request, "Consulta marcada como respondida.")
    return redirect("consultas_recibidas")

@login_required
@require_POST
def cerrar_consulta(request, pk):
    consulta = get_object_or_404(Consulta, pk=pk)
    if consulta.propiedad.corredor != request.user:
        raise PermissionDenied
    consulta.estado = Consulta.CERRADA
    consulta.save()
    messages.success(request, "Consulta cerrada.")
    return redirect("consultas_recibidas")