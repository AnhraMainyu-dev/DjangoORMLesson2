from collections import defaultdict

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Case, F, IntegerField, Sum, Value, When
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class RestaurantMenuItemQuerySet(models.QuerySet):
    def make_menu_by_restaurant(self):
        available_items = self.filter(availability=True).values_list(
            "restaurant_id", "product_id"
        )
        menus_by_restaurant = defaultdict(set)
        for restaurant_id, product_id in available_items:
            menus_by_restaurant[restaurant_id].add(product_id)
        return menus_by_restaurant


class OrderQuerySet(models.QuerySet):
    def with_sum(self):
        return self.annotate(sum=Sum(F("items__quantity") * F("items__price")))

    def with_status_order(self):
        status_order = Case(
            *[
                When(status=status, then=Value(number))
                for number, status in enumerate(Order.Status.values)
            ],
            output_field=IntegerField(),
        )
        return self.annotate(status_order=status_order).order_by(
            "status_order", "created_at"
        )


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = RestaurantMenuItem.objects.filter(availability=True).values_list(
            "product"
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField("название", max_length=50)

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "категории"

    def __str__(self):
        return self.name


class Restaurant(models.Model):
    name = models.CharField("название", max_length=50)
    address = models.CharField(
        "адрес",
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        "контактный телефон",
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = "ресторан"
        verbose_name_plural = "рестораны"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField("название", max_length=50)
    category = models.ForeignKey(
        ProductCategory,
        verbose_name="категория",
        related_name="products",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        "цена", max_digits=8, decimal_places=2, validators=[MinValueValidator(0)]
    )
    image = models.ImageField("картинка")
    special_status = models.BooleanField(
        "спец.предложение",
        default=False,
        db_index=True,
    )
    description = models.TextField(
        "описание",
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = "товар"
        verbose_name_plural = "товары"

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name="menu_items",
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="menu_items",
        verbose_name="продукт",
    )
    availability = models.BooleanField("в продаже", default=True, db_index=True)

    objects = RestaurantMenuItemQuerySet.as_manager()

    class Meta:
        verbose_name = "пункт меню ресторана"
        verbose_name_plural = "пункты меню ресторана"
        unique_together = [["restaurant", "product"]]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class Order(models.Model):
    class Status(models.TextChoices):
        CREATED = "CREATED", "Не обработан"
        COOKING = "COOKING", "Готовится"
        DELIVERING = "DELIVERING", "У курьера"
        COMPLETED = "COMPLETED", "Доставлен"
        CANCELLED = "CANCELLED", "Отменён"

    FINISHED_STATUSES = [Status.COMPLETED, Status.CANCELLED]

    class PaymentMethod(models.TextChoices):
        CASH = "CASH", "Наличные"
        CARD = "CARD", "Безнал"

    firstname = models.CharField("имя заказчика", max_length=50)
    lastname = models.CharField(
        "фамилия заказчика",
        max_length=50,
    )
    address = models.CharField(
        "адрес заказчика",
        max_length=100,
    )
    phonenumber = PhoneNumberField("контактный номер заказчика", db_index=True)
    status = models.CharField(
        "статус",
        max_length=15,
        choices=Status.choices,
        default=Status.CREATED,
        db_index=True,
    )
    payment_method = models.CharField(
        "способ оплаты",
        max_length=15,
        choices=PaymentMethod.choices,
        blank=True,
        db_index=True,
    )

    comment = models.TextField("комментарий", blank=True)

    created_at = models.DateTimeField(
        "время принятия заказа",
        default=timezone.now,
        db_index=True,
    )
    called_at = models.DateTimeField(
        "время звонка менеджера",
        blank=True,
        null=True,
        db_index=True,
    )
    delivered_at = models.DateTimeField(
        "время доставки",
        blank=True,
        null=True,
        db_index=True,
    )
    restaurant = models.ForeignKey(
        Restaurant,
        related_name="orders",
        verbose_name="готовящий заказ ресторан",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = "оформленный заказ"
        verbose_name_plural = "оформленные заказы"

    def __str__(self):
        return f"Заказ для {self.firstname} {self.lastname}, {self.address}"

    def get_product_ids(self):
        return {item.product_id for item in self.items.all()}


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, related_name="items", on_delete=models.CASCADE, verbose_name="заказ"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="items", verbose_name="товар"
    )
    quantity = models.PositiveIntegerField(
        "количество", validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        "цена", max_digits=8, decimal_places=2, validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = "товар в заказе"
        verbose_name_plural = "товары в заказе"

    def __str__(self):
        return f"Товары в заказе - {self.product.name}, {self.quantity} шт."
