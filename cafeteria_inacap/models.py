from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField()
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos",
    )
    codigo = models.CharField(
        max_length=10,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^CAF-\d{3}$",
                message="El código debe tener el formato CAF-000.",
            )
        ],
    )
    nombre = models.CharField(max_length=100)
    precio = models.IntegerField(
        validators=[
            MinValueValidator(100, message="El precio mínimo es $100."),
            MaxValueValidator(20000, message="El precio máximo es $20.000."),
        ]
    )
    stock = models.IntegerField(
        validators=[
            MinValueValidator(0, message="El stock no puede ser negativo."),
        ]
    )
    disponible = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Pedido(models.Model):
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pedidos",
    )
    fecha = models.DateTimeField(auto_now_add=True)
    hora_retiro = models.TimeField()
    estado = models.CharField(max_length=15)
    total = models.IntegerField()
    observacion = models.TextField()

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"

    def __str__(self):
        return f"Pedido #{self.pk} - {self.cliente}"


class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="detalles",
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="detalles_pedido",
    )
    cantidad = models.IntegerField()
    precio_unitario = models.IntegerField()
    subtotal = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["pedido", "producto"],
                name="detalle_pedido_producto_unico",
            )
        ]
        verbose_name = "detalle de pedido"
        verbose_name_plural = "detalles de pedido"

    def __str__(self):
        return f"{self.producto} x {self.cantidad}"
