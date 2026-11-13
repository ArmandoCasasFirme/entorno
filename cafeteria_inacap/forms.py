from django import forms

from .models import Categoria, Producto


class FiltroCatalogoForm(forms.Form):
    q = forms.CharField(
        label="Buscar por nombre",
        required=False,
        max_length=100,
    )
    categoria = forms.ModelChoiceField(
        label="Categoría",
        queryset=Categoria.objects.filter(activa=True),
        required=False,
        empty_label="Todas las categorías",
    )


class CategoriaGestionForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "descripcion", "activa"]


class ProductoGestionForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            "categoria",
            "codigo",
            "nombre",
            "precio",
            "stock",
            "disponible",
        ]


class FiltroGestionProductoForm(forms.Form):
    q = forms.CharField(label="Nombre o código", required=False, max_length=100)
    categoria = forms.ModelChoiceField(
        label="Categoría",
        queryset=Categoria.objects.all(),
        required=False,
        empty_label="Todas las categorías",
    )
    disponible = forms.ChoiceField(
        label="Disponibilidad",
        required=False,
        choices=[
            ("", "Todas"),
            ("si", "Disponible"),
            ("no", "No disponible"),
        ],
    )
