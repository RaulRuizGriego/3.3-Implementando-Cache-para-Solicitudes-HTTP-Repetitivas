Proyecto: **Consultorio médico** (Django + SQLite), `Paciente` y `Cita`.

## 1. optimizacion
Endpoint `GET /api/citas/` (con filtro por `estado`, paginación y resumen por estado).
URL: `http://127.0.0.1:8000/api/citas/?estado=Pendiente&page=1&page_size=500`.

## 2. Caché
`LocMemCache` en memoria de Django, con clave por `estado`, `page` y `page_size`.
Se ve en el header `X-Cache` (`MISS`, `HIT` o `DISABLED`) y en la consola.

## 3. Actualización
Se invalida (cambia de versión) cuando guardas o borras `Cita` o `Paciente` (`post_save` y `post_delete`), o a los 300 s. Mejor editar desde `/admin/` para que esté en el mismo proceso.

## 4. Cómo correrlo
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py cargar_datos --masivo 20000
python manage.py createsuperuser

# Con caché
python manage.py runserver

# Sin caché (PowerShell)
$env:CITAS_CACHE="off"; python manage.py runserver