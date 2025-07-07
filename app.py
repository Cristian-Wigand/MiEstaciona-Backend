# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, date  # ✅ importante: añadimos 'date'
import json  # ✅ necesario para json.dumps(...)
import os

from models import db, Plaza, Vehiculo, Usuario, Configuracion, Cuadratura, HistorialSalida
from sqlalchemy import func
from datetime import timedelta
from calendar import monthrange

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://mi-estacionav1.vercel.app"}}) #poner asi para vercel; CORS(app, resources={r"/*": {"origins": "https://mi-estacionav1.vercel.app"}})


# ─────────────────────────────
# Configuración de la base
# ─────────────────────────────
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["TARIFA_POR_MINUTO"] = float(os.getenv("TARIFA_POR_MINUTO", 50))

db.init_app(app)

# ─────────────────────────────
# Utilidades
# ─────────────────────────────

def plaza_libre():
    """Devuelve la primera Plaza libre según orden fila+numero, o None."""
    return (
        Plaza.query.filter_by(ocupado=False)
        .order_by(Plaza.fila, Plaza.numero)
        .first()
    )

def plazas_disponibles():
    return Plaza.query.filter_by(ocupado=False).count()

def calcular_total(hora_entrada: datetime, tarifa: float):
    minutos = (datetime.now() - hora_entrada).total_seconds() / 60
    return minutos, round(minutos * tarifa, 0)

# ─────────────────────────────
# Rutas
# ─────────────────────────────
@app.route("/")
def home():
    return "MiEstaciona API corriendo"

# ---------- Disponibilidad ----------
@app.route("/espacios_disponibles", methods=["GET"])
def espacios_disponibles():
    return jsonify({"disponibles": plazas_disponibles()})

# ---------- Vehículos ----------
@app.route("/registrar_vehiculo", methods=["POST"])
def registrar_vehiculo():
    data = request.get_json()
    plaza = plaza_libre()
    if not plaza:
        return jsonify({"error": "Estacionamiento lleno"}), 400

    try:
        nuevo = Vehiculo(
            patente=data["patente"],
            conductor=data["conductor"],
            correo=data.get("correo"),
            hora_entrada=datetime.fromisoformat(data["hora_entrada"]),
            plaza=plaza,
        )
        plaza.ocupado = True
        db.session.add(nuevo)
        db.session.commit()
        return (
            jsonify(
                {
                    "mensaje": "Vehículo registrado",
                    "numero_estacionamiento": plaza.codigo,
                }
            ),
            201,
        )
    except Exception as e:
        print("Error:", e)
        db.session.rollback()
        return jsonify({"error": "Error al registrar vehículo"}), 500

@app.route("/vehiculo/manual", methods=["POST"])
def registrar_ingreso_manual():
    data  = request.json
    plaza = plaza_libre()
    if not plaza:
        return jsonify({"error": "Estacionamiento lleno"}), 400

    nuevo = Vehiculo(
        patente=data["patente"],
        conductor=data["conductor"],
        hora_entrada=datetime.now(),
        plaza=plaza,
    )
    plaza.ocupado = True
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({"mensaje": "Ingreso manual registrado"}), 201

@app.route("/vehiculo/<patente>", methods=["DELETE"])
def cobrar_y_eliminar(patente):
    vehiculo = Vehiculo.query.filter_by(patente=patente).first()
    if not vehiculo:
        return jsonify({"error": "Vehículo no encontrado"}), 404

    minutos, total = calcular_total(
        vehiculo.hora_entrada, app.config["TARIFA_POR_MINUTO"]
    )

    historial = HistorialSalida(
        patente=vehiculo.patente,
        conductor=vehiculo.conductor,
        correo=vehiculo.correo,
        hora_entrada=vehiculo.hora_entrada,
        hora_salida=datetime.now(),
        duracion_minutos=round(minutos, 2),
        total_pagado=total,
        posicion=vehiculo.posicion
    )
    db.session.add(historial)

    if vehiculo.plaza:
        vehiculo.plaza.ocupado = False

    db.session.delete(vehiculo)
    db.session.commit()

    return jsonify(
        {
            "mensaje": "Cobro realizado y registrado",
            "total_pagar": total,
            "minutos": round(minutos, 2),
        }
    )

@app.route("/historial", methods=["GET"])
def historial():
    vehiculos = (
        Vehiculo.query.join(Plaza)
        .order_by(Plaza.fila, Plaza.numero)
        .all()
    )
    return jsonify(
        [
            {
                "patente": v.patente,
                "conductor": v.conductor,
                "correo": v.correo,
                "entrada": v.hora_entrada.isoformat(timespec="seconds"),
                "posicion": v.posicion,
            }
            for v in vehiculos
        ]
    )

@app.route("/salidas", methods=["GET"])
def ver_salidas():
    salidas = HistorialSalida.query.order_by(HistorialSalida.hora_salida.desc()).all()
    return jsonify([
        {
            "patente": s.patente,
            "conductor": s.conductor,
            "correo": s.correo,
            "entrada": s.hora_entrada.isoformat(timespec="seconds"),
            "salida": s.hora_salida.isoformat(timespec="seconds"),
            "duracion": round(s.duracion_minutos, 2),
            "total": s.total_pagado,
            "posicion": s.posicion,
        }
        for s in salidas
    ])

@app.route("/estadisticas/salidas", methods=["GET"])
def estadisticas_salidas():
    modo = request.args.get("modo", "semana")
    inicio_str = request.args.get("inicio")

    hoy = datetime.now()

    if modo == "semana":
        if inicio_str:
            try:
                inicio = datetime.fromisoformat(inicio_str)
                inicio = datetime(inicio.year, inicio.month, inicio.day, 0, 0, 0)  # fuerza hora exacta
            except Exception:
                return jsonify({"error": "Fecha de inicio inválida"}), 400
        else:
            inicio = hoy - timedelta(days=6)
        fin = (inicio + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999999)
        agrupamiento = func.date(HistorialSalida.hora_salida)

    elif modo == "mes":
        if inicio_str:
            try:
                inicio = datetime.fromisoformat(inicio_str)
                inicio = datetime(inicio.year, inicio.month, inicio.day, 0, 0, 0)  # fuerza hora exacta
            except Exception:
                return jsonify({"error": "Fecha de inicio inválida"}), 400
        else:
            inicio = hoy - timedelta(weeks=4)
        ultimo_dia = monthrange(inicio.year, inicio.month)[1]
        fin = datetime(inicio.year, inicio.month, ultimo_dia, 23, 59, 59)
        agrupamiento = func.date(HistorialSalida.hora_salida)

    elif modo == "anio":
        if inicio_str:
            try:
                inicio = datetime.fromisoformat(inicio_str)
                inicio = datetime(inicio.year, inicio.month, inicio.day, 0, 0, 0)  # fuerza hora exacta
            except Exception:
                return jsonify({"error": "Fecha de inicio inválida"}), 400
        else:
            inicio = datetime(hoy.year, 1, 1)
        fin = datetime(inicio.year, 12, 31)
        agrupamiento = func.strftime("%Y-%m", HistorialSalida.hora_salida)

    else:
        return jsonify({"error": "Modo inválido"}), 400

    resultados = (
        db.session.query(agrupamiento.label("periodo"), func.count().label("cantidad"))
        .filter(HistorialSalida.hora_salida >= inicio, HistorialSalida.hora_salida <= fin)
        .group_by("periodo")
        .order_by("periodo")
        .all()
    )

    return jsonify([
        {"periodo": r.periodo, "cantidad": r.cantidad} for r in resultados
    ])

# ---------- Usuarios ----------
@app.route("/registro", methods=["POST"])
def registro_usuario():
    data = request.json
    if Usuario.query.filter_by(correo=data["correo"]).first():
        return jsonify({"error": "Correo ya registrado"}), 400
    if data["tipo_usuario"] not in ["usuario", "trabajador", "admin"]:
        return jsonify({"error": "Tipo de usuario inválido"}), 400

    user = Usuario(
        nombre=data["nombre"],
        correo=data["correo"],
        tipo_usuario=data["tipo_usuario"],
    )
    user.set_password(data["contraseña"])
    db.session.add(user)
    db.session.commit()
    return jsonify({"mensaje": "Usuario registrado"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = Usuario.query.filter_by(correo=data["correo"]).first()
    if user and user.check_password(data["contraseña"]):
        return jsonify(
            {
                "mensaje": "Login exitoso",
                "id": user.id,
                "nombre": user.nombre,
                "tipo_usuario": user.tipo_usuario,
            }
        )
    return jsonify({"error": "Correo o contraseña incorrectos"}), 401

# --- LISTAR ---
@app.route("/usuarios", methods=["GET"])
def listar_usuarios():
    usuarios = Usuario.query.all()
    return jsonify(
        [
            {
                "id": u.id,
                "nombre": u.nombre,
                "correo": u.correo,
                "tipo_usuario": u.tipo_usuario,
            }
            for u in usuarios
        ]
    )

# --- OBTENER ---
@app.route("/usuario/<int:uid>", methods=["GET"])
def obtener_usuario(uid):
    usuario = Usuario.query.get(uid)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(
        {
            "id": usuario.id,
            "nombre": usuario.nombre,
            "correo": usuario.correo,
            "tipo_usuario": usuario.tipo_usuario,
        }
    )

# --- ACTUALIZAR ---
@app.route("/usuario/<int:uid>", methods=["PUT"])
def actualizar_usuario(uid):
    data = request.json
    usuario = Usuario.query.get(uid)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    if (
        not data.get("contraseña_actual")
        or not usuario.check_password(data["contraseña_actual"])
    ):
        return jsonify({"error": "Contraseña actual incorrecta"}), 401

    if data.get("correo") and data["correo"] != usuario.correo:
        if Usuario.query.filter_by(correo=data["correo"]).first():
            return jsonify({"error": "Ese correo ya está en uso"}), 400
        usuario.correo = data["correo"]

    usuario.nombre = data.get("nombre", usuario.nombre)

    nueva = data.get("nueva_contraseña", "")
    if nueva:
        usuario.set_password(nueva)

    db.session.commit()
    return jsonify({"mensaje": "Usuario actualizado correctamente"})

# --- ELIMINAR ---
@app.route("/usuario/<int:uid>", methods=["DELETE"])
def eliminar_usuario(uid):
    usuario = Usuario.query.get(uid)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404
    db.session.delete(usuario)
    db.session.commit()
    return jsonify({"mensaje": "Usuario eliminado"})

@app.route("/plazas", methods=["GET"])
def obtener_plazas():
    plazas = Plaza.query.order_by(Plaza.fila, Plaza.numero).all()
    return jsonify([
        {
            "codigo": p.codigo,
            "fila": p.fila,
            "numero": p.numero,
            "ocupado": p.ocupado
        } for p in plazas
    ])

@app.route("/estadisticas", methods=["GET"])
def estadisticas():
    total = Plaza.query.count()
    ocupadas = Plaza.query.filter_by(ocupado=True).count()
    libres = total - ocupadas

    ocupacion_por_fila = (
        db.session.query(Plaza.fila, db.func.count())
        .filter(Plaza.ocupado == True)
        .group_by(Plaza.fila)
        .all()
    )

    usuarios = Usuario.query.all()
    tipos = {"admin": 0, "trabajador": 0, "usuario": 0}
    for u in usuarios:
        if u.tipo_usuario in tipos:
            tipos[u.tipo_usuario] += 1

    return jsonify({
        "total_plazas": total,
        "ocupadas": ocupadas,
        "libres": libres,
        "por_fila": [{"fila": f, "cantidad": c} for f, c in ocupacion_por_fila],
        "usuarios": tipos,
    })

@app.route("/configuracion", methods=["GET"])
def obtener_config():
    config = Configuracion.query.first()
    if config:
        return jsonify({
            "nombre": config.nombre,
            "apertura": config.apertura,
            "cierre": config.cierre,
            "tarifa": config.tarifa
        })
    return jsonify({"error": "Configuración no encontrada"}), 404

@app.route("/configuracion", methods=["PUT"])
def actualizar_config():
    datos = request.get_json()
    print("✅ Datos recibidos:", datos)

    # Elimina claves que no pertenecen al modelo
    datos_filtrados = {
        "nombre": datos.get("nombre"),
        "apertura": datos.get("apertura"),
        "cierre": datos.get("cierre"),
        "tarifa": datos.get("tarifa")
    }

    config = Configuracion.query.first()
    if not config:
        config = Configuracion(**datos_filtrados)
        db.session.add(config)
    else:
        config.nombre = datos_filtrados["nombre"]
        config.apertura = datos_filtrados["apertura"]
        config.cierre = datos_filtrados["cierre"]
        config.tarifa = datos_filtrados["tarifa"]

    db.session.commit()
    return jsonify({"mensaje": "Configuración actualizada correctamente"})

# ─────────────────────────────



@app.route("/cuadratura", methods=["POST"])
def registrar_cuadratura():
    data = request.json
    trabajador_id = data["trabajador_id"]
    jornada_str = data["jornada"]          # viene como string "YYYY-MM-DD"
    desglose = data["desglose"]
    total = data["total"]
    contraseña = data["password"]

    trabajador = Usuario.query.get(trabajador_id)
    if not trabajador or not trabajador.check_password(contraseña):
        return jsonify({"error": "Contraseña incorrecta"}), 401

    try:
        jornada_fecha = datetime.strptime(jornada_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Formato de fecha inválido"}), 400

    nueva_cuadratura = Cuadratura(
        trabajador_id=trabajador_id,
        fecha=date.today(),             # fecha del registro
        jornada=jornada_fecha,          # fecha seleccionada como jornada
        desglose=json.dumps(desglose),
        total=total
    )
    db.session.add(nueva_cuadratura)
    db.session.commit()
    return jsonify({"mensaje": "Caja base registrada con éxito"})

# Bootstrap
# ─────────────────────────────
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✔️ Base de datos y tablas listas")
    app.run(debug=True)
