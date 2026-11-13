from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .forms import (
    CategoriaGestionForm,
    FiltroCatalogoForm,
    FiltroGestionProductoForm,
    ProductoGestionForm,
)
from .models import Categoria, Producto


def role_required(*, staff):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if request.user.is_staff != staff:
                return render(request, "cafeteria_inacap/403.html", status=403)
            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator


@login_required
def home(request):
    if request.user.is_staff:
        return redirect("encargado")
    return redirect("cliente")


@role_required(staff=False)
def cliente_dashboard(request):
    return render(request, "cafeteria_inacap/cliente.html")


@role_required(staff=False)
def catalogo(request):
    form = FiltroCatalogoForm(request.GET)
    productos = Producto.objects.filter(
        disponible=True,
        categoria__activa=True,
    ).select_related("categoria")

    if form.is_valid():
        if form.cleaned_data["q"]:
            productos = productos.filter(nombre__icontains=form.cleaned_data["q"])
        if form.cleaned_data["categoria"]:
            productos = productos.filter(categoria=form.cleaned_data["categoria"])
    else:
        productos = productos.none()

    return render(
        request,
        "cafeteria_inacap/catalogo.html",
        {"form": form, "productos": productos},
    )


@role_required(staff=False)
def carrito(request):
    productos_carrito = request.session.get("carrito", {})
    productos = Producto.objects.filter(
        pk__in=productos_carrito.keys(),
    ).select_related("categoria")
    items = []
    for producto in productos:
        cantidad = productos_carrito[str(producto.pk)]
        items.append(
            {
                "producto": producto,
                "cantidad": cantidad,
                "subtotal": producto.precio * cantidad,
            }
        )

    return render(
        request,
        "cafeteria_inacap/carrito.html",
        {
            "items": items,
            "total": sum(item["subtotal"] for item in items),
        },
    )


@role_required(staff=False)
@require_POST
def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(
        Producto.objects.select_related("categoria"),
        pk=producto_id,
    )
    if not producto.disponible or not producto.categoria.activa:
        messages.error(request, "Este producto ya no está disponible.")
        return redirect("catalogo")
    if producto.stock <= 0:
        messages.error(request, "Este producto está agotado.")
        return redirect("catalogo")

    productos_carrito = request.session.get("carrito", {})
    clave_producto = str(producto.pk)
    cantidad_actual = productos_carrito.get(clave_producto, 0)
    if cantidad_actual >= producto.stock:
        messages.error(request, "No hay más unidades disponibles de este producto.")
        return redirect("catalogo")

    productos_carrito[clave_producto] = cantidad_actual + 1
    request.session["carrito"] = productos_carrito
    messages.success(request, f"{producto.nombre} se agregó al carrito.")
    return redirect("catalogo")


@role_required(staff=False)
@require_POST
def quitar_del_carrito(request, producto_id):
    productos_carrito = request.session.get("carrito", {})
    productos_carrito.pop(str(producto_id), None)
    request.session["carrito"] = productos_carrito
    messages.success(request, "Producto eliminado del carrito.")
    return redirect("carrito")


@role_required(staff=True)
def categorias_lista(request):
    categorias = Categoria.objects.all()
    return render(
        request,
        "cafeteria_inacap/gestionar_categorias_lista.html",
        {"categorias": categorias},
    )


@role_required(staff=True)
def categoria_detalle(request, pk):
    categoria = get_object_or_404(
        Categoria.objects.prefetch_related("productos"),
        pk=pk,
    )
    return render(
        request,
        "cafeteria_inacap/gestionar_categoria_detalle.html",
        {"categoria": categoria},
    )


@role_required(staff=True)
def categoria_formulario(request, pk=None):
    categoria = get_object_or_404(Categoria, pk=pk) if pk else None
    if request.method == "POST":
        form = CategoriaGestionForm(request.POST, instance=categoria)
        if form.is_valid():
            categoria = form.save()
            resultado = "actualizada" if pk else "creada"
            messages.success(request, f"Categoría {resultado} correctamente.")
            return redirect("categoria_detalle", pk=categoria.pk)
    else:
        form = CategoriaGestionForm(instance=categoria)

    return render(
        request,
        "cafeteria_inacap/gestionar_formulario.html",
        {
            "form": form,
            "titulo": "Editar categoría" if pk else "Crear categoría",
            "cancelar_url": (
                "categoria_detalle" if pk else "categorias_lista"
            ),
            "cancelar_pk": pk,
        },
    )


@role_required(staff=True)
@require_http_methods(["GET", "POST"])
def categoria_eliminar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == "POST":
        try:
            categoria.delete()
            messages.success(request, "Categoría eliminada correctamente.")
            return redirect("categorias_lista")
        except ProtectedError:
            messages.error(
                request,
                "No se puede eliminar la categoría porque tiene productos.",
            )
            return redirect("categoria_detalle", pk=categoria.pk)

    return render(
        request,
        "cafeteria_inacap/gestionar_confirmar_eliminacion.html",
        {
            "titulo": "Eliminar categoría",
            "objeto": categoria,
            "cancelar_url": "categoria_detalle",
            "cancelar_pk": categoria.pk,
        },
    )


@role_required(staff=True)
def productos_gestion_lista(request):
    form = FiltroGestionProductoForm(request.GET)
    productos = Producto.objects.select_related("categoria").all()
    if form.is_valid():
        texto = form.cleaned_data["q"]
        if texto:
            productos = productos.filter(
                Q(nombre__icontains=texto) | Q(codigo__icontains=texto)
            )
        if form.cleaned_data["categoria"]:
            productos = productos.filter(categoria=form.cleaned_data["categoria"])
        if form.cleaned_data["disponible"] == "si":
            productos = productos.filter(disponible=True)
        elif form.cleaned_data["disponible"] == "no":
            productos = productos.filter(disponible=False)
    else:
        productos = productos.none()

    return render(
        request,
        "cafeteria_inacap/gestionar_productos_lista.html",
        {"form": form, "productos": productos},
    )


@role_required(staff=True)
def producto_gestion_detalle(request, pk):
    producto = get_object_or_404(
        Producto.objects.select_related("categoria"),
        pk=pk,
    )
    return render(
        request,
        "cafeteria_inacap/gestionar_producto_detalle.html",
        {"producto": producto},
    )


@role_required(staff=True)
def producto_gestion_formulario(request, pk=None):
    producto = get_object_or_404(Producto, pk=pk) if pk else None
    if request.method == "POST":
        form = ProductoGestionForm(request.POST, instance=producto)
        if form.is_valid():
            producto = form.save()
            resultado = "actualizado" if pk else "creado"
            messages.success(request, f"Producto {resultado} correctamente.")
            return redirect("producto_gestion_detalle", pk=producto.pk)
    else:
        form = ProductoGestionForm(instance=producto)

    return render(
        request,
        "cafeteria_inacap/gestionar_formulario.html",
        {
            "form": form,
            "titulo": "Editar producto" if pk else "Crear producto",
            "cancelar_url": (
                "producto_gestion_detalle" if pk else "productos_gestion_lista"
            ),
            "cancelar_pk": pk,
        },
    )


@role_required(staff=True)
@require_http_methods(["GET", "POST"])
def producto_gestion_eliminar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        try:
            producto.delete()
            messages.success(request, "Producto eliminado correctamente.")
            return redirect("productos_gestion_lista")
        except ProtectedError:
            messages.error(
                request,
                "No se puede eliminar el producto porque aparece en un pedido.",
            )
            return redirect("producto_gestion_detalle", pk=producto.pk)

    return render(
        request,
        "cafeteria_inacap/gestionar_confirmar_eliminacion.html",
        {
            "titulo": "Eliminar producto",
            "objeto": producto,
            "cancelar_url": "producto_gestion_detalle",
            "cancelar_pk": producto.pk,
        },
    )


@role_required(staff=True)
def encargado_dashboard(request):
    return render(request, "cafeteria_inacap/encargado.html")
