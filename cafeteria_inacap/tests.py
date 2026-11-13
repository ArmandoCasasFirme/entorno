from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from .models import Categoria, DetallePedido, Pedido, Producto


class ModelConstraintTests(TestCase):
    def setUp(self):
        self.cliente = get_user_model().objects.create_user(username="estudiante")
        self.categoria = Categoria.objects.create(
            nombre="Bebidas",
            descripcion="Bebidas frías y calientes.",
        )
        self.producto = Producto.objects.create(
            categoria=self.categoria,
            codigo="BEB001",
            nombre="Café",
            precio=1500,
            stock=10,
        )

    def test_categoria_with_products_cannot_be_deleted(self):
        with self.assertRaises(ProtectedError):
            self.categoria.delete()

    def test_product_in_order_cannot_be_deleted(self):
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            hora_retiro="12:30",
            estado="pendiente",
            total=1500,
            observacion="",
        )
        DetallePedido.objects.create(
            pedido=pedido,
            producto=self.producto,
            cantidad=1,
            precio_unitario=1500,
            subtotal=1500,
        )

        with self.assertRaises(ProtectedError):
            self.producto.delete()

    def test_order_cannot_have_duplicate_product_detail(self):
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            hora_retiro="12:30",
            estado="pendiente",
            total=3000,
            observacion="",
        )
        DetallePedido.objects.create(
            pedido=pedido,
            producto=self.producto,
            cantidad=1,
            precio_unitario=1500,
            subtotal=1500,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            DetallePedido.objects.create(
                pedido=pedido,
                producto=self.producto,
                cantidad=1,
                precio_unitario=1500,
                subtotal=1500,
            )


class DemoDataCommandTests(TestCase):
    def test_command_loads_expected_demo_data_idempotently(self):
        call_command("cargar_datos_demo", verbosity=0)
        call_command("cargar_datos_demo", verbosity=0)

        self.assertEqual(Categoria.objects.count(), 4)
        self.assertEqual(Producto.objects.count(), 20)
        self.assertTrue(Producto.objects.filter(stock=0).exists())
        self.assertTrue(Producto.objects.filter(disponible=False).exists())

        User = get_user_model()
        self.assertEqual(User.objects.count(), 3)
        self.assertTrue(User.objects.get(username="encargado").is_staff)
        self.assertFalse(User.objects.get(username="cliente1").is_staff)
