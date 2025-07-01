# models.py
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# ─────────────────────────────────────────────
#  NUEVA TABLA DE PLAZAS
#  - Permite tener filas A, B, C…
#  - Campo “codigo” único (A01, B05, etc.)
#  - Relación 1‑a‑1 con Vehiculo
# ─────────────────────────────────────────────
class Plaza(db.Model):
    __tablename__ = "plazas"

    id      = db.Column(db.Integer, primary_key=True)
    codigo  = db.Column(db.String(5), unique=True, nullable=False)  # Ej: "A01"
    fila    = db.Column(db.String(1), nullable=False)               # "A", "B"…
    numero  = db.Column(db.Integer, nullable=False)                 # 1, 2, 3…
    ocupado = db.Column(db.Boolean, default=False)

    # Relación 1‑a‑1 con Vehiculo (uselist=False)
    vehiculo = db.relationship(
        "Vehiculo",
        back_populates="plaza",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        estado = "Ocupado" if self.ocupado else "Libre"
        return f"<Plaza {self.codigo} – {estado}>"


# ─────────────────────────────────────────────
#  VEHÍCULOS
#  - Ahora guardan plaza_id (FK) en lugar de un string “posicion”
#  - Propiedad .posicion para retro‑compatibilidad
# ─────────────────────────────────────────────
class Vehiculo(db.Model):
    __tablename__ = "vehiculos"

    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patente      = db.Column(db.String(10),  nullable=False)
    conductor    = db.Column(db.String(50),  nullable=False)
    correo       = db.Column(db.String(120), nullable=True)

    hora_entrada = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    hora_salida  = db.Column(db.DateTime)     # Se usa antes de borrar
    total_pagar  = db.Column(db.Float)        # Ídem

    # --- Relación con Plaza ---
    plaza_id = db.Column(db.Integer, db.ForeignKey("plazas.id"), nullable=False)
    plaza    = db.relationship("Plaza", back_populates="vehiculo")

    # Propiedad calculada (para código existente que use “posicion”)
    @property
    def posicion(self):
        return self.plaza.codigo if self.plaza else None

    def __repr__(self):
        return f"<Vehiculo {self.patente} – {self.posicion}>"


# ─────────────────────────────────────────────
#  USUARIOS
# ─────────────────────────────────────────────
class Usuario(db.Model):
    __tablename__ = "usuarios"

    id              = db.Column(db.Integer, primary_key=True)
    nombre          = db.Column(db.String(100), nullable=False)
    correo          = db.Column(db.String(100), unique=True, nullable=False)
    contraseña_hash = db.Column(db.String(128), nullable=False)
    tipo_usuario    = db.Column(db.String(20),  nullable=False)  # usuario | trabajador | admin

    # ------ helpers de contraseña ------
    def set_password(self, contraseña):
        self.contraseña_hash = generate_password_hash(contraseña)

    def check_password(self, contraseña):
        return check_password_hash(self.contraseña_hash, contraseña)

    def __repr__(self):
        return f"<Usuario {self.nombre} ({self.tipo_usuario})>"

class Configuracion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    apertura = db.Column(db.String(5))  # Ej: "08:00"
    cierre = db.Column(db.String(5))    # Ej: "20:00"
    tarifa = db.Column(db.Float)
