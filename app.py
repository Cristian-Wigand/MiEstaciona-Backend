from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os

from models import db, Vehiculo, Usuario

app = Flask(__name__)
CORS(app)

# Configuración de la base de datos SQLite

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route('/')
def home():
    return "MiEstaciona API corriendo"

# Endpoint: Registrar ingreso de vehículo
@app.route('/ingreso', methods=['POST'])
def registrar_ingreso():
    data = request.json
    nuevo = Vehiculo(
        patente=data['patente'],
        conductor=data['conductor'],
        hora_entrada=datetime.now()
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({'mensaje': 'Ingreso registrado correctamente'}), 201

# Endpoint: Registrar salida y calcular tarifa
@app.route('/salida/<patente>', methods=['PUT'])
def registrar_salida(patente):
    vehiculo = Vehiculo.query.filter_by(patente=patente, hora_salida=None).first()
    if not vehiculo:
        return jsonify({'error': 'Vehículo no encontrado'}), 404

    vehiculo.hora_salida = datetime.now()
    duracion = (vehiculo.hora_salida - vehiculo.hora_entrada).total_seconds() / 60
    vehiculo.total_pagar = round(duracion * 50, 0)  # Tarifa por minuto
    db.session.commit()
    return jsonify({
        'mensaje': 'Salida registrada',
        'total_pagar': vehiculo.total_pagar
    })

# Endpoint: Historial completo
@app.route('/historial', methods=['GET'])
def historial():
    vehiculos = Vehiculo.query.all()
    resultado = [{
        'patente': v.patente,
        'conductor': v.conductor,
        'entrada': v.hora_entrada,
        'salida': v.hora_salida,
        'total_pagar': v.total_pagar
    } for v in vehiculos]
    return jsonify(resultado)

# Endpoint: Registro de usuario
@app.route('/registro', methods=['POST'])
def registro_usuario():
    data = request.json
    if Usuario.query.filter_by(correo=data['correo']).first():
        return jsonify({'error': 'Correo ya registrado'}), 400

    if data['tipo_usuario'] not in ['usuario', 'trabajador', 'admin']:
        return jsonify({'error': 'Tipo de usuario inválido'}), 400

    nuevo_usuario = Usuario(
        nombre=data['nombre'],
        correo=data['correo'],
        tipo_usuario=data['tipo_usuario']
    )
    nuevo_usuario.set_password(data['contraseña'])
    db.session.add(nuevo_usuario)
    db.session.commit()
    return jsonify({'mensaje': 'Usuario registrado correctamente'}), 201

# Endpoint: Login de usuario
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    usuario = Usuario.query.filter_by(correo=data['correo']).first()

    if usuario and usuario.check_password(data['contraseña']):
        return jsonify({
            'mensaje': 'Inicio de sesión exitoso',
            'id': usuario.id,  # Asegúrate que Usuario tiene atributo id
            'nombre': usuario.nombre,
            'tipo_usuario': usuario.tipo_usuario
            })
    return jsonify({'error': 'Correo o contraseña incorrectos'}), 401

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✔️ Base de datos y tablas creadas.")
    print("Rutas registradas:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.methods} -> {rule}")
    app.run(debug=True)
