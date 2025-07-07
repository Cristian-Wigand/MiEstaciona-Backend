# rellenar_historial.py

from app import app, db
from models import HistorialSalida
from datetime import datetime, timedelta
import random
from faker import Faker

fake = Faker("es_CL")

# Configura la tarifa (puedes importarla de app.config si lo deseas)
TARIFA_POR_MINUTO = 50

# Rango de fechas
fecha_inicio = datetime(2023, 1, 1, 6, 0, 0)
fecha_fin = datetime(2025, 7, 1, 23, 59, 59)

# Cantidad de registros
CANTIDAD = 10_000

# Rangos de minutos posibles de estadía
MIN_MINUTOS = 5
MAX_MINUTOS = 8 * 60    # máximo 8 horas

# Plazas posibles
FILAS = list("ABCDE")
NUMEROS = list(range(1, 11))   # A01 a E10

with app.app_context():
    registros = []

    for i in range(CANTIDAD):
        # Generar una hora de entrada aleatoria
        total_segundos = int((fecha_fin - fecha_inicio).total_seconds())
        segundos_aleatorios = random.randint(0, total_segundos)
        hora_entrada = fecha_inicio + timedelta(seconds=segundos_aleatorios)

        # Generar duración aleatoria
        duracion_min = random.randint(MIN_MINUTOS, MAX_MINUTOS)
        hora_salida = hora_entrada + timedelta(minutes=duracion_min)

        total_pagado = round(duracion_min * TARIFA_POR_MINUTO, 0)

        patente = fake.license_plate()
        conductor = fake.name()
        correo = fake.email() if random.random() < 0.7 else None

        fila = random.choice(FILAS)
        numero = random.choice(NUMEROS)
        posicion = f"{fila}{numero:02d}"

        registro = HistorialSalida(
            patente=patente,
            conductor=conductor,
            correo=correo,
            hora_entrada=hora_entrada,
            hora_salida=hora_salida,
            duracion_minutos=duracion_min,
            total_pagado=total_pagado,
            posicion=posicion
        )
        registros.append(registro)

        # Imprime avances cada 1000 registros
        if (i + 1) % 1000 == 0:
            print(f"→ Generados {i + 1} registros...")

    # Guardar en bloque
    db.session.bulk_save_objects(registros)
    db.session.commit()

    print(f"✅ ¡Se insertaron {CANTIDAD} registros ficticios en HistorialSalida!")
