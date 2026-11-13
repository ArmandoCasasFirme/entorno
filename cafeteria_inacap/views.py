from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import FiltroCatalogoForm
from .models import Producto


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
def encargado_dashboard(request):
    return render(request, "cafeteria_inacap/encargado.html")
