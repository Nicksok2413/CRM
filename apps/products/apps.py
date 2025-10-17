from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.products"

    def ready(self) -> None:
        """
        Переопределяем метод ready для импорта и регистрации сигналов.
        Этот метод вызывается, когда приложение готово к работе.
        """
        # Импортируем сигналы здесь, чтобы избежать AppRegistryNotReady
        import apps.products.signals  # noqa
