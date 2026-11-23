import random
from datetime import date, time, timedelta

from django.core.management.base import BaseCommand

from citas.models import Cita, Paciente

PACIENTES = [
    ("Ana", "López", 34, "6641000001", "ana.lopez@correo.com"),
    ("Luis", "Pérez", 45, "6641000002", "luis.perez@correo.com"),
    ("María", "Gómez", 29, "6641000003", "maria.gomez@correo.com"),
    ("Carlos", "Ruiz", 52, "6641000004", "carlos.ruiz@correo.com"),
    ("Sofía", "Díaz", 41, "6641000005", "sofia.diaz@correo.com"),
    ("Jorge", "Hernández", 38, "6641000006", "jorge.hernandez@correo.com"),
    ("Laura", "Torres", 27, "6641000007", "laura.torres@correo.com"),
    ("Pedro", "Ramírez", 60, "6641000008", "pedro.ramirez@correo.com"),
    ("Elena", "Castro", 33, "6641000009", "elena.castro@correo.com"),
    ("Diego", "Morales", 47, "6641000010", "diego.morales@correo.com"),
]

CITAS = [
    (0, 3, 9, "Consulta general", "Pendiente"),
    (0, 10, 10, "Seguimiento de tratamiento", "Confirmada"),
    (1, 4, 11, "Dolor de espalda", "Pendiente"),
    (2, 5, 12, "Revisión de laboratorio", "Cancelada"),
    (3, 6, 9, "Control de presión arterial", "Pendiente"),
    (4, 7, 13, "Consulta dermatológica", "Confirmada"),
    (5, 8, 14, "Chequeo anual", "Pendiente"),
    (6, 9, 15, "Consulta de nutrición", "Confirmada"),
]

MOTIVOS = [
    "Consulta general", "Seguimiento de tratamiento", "Dolor de espalda",
    "Revisión de laboratorio", "Control de presión arterial",
    "Consulta dermatológica", "Chequeo anual", "Consulta de nutrición",
]
ESTADOS = ["Pendiente", "Confirmada", "Cancelada"]


class Command(BaseCommand):
    help = (
        "Carga 10 pacientes y 8 citas de ejemplo. "
        "Con --masivo agrega además miles de citas para que la diferencia "
        "de tiempos con/sin caché sea medible."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--masivo",
            type=int,
            default=0,
            metavar="N",
            help="Agrega N citas adicionales (ej. --masivo 20000)",
        )

    def handle(self, *args, **options):
        if not Paciente.objects.exists():
            pacientes = [
                Paciente.objects.create(
                    nombre=n, apellido=a, edad=e, telefono=t, correo=c
                )
                for n, a, e, t, c in PACIENTES
            ]
            for idx, dia, hora, motivo, estado in CITAS:
                Cita.objects.create(
                    paciente=pacientes[idx],
                    fecha=date(2026, 11, dia),
                    hora=time(hora, 0),
                    motivo=motivo,
                    estado=estado,
                )
            self.stdout.write(self.style.SUCCESS("Datos base cargados."))
        else:
            self.stdout.write(self.style.WARNING("Ya existen datos base."))

        n = options["masivo"]
        if n:
            random.seed(42)  # datos reproducibles
            ids = list(Paciente.objects.values_list("id", flat=True))
            inicio = date(2026, 12, 1)
            Cita.objects.bulk_create(
                [
                    Cita(
                        paciente_id=random.choice(ids),
                        fecha=inicio + timedelta(days=random.randint(0, 365)),
                        hora=time(random.randint(8, 18), random.choice([0, 30])),
                        motivo=random.choice(MOTIVOS),
                        estado=random.choice(ESTADOS),
                    )
                    for _ in range(n)
                ],
                batch_size=1000,
            )
            self.stdout.write(self.style.SUCCESS(f"Se agregaron {n} citas masivas."))

        self.stdout.write(
            f"Total: {Paciente.objects.count()} pacientes, {Cita.objects.count()} citas."
        )
