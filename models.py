from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Vehiculo(db.Model):
    __tablename__ = 'vehiculos'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patente = db.Column(db.String(10), nullable=False)
    conductor = db.Column(db.String(50), nullable=False)
    correo = db.Column(db.String(120), nullable=True)

    hora_entrada = db.Column(db.DateTime, nullable=False)
    hora_salida = db.Column(db.DateTime)
    total_pagar = db.Column(db.Float)

    posicion = db.Column(db.String(5), nullable=False)  # Ej: A01, A02, etc.
    activo = db.Column(db.Boolean, default=True)  # True = dentro del estacionamiento

    def __repr__(self):
        return f"<Vehiculo {self.patente} - Posición {self.posicion} - Activo: {self.activo}>"


class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    contraseña_hash = db.Column(db.String(128), nullable=False)
    tipo_usuario = db.Column(db.String(20), nullable=False)  # usuario, trabajador, admin

    def set_password(self, contraseña):
        self.contraseña_hash = generate_password_hash(contraseña)

    def check_password(self, contraseña):
        return check_password_hash(self.contraseña_hash, contraseña)

    def __repr__(self):
        return f"<Usuario {self.nombre} ({self.tipo_usuario})>"
