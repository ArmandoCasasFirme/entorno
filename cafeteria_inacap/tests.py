from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

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


class AuthenticationAndRoleTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.cliente = User.objects.create_user(
            username="cliente",
            password="cliente-seguro-123",
        )
        self.encargado = User.objects.create_user(
            username="encargado",
            password="encargado-seguro-123",
            is_staff=True,
        )

    def test_application_routes_require_authentication(self):
        response = self.client.get("/")
        self.assertRedirects(response, "/accounts/login/?next=/")

        response = self.client.get("/encargado/")
        self.assertRedirects(
            response,
            "/accounts/login/?next=/encargado/",
        )

    def test_client_can_access_client_area_but_not_staff_area(self):
        self.assertTrue(self.client.login(username="cliente", password="cliente-seguro-123"))

        response = self.client.get("/cliente/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cliente")
        self.assertContains(response, "Cliente")

        response = self.client.get("/encargado/")
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Acceso denegado", status_code=403)
        self.assertContains(response, "Usuario:", status_code=403)

        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)

    def test_staff_can_access_staff_area_but_not_client_area(self):
        self.assertTrue(
            self.client.login(username="encargado", password="encargado-seguro-123")
        )

        response = self.client.get("/")
        self.assertRedirects(response, "/encargado/")
        self.assertEqual(self.client.get("/encargado/").status_code, 200)
        self.assertEqual(self.client.get("/cliente/").status_code, 403)

    def test_logout_ends_session_and_session_timeout_is_30_minutes(self):
        self.assertTrue(self.client.login(username="cliente", password="cliente-seguro-123"))

        session = self.client.session
        self.assertEqual(session.get_expiry_age(), 1800)
        self.assertEqual(settings.SESSION_COOKIE_AGE, 1800)
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)

        response = self.client.post("/accounts/logout/")
        self.assertRedirects(response, "/accounts/login/")
        self.assertRedirects(
            self.client.get("/cliente/"),
            "/accounts/login/?next=/cliente/",
        )
