from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

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
            codigo="CAF-101",
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


class ProductCatalogTests(TestCase):
    def setUp(self):
        User = get_user_model()
        cliente = User.objects.create_user(username="comprador", password="demo-pass-123")
        self.client.force_login(cliente)

        self.categoria = Categoria.objects.create(
            nombre="Cafetería",
            descripcion="Bebidas y café.",
        )
        self.categoria_inactiva = Categoria.objects.create(
            nombre="Temporal",
            descripcion="Categoría inactiva.",
            activa=False,
        )
        self.cafe = Producto.objects.create(
            categoria=self.categoria,
            codigo="CAF-101",
            nombre="Café espresso",
            precio=1500,
            stock=2,
        )
        self.agotado = Producto.objects.create(
            categoria=self.categoria,
            codigo="CAF-102",
            nombre="Café filtrado",
            precio=2000,
            stock=0,
        )
        self.no_disponible = Producto.objects.create(
            categoria=self.categoria,
            codigo="CAF-103",
            nombre="Café temporal",
            precio=1200,
            stock=5,
            disponible=False,
        )
        self.de_categoria_inactiva = Producto.objects.create(
            categoria=self.categoria_inactiva,
            codigo="CAF-104",
            nombre="Producto temporal",
            precio=1000,
            stock=4,
        )

    def test_catalog_lists_active_products_and_marks_zero_stock(self):
        response = self.client.get("/cliente/catalogo/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Café espresso")
        self.assertContains(response, "Café filtrado")
        self.assertContains(response, "Agotado")
        self.assertContains(response, "$1.500")
        self.assertNotContains(response, "Café temporal")
        self.assertNotContains(response, "Producto temporal")
        self.assertNotContains(
            response,
            f'action="/cliente/carrito/agregar/{self.agotado.pk}/"',
        )

    def test_catalog_search_and_category_filter(self):
        response = self.client.get(
            "/cliente/catalogo/",
            {"q": "espresso", "categoria": self.categoria.pk},
        )

        self.assertContains(response, "Café espresso")
        self.assertNotContains(response, "Café filtrado")

    def test_stock_validation_prevents_adding_unavailable_products(self):
        response = self.client.post(
            f"/cliente/carrito/agregar/{self.agotado.pk}/",
        )
        self.assertRedirects(response, "/cliente/catalogo/")
        self.assertNotIn("carrito", self.client.session)

        self.client.post(
            f"/cliente/carrito/agregar/{self.no_disponible.pk}/",
        )
        self.client.post(
            f"/cliente/carrito/agregar/{self.de_categoria_inactiva.pk}/",
        )
        self.assertNotIn("carrito", self.client.session)

        response = self.client.post(
            f"/cliente/carrito/agregar/{self.cafe.pk}/",
        )
        self.assertRedirects(response, "/cliente/catalogo/")
        self.assertEqual(self.client.session["carrito"], {str(self.cafe.pk): 1})

        self.client.post(f"/cliente/carrito/agregar/{self.cafe.pk}/")
        self.assertEqual(self.client.session["carrito"], {str(self.cafe.pk): 2})

        self.client.post(f"/cliente/carrito/agregar/{self.cafe.pk}/")
        self.assertEqual(self.client.session["carrito"], {str(self.cafe.pk): 2})

    def test_staff_cannot_access_client_catalog(self):
        User = get_user_model()
        encargado = User.objects.create_user(username="otro-encargado", is_staff=True)
        self.client.force_login(encargado)

        response = self.client.get("/cliente/catalogo/")
        self.assertEqual(response.status_code, 403)

    def test_cart_displays_clp_total_and_removes_items(self):
        self.client.post(f"/cliente/carrito/agregar/{self.cafe.pk}/")

        response = self.client.get("/cliente/carrito/")
        self.assertContains(response, "Café espresso")
        self.assertContains(response, "$1.500")
        self.assertContains(response, "$1.500</strong>")

        response = self.client.post(
            f"/cliente/carrito/quitar/{self.cafe.pk}/",
            follow=True,
        )
        self.assertContains(response, "Tu carrito está vacío.")
        self.assertEqual(self.client.session["carrito"], {})


class StaffManagementTests(TestCase):
    def setUp(self):
        User = get_user_model()
        encargado = User.objects.create_user(username="gestor", is_staff=True)
        self.cliente = User.objects.create_user(username="alumna")
        self.client.force_login(encargado)

        self.categoria = Categoria.objects.create(
            nombre="Bebidas",
            descripcion="Bebidas preparadas.",
        )
        self.producto = Producto.objects.create(
            categoria=self.categoria,
            codigo="CAF-201",
            nombre="Café americano",
            precio=1500,
            stock=8,
        )

    def test_only_staff_can_open_management_pages(self):
        self.client.force_login(self.cliente)

        response = self.client.get(reverse("categorias_lista"))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("productos_gestion_lista"))
        self.assertEqual(response.status_code, 403)

    def test_categories_can_be_created_edited_and_deleted_after_confirmation(self):
        response = self.client.post(
            reverse("categoria_crear"),
            {
                "nombre": "Colaciones",
                "descripcion": "Productos para colación.",
                "activa": "on",
            },
            follow=True,
        )
        self.assertContains(response, "Categoría creada correctamente.")
        categoria = Categoria.objects.get(nombre="Colaciones")

        response = self.client.get(
            reverse("categoria_eliminar", args=[categoria.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Categoria.objects.filter(pk=categoria.pk).exists())

        response = self.client.post(
            reverse("categoria_editar", args=[categoria.pk]),
            {
                "nombre": "Colaciones frías",
                "descripcion": "Productos fríos para colación.",
                "activa": "on",
            },
            follow=True,
        )
        self.assertContains(response, "Categoría actualizada correctamente.")

        response = self.client.post(
            reverse("categoria_eliminar", args=[categoria.pk]),
            follow=True,
        )
        self.assertContains(response, "Categoría eliminada correctamente.")
        self.assertFalse(Categoria.objects.filter(pk=categoria.pk).exists())

    def test_category_with_products_shows_delete_error(self):
        response = self.client.post(
            reverse("categoria_eliminar", args=[self.categoria.pk]),
            follow=True,
        )

        self.assertContains(
            response,
            "No se puede eliminar la categoría porque tiene productos.",
        )
        self.assertTrue(Categoria.objects.filter(pk=self.categoria.pk).exists())

    def test_product_list_searches_name_and_code_and_filters_fields(self):
        otro_producto = Producto.objects.create(
            categoria=self.categoria,
            codigo="CAF-202",
            nombre="Té negro",
            precio=1000,
            stock=4,
            disponible=False,
        )

        response = self.client.get(
            reverse("productos_gestion_lista"),
            {"q": "CAF-202", "categoria": self.categoria.pk, "disponible": "no"},
        )
        self.assertContains(response, otro_producto.nombre)
        self.assertNotContains(response, self.producto.nombre)

        response = self.client.get(
            reverse("productos_gestion_lista"),
            {"q": "americano", "disponible": "si"},
        )
        self.assertContains(response, self.producto.nombre)
        self.assertNotContains(response, otro_producto.nombre)

    def test_product_form_shows_code_price_and_stock_errors(self):
        response = self.client.post(
            reverse("producto_gestion_crear"),
            {
                "categoria": self.categoria.pk,
                "codigo": "CAF-20",
                "nombre": "Producto inválido",
                "precio": "99",
                "stock": "-1",
                "disponible": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "El código debe tener el formato CAF-000.")
        self.assertContains(response, "El precio mínimo es $100.")
        self.assertContains(response, "El stock no puede ser negativo.")
        self.assertFalse(
            Producto.objects.filter(nombre="Producto inválido").exists()
        )

        response = self.client.post(
            reverse("producto_gestion_crear"),
            {
                "categoria": self.categoria.pk,
                "codigo": "CAF-203",
                "nombre": "Producto caro",
                "precio": "20001",
                "stock": "1",
                "disponible": "on",
            },
        )
        self.assertContains(response, "El precio máximo es $20.000.")

    def test_product_can_be_created_and_edited(self):
        response = self.client.post(
            reverse("producto_gestion_crear"),
            {
                "categoria": self.categoria.pk,
                "codigo": "CAF-203",
                "nombre": "Jugo de naranja",
                "precio": "2000",
                "stock": "3",
                "disponible": "on",
            },
            follow=True,
        )
        self.assertContains(response, "Producto creado correctamente.")
        producto = Producto.objects.get(codigo="CAF-203")

        response = self.client.post(
            reverse("producto_gestion_editar", args=[producto.pk]),
            {
                "categoria": self.categoria.pk,
                "codigo": "CAF-204",
                "nombre": "Jugo natural",
                "precio": "2200",
                "stock": "5",
                "disponible": "on",
            },
            follow=True,
        )
        self.assertContains(response, "Producto actualizado correctamente.")
        producto.refresh_from_db()
        self.assertEqual(producto.codigo, "CAF-204")
        self.assertEqual(producto.stock, 5)

    def test_product_delete_is_confirmed_and_protected_by_orders(self):
        response = self.client.get(
            reverse("producto_gestion_eliminar", args=[self.producto.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Producto.objects.filter(pk=self.producto.pk).exists())

        pedido = Pedido.objects.create(
            cliente=self.cliente,
            hora_retiro="12:30",
            estado="pendiente",
            total=self.producto.precio,
            observacion="",
        )
        DetallePedido.objects.create(
            pedido=pedido,
            producto=self.producto,
            cantidad=1,
            precio_unitario=self.producto.precio,
            subtotal=self.producto.precio,
        )
        response = self.client.post(
            reverse("producto_gestion_eliminar", args=[self.producto.pk]),
            follow=True,
        )
        self.assertContains(
            response,
            "No se puede eliminar el producto porque aparece en un pedido.",
        )
        self.assertTrue(Producto.objects.filter(pk=self.producto.pk).exists())

    def test_categories_and_products_are_not_in_django_admin(self):
        self.assertFalse(admin.site.is_registered(Categoria))
        self.assertFalse(admin.site.is_registered(Producto))
