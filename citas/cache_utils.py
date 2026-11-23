"""Utilidades de caché para el endpoint /api/citas/."""
from django.core.cache import cache

VERSION_KEY = "citas_api:version"


def get_version():
    """Número de 'generación' del caché. Si cambia, todas las claves viejas
    quedan huérfanas (ya nadie las consulta) y expiran solas por timeout."""
    version = cache.get(VERSION_KEY)
    if version is None:
        version = 1
        cache.set(VERSION_KEY, version, None)  # None = no expira
    return version


def invalidate_citas_cache():
    """Invalida TODAS las combinaciones de filtros/páginas de una sola vez."""
    try:
        cache.incr(VERSION_KEY)
    except ValueError:  # la clave aún no existía
        cache.set(VERSION_KEY, 2, None)


def build_key(estado, page, page_size):
    """Clave única por combinación de parámetros.
    Ej.: citas_api:v3:estado=Pendiente:page=2:size=50"""
    return f"citas_api:v{get_version()}:estado={estado or 'todas'}:page={page}:size={page_size}"
