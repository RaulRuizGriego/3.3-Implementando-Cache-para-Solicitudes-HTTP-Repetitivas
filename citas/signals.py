import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .cache_utils import invalidate_citas_cache
from .models import Cita, Paciente

logger = logging.getLogger("citas.cache")


# El JSON incluye datos de la cita Y del paciente (nombre), por eso se
# invalida al crear/editar/eliminar cualquiera de los dos modelos.
@receiver([post_save, post_delete], sender=Cita)
@receiver([post_save, post_delete], sender=Paciente)
def invalidar_cache(sender, **kwargs):
    invalidate_citas_cache()
    logger.info("[CACHE] INVALIDADO por cambio en %s", sender.__name__)
