from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


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


@role_required(staff=True)
def encargado_dashboard(request):
    return render(request, "cafeteria_inacap/encargado.html")
