"""
URL configuration for cafeteria project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from cafeteria_inacap import views

urlpatterns = [
    path("accounts/login/", auth_views.LoginView.as_view(
        template_name="registration/login.html",
        redirect_authenticated_user=True,
    ), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", views.home, name="home"),
    path("cliente/", views.cliente_dashboard, name="cliente"),
    path("cliente/catalogo/", views.catalogo, name="catalogo"),
    path("cliente/carrito/", views.carrito, name="carrito"),
    path(
        "cliente/carrito/agregar/<int:producto_id>/",
        views.agregar_al_carrito,
        name="agregar_al_carrito",
    ),
    path(
        "cliente/carrito/quitar/<int:producto_id>/",
        views.quitar_del_carrito,
        name="quitar_del_carrito",
    ),
    path("encargado/", views.encargado_dashboard, name="encargado"),
    path(
        "encargado/categorias/",
        views.categorias_lista,
        name="categorias_lista",
    ),
    path(
        "encargado/categorias/nueva/",
        views.categoria_formulario,
        name="categoria_crear",
    ),
    path(
        "encargado/categorias/<int:pk>/editar/",
        views.categoria_formulario,
        name="categoria_editar",
    ),
    path(
        "encargado/categorias/<int:pk>/eliminar/",
        views.categoria_eliminar,
        name="categoria_eliminar",
    ),
    path(
        "encargado/categorias/<int:pk>/",
        views.categoria_detalle,
        name="categoria_detalle",
    ),
    path(
        "encargado/productos/",
        views.productos_gestion_lista,
        name="productos_gestion_lista",
    ),
    path(
        "encargado/productos/nuevo/",
        views.producto_gestion_formulario,
        name="producto_gestion_crear",
    ),
    path(
        "encargado/productos/<int:pk>/editar/",
        views.producto_gestion_formulario,
        name="producto_gestion_editar",
    ),
    path(
        "encargado/productos/<int:pk>/eliminar/",
        views.producto_gestion_eliminar,
        name="producto_gestion_eliminar",
    ),
    path(
        "encargado/productos/<int:pk>/",
        views.producto_gestion_detalle,
        name="producto_gestion_detalle",
    ),
    path("admin/", admin.site.urls),
]
