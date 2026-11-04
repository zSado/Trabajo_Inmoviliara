from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('propiedades/', views.lista_propiedades, name='lista_propiedades'),
    path('propiedades/<int:pk>/', views.detalle_propiedad, name='detalle_propiedad'),
    path('propiedades/nueva/', views.crear_propiedad, name='crear_propiedad'),
    path('propiedades/<int:pk>/editar/', views.editar_propiedad, name='editar_propiedad'),
    path('propiedades/<int:pk>/eliminar/', views.eliminar_propiedad, name='eliminar_propiedad'),
    path('mis-propiedades/', views.mis_propiedades, name='mis_propiedades'),
    path('tipos/nuevo/', views.crear_tipo, name='crear_tipo'),
    path('registro/', views.registro, name='registro'),
    path('login/', auth_views.LoginView.as_view(template_name='sitios/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('cuenta/', views.cuenta, name='cuenta'),
    path('cuenta/editar/', views.editar_perfil, name='editar_perfil'),
    path('cuenta/password/', views.CambiarPasswordView.as_view(), name='cambiar_password'),
    path('propiedades/<int:propiedad_pk>/consultar/', views.crear_consulta, name='crear_consulta'),
    path('mis-consultas/', views.mis_consultas, name='mis_consultas'),
    path('mis-consultas/<int:pk>/cancelar/', views.cancelar_consulta, name='cancelar_consulta'),
    path('consultas-recibidas/', views.consultas_recibidas, name='consultas_recibidas'),
    path('consultas-recibidas/<int:pk>/responder/', views.responder_consulta, name='responder_consulta'),
    path('consultas-recibidas/<int:pk>/cerrar/', views.cerrar_consulta, name='cerrar_consulta'),
]