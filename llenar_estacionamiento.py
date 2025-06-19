'''llenar_estacionamiento.py
Crea vehículos de prueba hasta llenar todas las plazas libres.
Se generan patentes secuenciales (AAA001, AAA002, …) y conductores "prueba1", "prueba2", …

Uso:
    python llenar_estacionamiento.py
'''

from datetime import datetime
from itertools import product

from app import app, db, Plaza, Vehiculo

# -------------------------------------------------------------
# Utilidades para generar patentes "AAA001" … "ZZZ999"
# -------------------------------------------------------------
_letters = [chr(c) for c in range(ord("A"), ord("Z") + 1)]
_patente_iter = ("".join(letters) + f"{num:03d}" for letters in product(_letters, repeat=3) for num in range(1, 1000))

def siguiente_patente():
    """Devuelve la primera patente única disponible."""
    usadas = {p for (p,) in db.session.query(Vehiculo.patente)}
    for p in _patente_iter:
        if p not in usadas:
            return p
    raise RuntimeError("No quedan patentes de prueba disponibles.")

# -------------------------------------------------------------
# Script principal
# -------------------------------------------------------------

def llenar_estacionamiento():
    libres = (
        Plaza.query.filter_by(ocupado=False)
        .order_by(Plaza.fila, Plaza.numero)
        .all()
    )
    if not libres:
        print("⚠️  No hay plazas libres. Nada que hacer.")
        return

    for idx, plaza in enumerate(libres, start=1):
        vehiculo = Vehiculo(
            patente=siguiente_patente(),
            conductor=f"prueba{idx}",
            hora_entrada=datetime.now(),  # ⬅️ hora exacta de ejecución
            plaza=plaza,
        )
        plaza.ocupado = True
        db.session.add(vehiculo)

    db.session.commit()
    print(f"✔️  Se llenaron {len(libres)} plazas libres con vehículos de prueba.")

if __name__ == "__main__":
    with app.app_context():
        llenar_estacionamiento()
