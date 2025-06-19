# crear_usuario.py
from app import app, db
from models import Usuario

usuarios_a_crear = [
    {"nombre": "Juan", "correo": "juan@example.com", "contraseña": "1234", "tipo_usuario": "usuario"},
    {"nombre": "Ana", "correo": "ana@example.com", "contraseña": "abcd", "tipo_usuario": "trabajador"},
    {"nombre": "Luis", "correo": "luis@example.com", "contraseña": "5678", "tipo_usuario": "usuario"},
    {"nombre": "Juan", "correo": "juan1@example.com", "contraseña": "1234", "tipo_usuario": "usuario"},
    {"nombre": "Ana", "correo": "ana1@example.com", "contraseña": "abcd", "tipo_usuario": "trabajador"},
    {"nombre": "Luis", "correo": "luis1@example.com", "contraseña": "5678", "tipo_usuario": "trabajador"},
    {"nombre": "Juan", "correo": "juan2@example.com", "contraseña": "1234", "tipo_usuario": "usuario"},
    {"nombre": "Ana", "correo": "ana2@example.com", "contraseña": "abcd", "tipo_usuario": "trabajador"},
    {"nombre": "Luis", "correo": "luisadmin@example.com", "contraseña": "5678", "tipo_usuario": "admin"},
]

with app.app_context():
    for u in usuarios_a_crear:
        if Usuario.query.filter_by(correo=u["correo"]).first():
            print(f"⚠️ Usuario con correo {u['correo']} ya existe. Saltando.")
            continue
        nuevo = Usuario(
            nombre=u["nombre"],
            correo=u["correo"],
            tipo_usuario=u["tipo_usuario"]
        )
        nuevo.set_password(u["contraseña"])
        db.session.add(nuevo)
        print(f"✔️ Usuario {u['correo']} agregado")
    db.session.commit()
    print("✅ Usuarios creados correctamente.")
