from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand

from cafeteria_inacap.models import Categoria, Producto


CATEGORIAS = (
    ("Sándwiches", "Sándwiches y preparaciones saladas."),
    ("Bebidas", "Bebidas frías y calientes."),
    ("Repostería", "Pastelería, galletas y productos dulces."),
    ("Colaciones", "Alternativas para una colación rápida."),
)

PRODUCTOS = (
    ("CAF-001", "Ave palta", "Sándwiches", 3500, 12, True),
    ("CAF-002", "Barros luco", "Sándwiches", 4200, 8, True),
    ("CAF-003", "Churrasco italiano", "Sándwiches", 4500, 0, True),
    ("CAF-004", "Vegetariano", "Sándwiches", 3200, 7, True),
    ("CAF-005", "Jamón queso", "Sándwiches", 2800, 5, False),
    ("CAF-006", "Café americano", "Bebidas", 1500, 30, True),
    ("CAF-007", "Capuchino", "Bebidas", 2200, 18, True),
    ("CAF-008", "Té", "Bebidas", 1200, 22, True),
    ("CAF-009", "Jugo natural", "Bebidas", 2000, 10, True),
    ("CAF-010", "Agua mineral", "Bebidas", 1000, 16, True),
    ("CAF-011", "Brownie", "Repostería", 1600, 14, True),
    ("CAF-012", "Muffin de arándano", "Repostería", 1700, 9, True),
    ("CAF-013", "Kuchen de manzana", "Repostería", 1900, 6, True),
    ("CAF-014", "Galleta de avena", "Repostería", 900, 20, True),
    ("CAF-015", "Queque de naranja", "Repostería", 1500, 4, True),
    ("CAF-016", "Ensalada César", "Colaciones", 3900, 8, True),
    ("CAF-017", "Ensalada vegetariana", "Colaciones", 3600, 6, True),
    ("CAF-018", "Yogur con granola", "Colaciones", 1800, 11, True),
    ("CAF-019", "Barra de cereal", "Colaciones", 800, 25, True),
    ("CAF-020", "Fruta de estación", "Colaciones", 1000, 13, True),
)


class Command(BaseCommand):
    help = "Carga categorías, productos y usuarios de demostración para desarrollo."

    def handle(self, *args, **options):
        categorias = {}
        for nombre, descripcion in CATEGORIAS:
            categoria, _ = Categoria.objects.get_or_create(
                nombre=nombre,
                defaults={"descripcion": descripcion, "activa": True},
            )
            categorias[nombre] = categoria

        for codigo, nombre, categoria, precio, stock, disponible in PRODUCTOS:
            Producto.objects.get_or_create(
                codigo=codigo,
                defaults={
                    "categoria": categorias[categoria],
                    "nombre": nombre,
                    "precio": precio,
                    "stock": stock,
                    "disponible": disponible,
                },
            )

        User = get_user_model()
        usuarios = (
            ("encargado", "Encargado", "encargado@fiores.cl", True),
            ("cliente1", "Estudiante Uno", "cliente1@alumno.inacap.cl", False),
            ("cliente2", "Estudiante Dos", "cliente2@alumno.inacap.cl", False),
        )
        for username, first_name, email, is_staff in usuarios:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first_name,
                    "email": email,
                    "is_staff": is_staff,
                },
            )
            if created:
                user.set_password("FioresDemo2026!")
                user.save(update_fields=["password"])
            if username == "encargado":
                permissions = Permission.objects.filter(
                    content_type__app_label__in=("cafeteria_inacap", "auth")
                )
                user.user_permissions.set(permissions)

        self.stdout.write(
            self.style.SUCCESS(
                "Datos demo cargados. Usuarios: encargado, cliente1 y cliente2. "
                "Clave inicial (solo desarrollo): FioresDemo2026!"
            )
        )
