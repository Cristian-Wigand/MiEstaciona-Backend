'''eliminar_vehiculos.py
Vacía por completo el estacionamiento: borra todos los registros de Vehiculo y marca cada plaza como libre.

Uso:
    python eliminar_vehiculos.py
'''

from app import app, db, Plaza, Vehiculo


def vaciar_estacionamiento():
    total = Vehiculo.query.count()
    if total == 0:
        print("ℹ️  No hay vehículos para eliminar. Todas las plazas ya están libres.")
        return

    # Elimina todos los vehículos
    Vehiculo.query.delete()
    # Libera todas las plazas (bulk update)
    Plaza.query.update({Plaza.ocupado: False})
    db.session.commit()

    print(f"✔️  Eliminados {total} vehículos y liberadas todas las plazas.")


if __name__ == "__main__":
    with app.app_context():
        vaciar_estacionamiento()
