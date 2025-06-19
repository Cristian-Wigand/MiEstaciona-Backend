# crear_plazas.py
"""
Añade 5 plazas nuevas (01‑05) para las filas A, B, C, D, E.
Ejecútalo con:  python crear_plazas.py
"""

from app import app, db, Plaza   # importa tu app y el modelo Plaza

def crear_plazas(filas: list[str], cantidad: int = 5):
    """Crea `cantidad` plazas por cada fila indicada."""
    nuevas = []

    for fila in filas:
        for n in range(1, cantidad + 1):
            codigo = f"{fila}{str(n).zfill(2)}"   # Ej: "A01"
            # Evita duplicar
            if not Plaza.query.filter_by(codigo=codigo).first():
                nuevas.append(
                    Plaza(codigo=codigo, fila=fila, numero=n, ocupado=False)
                )

    if nuevas:
        db.session.bulk_save_objects(nuevas)
        db.session.commit()
        print(f"✔️ Agregadas {len(nuevas)} plazas:", ", ".join(p.codigo for p in nuevas))
    else:
        print("ℹ️ Todas las plazas ya existían. No se agregó nada.")

if __name__ == "__main__":
    with app.app_context():
        crear_plazas(["A","B","C","D"], 4)
