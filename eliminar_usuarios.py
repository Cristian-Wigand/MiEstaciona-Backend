# eliminar_usuario.py
from app import app, db
from models import Usuario

correos_a_eliminar = [
    "juan@example.com",
    "ana@example.com",
    "luis@example.com",
]

with app.app_context():
    for correo in correos_a_eliminar:
        usuario = Usuario.query.filter_by(correo=correo).first()
        if usuario:
            db.session.delete(usuario)
            print(f"🗑️ Usuario {correo} eliminado")
        else:
            print(f"⚠️ Usuario {correo} no encontrado")
    db.session.commit()
    print("✅ Eliminación completada.")
