from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Cita, Paciente


def inicio(request):
    pendientes = Cita.objects.select_related("paciente").filter(estado=Cita.PENDIENTE)
    contexto = {
        "total_pacientes": Paciente.objects.count(),
        "total_citas": Cita.objects.count(),
        "total_pendientes": pendientes.count(),
        "total_confirmadas": Cita.objects.filter(estado=Cita.CONFIRMADA).count(),
        "proximas": pendientes[:3],
    }
    return render(request, "citas/inicio.html", contexto)


def lista_pacientes(request):
    q = request.GET.get("q", "").strip()
    pacientes = Paciente.objects.all()
    if q:
        pacientes = pacientes.filter(Q(nombre__icontains=q) | Q(apellido__icontains=q))
    return render(
        request, "citas/pacientes_lista.html", {"pacientes": pacientes, "q": q}
    )


def detalle_paciente(request, id):
    paciente = get_object_or_404(Paciente, id=id)
    citas = paciente.citas.all()
    return render(
        request,
        "citas/paciente_detalle.html",
        {"paciente": paciente, "citas": citas},
    )


def lista_citas(request):
    citas = Cita.objects.select_related("paciente").all()
    return render(
        request,
        "citas/citas_lista.html",
        {
            "citas": citas,
            "titulo": "Agenda general",
            "descripcion": "Todas las citas programadas, agrupadas por día.",
        },
    )


def citas_pendientes(request):
    citas = Cita.objects.select_related("paciente").filter(estado=Cita.PENDIENTE)
    return render(
        request,
        "citas/citas_lista.html",
        {
            "citas": citas,
            "titulo": "Citas pendientes",
            "descripcion": "Citas que aún esperan confirmación.",
        },
    )


# ---------------------------------------------------------------------------
# API JSON con caché  ->  GET /api/citas/?estado=Pendiente&page=1&page_size=50
# ---------------------------------------------------------------------------
import logging  # noqa: E402

from django.conf import settings  # noqa: E402
from django.core.cache import cache  # noqa: E402
from django.core.paginator import Paginator  # noqa: E402
from django.db.models import Count  # noqa: E402
from django.http import JsonResponse  # noqa: E402
from django.views.decorators.http import require_GET  # noqa: E402

from .cache_utils import build_key  # noqa: E402

logger = logging.getLogger("citas.cache")
ESTADOS_VALIDOS = {e for e, _ in Cita.ESTADOS}


def _generar_payload(estado, page, page_size):
    """Consulta la BD y arma el JSON (la parte 'cara')."""
    qs = Cita.objects.select_related("paciente")
    if estado:
        qs = qs.filter(estado=estado)

    paginador = Paginator(qs, page_size)
    pagina = paginador.get_page(page)

    resumen = {
        fila["estado"]: fila["total"]
        for fila in Cita.objects.values("estado").annotate(total=Count("id"))
    }

    return {
        "total": paginador.count,
        "pagina": pagina.number,
        "total_paginas": paginador.num_pages,
        "page_size": page_size,
        "resumen_por_estado": resumen,
        "resultados": [
            {
                "id": c.id,
                "paciente_id": c.paciente_id,
                "paciente": f"{c.paciente.nombre} {c.paciente.apellido}",
                "fecha": c.fecha.isoformat(),
                "hora": c.hora.strftime("%H:%M"),
                "motivo": c.motivo,
                "estado": c.estado,
            }
            for c in pagina
        ],
    }


@require_GET
def api_citas(request):
    estado = request.GET.get("estado", "").strip()
    if estado and estado not in ESTADOS_VALIDOS:
        return JsonResponse(
            {"error": f"estado inválido. Usa: {sorted(ESTADOS_VALIDOS)}"}, status=400
        )
    try:
        page = max(int(request.GET.get("page", 1)), 1)
        page_size = min(max(int(request.GET.get("page_size", 50)), 1), 500)
    except ValueError:
        return JsonResponse({"error": "page y page_size deben ser enteros"}, status=400)

    if not settings.CITAS_CACHE_ENABLED:  # modo "sin caché" para la medición
        payload = _generar_payload(estado, page, page_size)
        logger.info("[CACHE] DESACTIVADO -> consulta a BD")
        respuesta = JsonResponse(payload, json_dumps_params={"ensure_ascii": False})
        respuesta["X-Cache"] = "DISABLED"
        return respuesta

    key = build_key(estado, page, page_size)
    payload = cache.get(key)

    if payload is not None:
        origen = "HIT"
        logger.info("[CACHE] HIT  -> %s", key)
    else:
        origen = "MISS"
        payload = _generar_payload(estado, page, page_size)
        cache.set(key, payload, settings.CITAS_CACHE_TIMEOUT)
        logger.info("[CACHE] MISS -> consulta a BD y se guarda %s", key)

    respuesta = JsonResponse(payload, json_dumps_params={"ensure_ascii": False})
    respuesta["X-Cache"] = origen  # <- se ve en Postman > Headers
    return respuesta
