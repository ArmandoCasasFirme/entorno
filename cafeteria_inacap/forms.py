from django import forms

from .models import Categoria


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
