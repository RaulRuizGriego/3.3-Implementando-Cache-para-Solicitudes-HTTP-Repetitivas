from django.apps import AppConfig


class CitasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "citas"

    def ready(self):
        # Registra las señales que invalidan el caché al cambiar los datos.
        from . import signals  # noqa: F401
