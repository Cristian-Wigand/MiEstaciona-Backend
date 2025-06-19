"""
Elimina plazas según las filas y la cantidad indicada.
Solo elimina plazas desocupadas.
Ejecútalo con:  python eliminar_plazas.py
"""

from app import app, db, Plaza

def eliminar_plazas(filas: list[str], cantidad: int = 5):
    """Elimina `cantidad` plazas por cada fila indicada, solo si están libres."""
    eliminadas     = []
    no_eliminables = []

    for fila in filas:
        for n in range(1, cantidad + 1):
            codigo = f"{fila}{str(n).zfill(2)}"  # Ej: "A01"
            plaza = Plaza.query.filter_by(codigo=codigo).first()

            if plaza:
                if plaza.ocupado:
                    no_eliminables.append(codigo)
                else:
                    eliminadas.append(plaza)

    if eliminadas:
        for p in eliminadas:
            db.session.delete(p)
        db.session.commit()
        print(f"🗑️ Eliminadas {len(eliminadas)} plazas:", ", ".join(p.codigo for p in eliminadas))
    else:
        print("ℹ️ No se eliminó ninguna plaza.")

    if no_eliminables:
        print(f"⚠️ No se pudieron eliminar {len(no_eliminables)} plazas porque están ocupadas:", ", ".join(no_eliminables))

if __name__ == "__main__":
    with app.app_context():
        eliminar_plazas(["A", "B", "C", "D", "E", "F", "Y", "Z"], 100)
