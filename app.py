from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os

from models import db, Vehiculo, Usuario

app = Flask(__name__)
CORS(app)

# ──────────────────────
# Configuración SQLite
# ──────────────────────
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR,'database.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Tarifa (colócala como variable de entorno si la quieres configurable)
app.config["TARIFA_POR_MINUTO"] = float(os.getenv("TARIFA_POR_MINUTO", 50))

db.init_app(app)

# ──────────────────────
# Utilidades internas
# ──────────────────────
def asignar_posicion_disponible():
    """Devuelve primera plaza libre A01…A10 o None si está lleno."""
    posiciones = [f"A{str(i).zfill(2)}" for i in range(1, 11)]
    ocupadas   = [v.posicion for v in Vehiculo.query.all()]  # Solo vehículos estacionados
    for pos in posiciones:
        if pos not in ocupadas:
            return pos
    return None

def calcular_total(hora_entrada: datetime, tarifa: float) -> tuple[float, float]:
    """Minutos estacionados y total a pagar."""
    minutos = (datetime.now() - hora_entrada).total_seconds() / 60
    return minutos, round(minutos * tarifa, 0)

# ──────────────────────
# Rutas
# ──────────────────────
@app.route("/")
def home():
    return "MiEstaciona API corriendo"

# Alta con plaza automática
@app.route("/registrar_vehiculo", methods=["POST"])
def registrar_vehiculo():
    data      = request.get_json()
    posicion  = asignar_posicion_disponible()
    if not posicion:
        return jsonify({"error": "Estacionamiento lleno"}), 400

    try:
        nuevo = Vehiculo(
            patente      = data["patente"],
            conductor    = data["conductor"],
            correo       = data.get("correo"),
            hora_entrada = datetime.fromisoformat(data["hora_entrada"]),
            posicion     = posicion
        )
        db.session.add(nuevo)
        db.session.commit()
        return jsonify({"mensaje": "Vehículo registrado con éxito",
                        "posicion": posicion}), 201
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Error al registrar vehículo"}), 500

# Alta manual (posición no automática)
@app.route("/vehiculo/manual", methods=["POST"])
def registrar_ingreso_manual():
    data  = request.json
    nuevo = Vehiculo(
        patente      = data["patente"],
        conductor    = data["conductor"],
        hora_entrada = datetime.now(),
        posicion     = "MANUAL"
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({"mensaje": "Ingreso manual registrado"}), 201

# Cobrar y eliminar (botón “Eliminar” en frontend)
@app.route("/vehiculo/<patente>", methods=["DELETE"])
def cobrar_y_eliminar(patente):
    vehiculo = Vehiculo.query.filter_by(patente=patente).first()
    if not vehiculo:
        return jsonify({"error": "Vehículo no encontrado"}), 404

    minutos, total = calcular_total(
        vehiculo.hora_entrada,
        app.config["TARIFA_POR_MINUTO"]
    )

    db.session.delete(vehiculo)
    db.session.commit()

    return jsonify({
        "mensaje": "Cobro realizado y vehículo eliminado",
        "total_pagar": total,
        "minutos": round(minutos, 2)
    })

# Vehículos actualmente estacionados
@app.route("/historial", methods=["GET"])
def historial():
    vehiculos = Vehiculo.query.all()
    return jsonify([
        {
            "patente":   v.patente,
            "conductor": v.conductor,
            "entrada":   v.hora_entrada,
            "posicion":  v.posicion
        } for v in vehiculos
    ])

# ───────────
# Usuarios
# ───────────
@app.route("/registro", methods=["POST"])
def registro_usuario():
    data = request.json
    if Usuario.query.filter_by(correo=data["correo"]).first():
        return jsonify({"error": "Correo ya registrado"}), 400
    if data["tipo_usuario"] not in ["usuario", "trabajador", "admin"]:
        return jsonify({"error": "Tipo de usuario inválido"}), 400

    user = Usuario(
        nombre       = data["nombre"],
        correo       = data["correo"],
        tipo_usuario = data["tipo_usuario"]
    )
    user.set_password(data["contraseña"])
    db.session.add(user)
    db.session.commit()
    return jsonify({"mensaje": "Usuario registrado correctamente"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = Usuario.query.filter_by(correo=data["correo"]).first()
    if user and user.check_password(data["contraseña"]):
        return jsonify({
            "mensaje": "Inicio de sesión exitoso",
            "id":           user.id,
            "nombre":       user.nombre,
            "tipo_usuario": user.tipo_usuario
        })
    return jsonify({"error": "Correo o contraseña incorrectos"}), 401

# 1) Listar todos
@app.route("/usuarios", methods=["GET"])
def listar_usuarios():
    usuarios = Usuario.query.all()
    return jsonify([
        {
            "id":           u.id,
            "nombre":       u.nombre,
            "correo":       u.correo,
            "tipo_usuario": u.tipo_usuario
        } for u in usuarios
    ])

# 2) Actualizar
@app.route("/usuario/<int:uid>", methods=["PUT"])
def actualizar_usuario(uid):
    data     = request.json
    usuario  = Usuario.query.get(uid)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Validar correo único (si lo cambian)
    if data.get("correo") and data["correo"] != usuario.correo:
        if Usuario.query.filter_by(correo=data["correo"]).first():
            return jsonify({"error": "Ese correo ya está en uso"}), 400
        usuario.correo = data["correo"]

    # Campos opcionales
    usuario.nombre       = data.get("nombre", usuario.nombre)
    usuario.tipo_usuario = data.get("tipo_usuario", usuario.tipo_usuario)

    # Si llega una nueva contraseña no vacía, la actualizamos
    nueva_pass = data.get("contraseña")
    if nueva_pass:
        usuario.set_password(nueva_pass)

    db.session.commit()
    return jsonify({"mensaje": "Usuario actualizado correctamente"})

# 3) Eliminar
@app.route("/usuario/<int:uid>", methods=["DELETE"])
def eliminar_usuario(uid):
    usuario = Usuario.query.get(uid)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    db.session.delete(usuario)
    db.session.commit()
    return jsonify({"mensaje": "Usuario eliminado"})

# ───────────
# Bootstrap
# ───────────
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✔️ Base de datos y tablas listas")
    app.run(debug=True)
