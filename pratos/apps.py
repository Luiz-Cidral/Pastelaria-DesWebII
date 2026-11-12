from django.apps import AppConfig


class PratosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pratos"

    def ready(self):
        from . import signals  # noqa: F401
