# =============================================================================
# APP.PY - SERVIDOR FLASK PARA GESTIÓN DE BOMBEROS
# =============================================================================
# Este es el archivo principal que ejecuta el servidor web y maneja toda la
# lógica de la aplicación: base de datos, autenticación, rutas API y 
# procesamiento de datos
# 
# AUTOR: Sistema de Gestión de Voluntarios - Cuerpo de Bomberos de Valencia
# VERSIÓN: 5.0 (CON AUTENTICACIÓN Y ROLES)
# FECHA: Marzo 2026
# =============================================================================

# -----------------------------------------------------------------------------
# IMPORTACIÓN DE LIBRERÍAS
# -----------------------------------------------------------------------------
import os
import shutil
import zipfile
from io import BytesIO
from datetime import datetime, timedelta
import re
import traceback
import uuid

from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from supabase import create_client, Client
from dotenv import load_dotenv
from functools import wraps
import pandas as pd

# Cargar variables de entorno
load_dotenv()

# =============================================================================
# CONFIGURACIÓN INICIAL DE LA APLICACIÓN
# =============================================================================
app = Flask(__name__)

# Configuración de la base de datos (SQLite local - los datos de voluntarios)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///bomberos.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración de subida de archivos (fotos)
app.config['UPLOAD_FOLDER'] = 'static/fotos'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Límite: 16MB

# Configuración de sesión de Flask
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-key-very-secret')
app.config['SESSION_TYPE'] = 'filesystem'

# Inicializamos SQLAlchemy
db = SQLAlchemy(app)

# =============================================================================
# CONFIGURACIÓN DE SUPABASE (AUTENTICACIÓN)
# =============================================================================
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️ ADVERTENCIA: SUPABASE_URL o SUPABASE_KEY no configurados en .env")

# Cliente de Supabase para autenticación
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

# =============================================================================
# MODELO DE USUARIO LOCAL (SOLO PARA ROLES)
# =============================================================================
class Usuario(db.Model):
    """Modelo local para almacenar roles y datos adicionales de usuarios"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    supabase_uid = db.Column(db.String(255), unique=True, nullable=False)  # ID de Supabase Auth
    email = db.Column(db.String(255), unique=True, nullable=False)
    nombre_completo = db.Column(db.String(255))
    rol = db.Column(db.String(50), default='ver')  # ver, modificar, admin
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acceso = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Usuario {self.email} - {self.rol}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'nombre': self.nombre_completo,
            'rol': self.rol,
            'activo': self.activo
        }

# =============================================================================
# MODELO DE DATOS - TABLA VOLUNTARIOS (TU MODELO ORIGINAL)
# =============================================================================
class Voluntario(db.Model):
    """
    Modelo que representa a un bombero voluntario en la base de datos.
    """
    
    __tablename__ = 'voluntarios'
    
    # -------------------------------------------------------------------------
    # CAMPOS DE IDENTIFICACIÓN BÁSICA
    # -------------------------------------------------------------------------
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False)
    institucion = db.Column(db.String(100))
    jerarquia = db.Column(db.String(50))
    nombre_apellido = db.Column(db.String(200), nullable=False)
    
    # -------------------------------------------------------------------------
    # DATOS PERSONALES
    # -------------------------------------------------------------------------
    cedula = db.Column(db.String(20))
    fecha_nacimiento = db.Column(db.Date)
    edad = db.Column(db.Integer)
    
    # -------------------------------------------------------------------------
    # HISTORIAL DE INGRESOS Y EGRESOS
    # -------------------------------------------------------------------------
    fecha_ingreso_1 = db.Column(db.Date)
    fecha_egreso_1 = db.Column(db.Date)
    fecha_ingreso_2 = db.Column(db.Date)
    fecha_egreso_2 = db.Column(db.Date)
    ultima_fecha_ingreso = db.Column(db.Date)
    total_anos_vol = db.Column(db.Integer)
    
    # -------------------------------------------------------------------------
    # INFORMACIÓN ACADÉMICA Y PROFESIONAL
    # -------------------------------------------------------------------------
    nivel_academico = db.Column(db.String(50))
    carrera = db.Column(db.String(100))
    ultimo_ascenso = db.Column(db.String(50))
    orden_general = db.Column(db.String(50))
    cargo = db.Column(db.String(100))
    
    # -------------------------------------------------------------------------
    # DATOS DE CONTACTO Y MÉDICOS
    # -------------------------------------------------------------------------
    tipo_sangre = db.Column(db.String(10))
    telefono = db.Column(db.String(50))
    correo = db.Column(db.String(100))
    
    # -------------------------------------------------------------------------
    # TALLAS DE UNIFORME
    # -------------------------------------------------------------------------
    talla_pantalon = db.Column(db.String(10))
    talla_camisa = db.Column(db.String(10))
    talla_botas = db.Column(db.String(10))
    talla_gorra = db.Column(db.String(10))
    
    # -------------------------------------------------------------------------
    # ARCHIVOS Y OBSERVACIONES
    # -------------------------------------------------------------------------
    foto_path = db.Column(db.String(200))
    observaciones = db.Column(db.Text)
    
    # -------------------------------------------------------------------------
    # METADATOS DEL REGISTRO
    # -------------------------------------------------------------------------
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # -------------------------------------------------------------------------
    # MÉTODO PARA CONVERTIR A DICCIONARIO (JSON)
    # -------------------------------------------------------------------------
    def to_dict(self):
        """
        Convierte el objeto Voluntario a un diccionario Python para JSON.
        """
        return {
            'id': self.id,
            'codigo': self.codigo,
            'institucion': self.institucion,
            'jerarquia': self.jerarquia,
            'nombre_apellido': self.nombre_apellido,
            'cedula': self.cedula,
            'fecha_nacimiento': self.fecha_nacimiento.isoformat() if self.fecha_nacimiento else None,
            'edad': self.edad,
            'fecha_ingreso_1': self.fecha_ingreso_1.isoformat() if self.fecha_ingreso_1 else None,
            'fecha_egreso_1': self.fecha_egreso_1.isoformat() if self.fecha_egreso_1 else None,
            'fecha_ingreso_2': self.fecha_ingreso_2.isoformat() if self.fecha_ingreso_2 else None,
            'fecha_egreso_2': self.fecha_egreso_2.isoformat() if self.fecha_egreso_2 else None,
            'ultima_fecha_ingreso': self.ultima_fecha_ingreso.isoformat() if self.ultima_fecha_ingreso else None,
            'total_anos_vol': self.total_anos_vol,
            'nivel_academico': self.nivel_academico,
            'carrera': self.carrera,
            'ultimo_ascenso': self.ultimo_ascenso,
            'orden_general': self.orden_general,
            'cargo': self.cargo,
            'tipo_sangre': self.tipo_sangre,
            'telefono': self.telefono,
            'correo': self.correo,
            'talla_pantalon': self.talla_pantalon,
            'talla_camisa': self.talla_camisa,
            'talla_botas': self.talla_botas,
            'talla_gorra': self.talla_gorra,
            'foto_path': self.foto_path,
            'observaciones': self.observaciones
        }


# =============================================================================
# CONSTANTES Y CONFIGURACIÓN DE NEGOCIO
# =============================================================================

# Jerarquía oficial de rangos (de mayor a menor)
# Número MENOR = Mayor rango (1 es CORONEL, 13 es BOMBERO)
RANK_HIERARCHY = {
    'CORONEL': 1,
    'TENIENTE CORONEL': 2,
    'MAYOR': 3,
    'CAPITAN': 4,
    'PRIMER TENIENTE': 5,
    'TENIENTE': 6,
    'SARGENTO MAYOR': 7,
    'SARGENTO PRIMERO': 8,
    'SARGENTO SEGUNDO': 9,
    'CABO PRIMERO': 10,
    'CABO SEGUNDO': 11,
    'DISTINGUIDO': 12,
    'BOMBERO': 13
}


# =============================================================================
# FUNCIONES AUXILIARES (TUS FUNCIONES ORIGINALES)
# =============================================================================

def limpiar_cedula(cedula):
    """Limpia el formato de la cédula eliminando caracteres no numéricos."""
    if not cedula or pd.isna(cedula):
        return None
    cedula_str = str(cedula).strip()
    cedula_limpia = re.sub(r'[^0-9]', '', cedula_str)
    return cedula_limpia if cedula_limpia else None


def formatear_telefono(telefono):
    """Formatea el número de teléfono para guardarlo de manera consistente."""
    if not telefono or pd.isna(telefono):
        return None
    tel_str = str(telefono).strip()
    tel_limpio = re.sub(r'[^0-9]', '', tel_str)
    return tel_limpio if tel_limpio else None


def convertir_fecha_excel(fecha_excel):
    """Convierte un número de Excel a fecha de Python."""
    try:
        if isinstance(fecha_excel, str):
            fecha_excel = re.sub(r'[^0-9.]', '', fecha_excel)
            if not fecha_excel:
                return None
            fecha_excel = float(fecha_excel)
        elif isinstance(fecha_excel, (int, float)):
            fecha_excel = float(fecha_excel)
        else:
            return None
        
        fecha_base = datetime(1899, 12, 30)
        fecha_resultado = fecha_base + timedelta(days=fecha_excel)
        return fecha_resultado.date()
    except:
        return None


def convertir_fecha_texto(fecha_str):
    """Convierte string de fecha a objeto date."""
    if not fecha_str:
        return None
    fecha_str = str(fecha_str).strip()
    formatos = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%y', '%d-%m-%y', '%Y/%m/%d']
    for formato in formatos:
        try:
            return datetime.strptime(fecha_str, formato).date()
        except ValueError:
            continue
    return None


def convertir_fecha(valor):
    """Intenta convertir cualquier valor a fecha usando múltiples estrategias."""
    if valor is None or pd.isna(valor):
        return None
    fecha = convertir_fecha_excel(valor)
    if fecha:
        return fecha
    fecha = convertir_fecha_texto(valor)
    if fecha:
        return fecha
    try:
        if hasattr(valor, 'strftime'):
            return valor.date()
    except:
        pass
    return None


def convertir_numero(valor):
    """Convierte un valor a entero, manejando decimales y strings."""
    if not valor or pd.isna(valor):
        return None
    try:
        if isinstance(valor, float):
            return int(valor)
        elif isinstance(valor, str):
            valor_limpio = re.sub(r'[^0-9]', '', valor)
            return int(valor_limpio) if valor_limpio else None
        elif isinstance(valor, int):
            return valor
    except:
        pass
    return None


# =============================================================================
# DECORADORES DE AUTENTICACIÓN Y PERMISOS
# =============================================================================

def login_required(f):
    """Decorador para verificar que el usuario está autenticado con Supabase"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def requiere_rol(*roles_permitidos):
    """Decorador para verificar que el usuario tiene un rol específico"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                return redirect(url_for('login'))
            
            # Obtener el rol del usuario desde la base de datos local
            user_id = session['user']['id']
            usuario_local = Usuario.query.filter_by(supabase_uid=user_id).first()
            
            if not usuario_local or usuario_local.rol not in roles_permitidos:
                return render_template('error_403.html'), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def solo_ver(f):
    """Decorador para usuarios que solo pueden ver"""
    return requiere_rol('ver', 'modificar', 'admin')(f)


def puede_modificar(f):
    """Decorador para usuarios que pueden modificar"""
    return requiere_rol('modificar', 'admin')(f)


def es_admin(f):
    """Decorador para administradores"""
    return requiere_rol('admin')(f)


# =============================================================================
# RUTAS DE AUTENTICACIÓN
# =============================================================================

# -------------------------------------------------------------------------
# RUTA: LOGIN - PORTAL DE ACCESO
# -------------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Muestra el portal de acceso y maneja la autenticación con Supabase"""
    if 'user' in session:
        return redirect(url_for('index'))
        
    error = None
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Autenticación con Supabase
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response and auth_response.user:
                user_data = auth_response.user
                
                # Verificar/Buscar usuario en base de datos local
                usuario_local = Usuario.query.filter_by(supabase_uid=user_data.id).first()
                
                # Si no existe, crearlo (primer login)
                if not usuario_local:
                    # Extraer nombre del email (parte antes del @)
                    nombre_default = email.split('@')[0]
                    
                    usuario_local = Usuario(
                        supabase_uid=user_data.id,
                        email=email,
                        nombre_completo=user_data.user_metadata.get('full_name', nombre_default),
                        rol='ver',  # Rol por defecto: solo ver
                        activo=True,
                        ultimo_acceso=datetime.utcnow()
                    )
                    db.session.add(usuario_local)
                    db.session.commit()
                    
                    print(f"✅ Nuevo usuario registrado: {email} con rol 'ver'")
                else:
                    # Actualizar último acceso
                    usuario_local.ultimo_acceso = datetime.utcnow()
                    db.session.commit()
                
                # Guardar usuario en sesión de Flask
                session['user'] = {
                    'id': user_data.id,
                    'email': user_data.email,
                    'rol': usuario_local.rol
                }
                
                # Redirigir a la página que intentaba acceder
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('index'))
            else:
                error = "Credenciales inválidas"
        except Exception as e:
            print(f"❌ Error de login: {e}")
            error = f"Error al intentar iniciar sesión: {str(e)}"
            
    return render_template('login.html', error=error)


# -------------------------------------------------------------------------
# RUTA: REGISTRO DE NUEVOS USUARIOS
# -------------------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registro de nuevos usuarios con Supabase Auth"""
    if 'user' in session:
        return redirect(url_for('index'))
    
    error = None
    success = None
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('password_confirm')
        nombre_completo = request.form.get('nombre_completo', '')
        
        # Validaciones básicas
        if password != confirm:
            error = "Las contraseñas no coinciden"
        elif len(password) < 6:
            error = "La contraseña debe tener al menos 6 caracteres"
        else:
            try:
                # Registrar en Supabase Auth
                auth_response = supabase.auth.sign_up({
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {
                            "full_name": nombre_completo
                        }
                    }
                })
                
                if auth_response and auth_response.user:
                    success = "Registro exitoso. Por favor inicia sesión."
                    
                    print(f"✅ Usuario registrado en Supabase: {email}")
                    
                    # Nota: El usuario se creará en la BD local cuando haga login por primera vez
                    # Esto es mejor porque asegura que el email esté verificado (si configuras confirmación)
                    
                    return redirect(url_for('login', registered=True))
                else:
                    error = "Error en el registro con Supabase"
            except Exception as e:
                print(f"❌ Error de registro: {e}")
                error = f"Error al registrar: {str(e)}"
    
    return render_template('register.html', error=error, success=success)


# -------------------------------------------------------------------------
# RUTA: LOGOUT - CERRAR SESIÓN
# -------------------------------------------------------------------------
@app.route('/logout')
def logout():
    """Cierra la sesión del usuario en Supabase y Flask"""
    # Cerrar sesión en Supabase
    try:
        supabase.auth.sign_out()
    except Exception as e:
        print(f"⚠️ Error al cerrar sesión en Supabase: {e}")
    
    # Limpiar sesión de Flask
    session.pop('user', None)
    
    return redirect(url_for('login'))


# -------------------------------------------------------------------------
# RUTA: PERFIL DE USUARIO
# -------------------------------------------------------------------------
@app.route('/perfil')
@login_required
def perfil():
    """Muestra el perfil del usuario actual"""
    user_id = session['user']['id']
    usuario_local = Usuario.query.filter_by(supabase_uid=user_id).first()
    
    return render_template('perfil.html', usuario=usuario_local)


# =============================================================================
# RUTAS DE LA APLICACIÓN (TUS ENDPOINTS ORIGINALES, AHORA PROTEGIDOS)
# =============================================================================

# -------------------------------------------------------------------------
# RUTA PRINCIPAL - PÁGINA DE INICIO
# -------------------------------------------------------------------------
@app.route('/')
@login_required
def index():
    """Renderiza la página principal con el listado de voluntarios"""
    user_id = session['user']['id']
    usuario_local = Usuario.query.filter_by(supabase_uid=user_id).first()
    
    return render_template('index.html', 
                         usuario=usuario_local,
                         puede_modificar=usuario_local and usuario_local.rol in ['modificar', 'admin'],
                         es_admin=usuario_local and usuario_local.rol == 'admin')


# -------------------------------------------------------------------------
# RUTA: FORMULARIO PARA NUEVO VOLUNTARIO
# -------------------------------------------------------------------------
@app.route('/nuevo', methods=['GET'])
@login_required
@puede_modificar
def nuevo_voluntario_form():
    """Muestra el formulario para crear un nuevo voluntario"""
    return render_template('nuevo.html')


# -------------------------------------------------------------------------
# RUTA: FORMULARIO PARA EDITAR VOLUNTARIO
# -------------------------------------------------------------------------
@app.route('/editar/<int:id>', methods=['GET'])
@login_required
@puede_modificar
def editar_voluntario_form(id):
    """Muestra el formulario para editar un voluntario existente"""
    voluntario = Voluntario.query.get_or_404(id)
    return render_template('editar.html', voluntario=voluntario)


# -------------------------------------------------------------------------
# RUTA: VER FICHA INDIVIDUAL DEL VOLUNTARIO
# -------------------------------------------------------------------------
@app.route('/ficha/<int:id>')
@login_required
def ver_ficha(id):
    """Muestra la ficha imprimible de un voluntario"""
    voluntario = Voluntario.query.get_or_404(id)
    user_id = session['user']['id']
    usuario_local = Usuario.query.filter_by(supabase_uid=user_id).first()
    
    return render_template('ficha.html', 
                         voluntario=voluntario, 
                         now=datetime.now,
                         puede_modificar=usuario_local and usuario_local.rol in ['modificar', 'admin'])


# -------------------------------------------------------------------------
# API: OBTENER TODOS LOS VOLUNTARIOS (GET) - CORREGIDO
# -------------------------------------------------------------------------
@app.route('/api/voluntarios', methods=['GET'])
@login_required
def get_voluntarios():
    """Obtiene todos los voluntarios en formato JSON, ordenados jerárquicamente"""
    voluntarios = Voluntario.query.all()
    
    # Función para obtener el peso de la jerarquía
    def get_rank_weight(v):
        if not v.jerarquia:
            return 999  # Sin jerarquía al final
        rank = v.jerarquia.strip().upper()
        return RANK_HIERARCHY.get(rank, 990)  # Rangos desconocidos al final
    
    # Función de ordenamiento personalizada
    def ordenar_voluntario(v):
        rank_weight = get_rank_weight(v)
        rank_name = v.jerarquia.strip().upper() if v.jerarquia else ""
        
        # CASO ESPECIAL: DISTINGUIDOS - ordenar por ID (más antiguo = ID menor)
        if rank_name == "DISTINGUIDO":
            return (rank_weight, v.id)
        
        # CASO GENERAL: resto de rangos - ordenar por rango y luego por ID
        else:
            return (rank_weight, v.id)
    
    # Ordenar voluntarios
    voluntarios_sorted = sorted(voluntarios, key=ordenar_voluntario)
    
    return jsonify([v.to_dict() for v in voluntarios_sorted])


# -------------------------------------------------------------------------
# API: OBTENER UN VOLUNTARIO POR ID (GET)
# -------------------------------------------------------------------------
@app.route('/api/voluntarios/<int:id>', methods=['GET'])
@login_required
def get_voluntario(id):
    """Obtiene un voluntario específico por ID"""
    voluntario = Voluntario.query.get_or_404(id)
    return jsonify(voluntario.to_dict())


# -------------------------------------------------------------------------
# API: CREAR NUEVO VOLUNTARIO (POST)
# -------------------------------------------------------------------------
@app.route('/api/voluntarios', methods=['POST'])
@login_required
@puede_modificar
def create_voluntario():
    """Crea un nuevo voluntario (desde formulario o API)"""
    data = request.form.to_dict()
    
    # Procesamiento de foto
    foto_path = None
    if 'foto' in request.files:
        foto = request.files['foto']
        if foto.filename:
            filename = secure_filename(f"{datetime.now().timestamp()}_{foto.filename}")
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            foto_path = f"static/fotos/{filename}"
    
    # Conversión de fechas
    date_fields = [
        'fecha_nacimiento', 'fecha_ingreso_1', 'fecha_egreso_1',
        'fecha_ingreso_2', 'fecha_egreso_2', 'ultima_fecha_ingreso'
    ]
    
    for field in date_fields:
        if data.get(field):
            try:
                data[field] = datetime.strptime(data[field], '%Y-%m-%d').date()
            except:
                data[field] = None
        else:
            data[field] = None
    
    # Conversión de números
    try:
        data['edad'] = int(data['edad']) if data.get('edad') else None
    except:
        data['edad'] = None
        
    try:
        data['total_anos_vol'] = int(data['total_anos_vol']) if data.get('total_anos_vol') else None
    except:
        data['total_anos_vol'] = None
    
    # Limpieza de cédula y teléfono
    if data.get('cedula'):
        data['cedula'] = limpiar_cedula(data['cedula'])
    if data.get('telefono'):
        data['telefono'] = formatear_telefono(data['telefono'])
    
    # Unificar formato de CAPITÁN
    if data.get('jerarquia'):
        data['jerarquia'] = data['jerarquia'].strip().upper().replace('CAPITÁN', 'CAPITAN')
    
    if foto_path:
        data['foto_path'] = foto_path
    
    voluntario = Voluntario(**data)
    db.session.add(voluntario)
    db.session.commit()
    
    # Redirigir a la ficha del nuevo voluntario
    return redirect(url_for('ver_ficha', id=voluntario.id))


# -------------------------------------------------------------------------
# RUTA: ACTUALIZAR VOLUNTARIO DESDE FORMULARIO (POST)
# -------------------------------------------------------------------------
@app.route('/actualizar/<int:id>', methods=['GET', 'POST'])
@login_required
@puede_modificar
def actualizar_voluntario_post(id):
    """Procesa la actualización de un voluntario desde formulario"""
    if request.method == 'GET':
        return redirect(url_for('editar_voluntario_form', id=id))
        
    voluntario = Voluntario.query.get_or_404(id)
    data = request.form.to_dict()
    
    # Procesar foto si se subió una nueva
    if 'foto' in request.files:
        foto = request.files['foto']
        if foto.filename:
            # Eliminar foto anterior si existe
            if voluntario.foto_path and os.path.exists(voluntario.foto_path):
                try:
                    os.remove(voluntario.foto_path)
                except:
                    pass
            
            # Guardar nueva foto
            filename = secure_filename(f"{datetime.now().timestamp()}_{foto.filename}")
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            data['foto_path'] = f"static/fotos/{filename}"
    
    # Actualizar campos de fecha
    date_fields = [
        'fecha_nacimiento', 'fecha_ingreso_1', 'fecha_egreso_1',
        'fecha_ingreso_2', 'fecha_egreso_2', 'ultima_fecha_ingreso'
    ]
    
    for field in date_fields:
        if field in data:
            if data[field]:
                try:
                    data[field] = datetime.strptime(data[field], '%Y-%m-%d').date()
                except:
                    data[field] = None
            else:
                data[field] = None
    
    # Actualizar campos numéricos
    if 'edad' in data and data['edad']:
        try:
            data['edad'] = int(data['edad'])
        except:
            data['edad'] = None
    else:
        data['edad'] = None
    
    if 'total_anos_vol' in data and data['total_anos_vol']:
        try:
            data['total_anos_vol'] = int(data['total_anos_vol'])
        except:
            data['total_anos_vol'] = None
    else:
        data['total_anos_vol'] = None

    # Limpieza de cédula y teléfono
    if 'cedula' in data and data['cedula']:
        data['cedula'] = limpiar_cedula(data['cedula'])
    if 'telefono' in data and data['telefono']:
        data['telefono'] = formatear_telefono(data['telefono'])
    
    # Unificar formato de CAPITÁN
    if 'jerarquia' in data and data['jerarquia']:
        data['jerarquia'] = data['jerarquia'].strip().upper().replace('CAPITÁN', 'CAPITAN')
    
    # Actualizar el voluntario solo con los campos enviados en el formulario
    form_keys = request.form.keys()
    for key in form_keys:
        if hasattr(voluntario, key) and key != 'id' and not callable(getattr(voluntario, key)):
            setattr(voluntario, key, data.get(key))
    
    # Asegurar que la foto se actualice si fue procesada
    if 'foto_path' in data:
        voluntario.foto_path = data['foto_path']
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al guardar en BD: {e}")
        return jsonify({'error': 'Error al guardar los datos en la base de datos'}), 500
    
    # Redirigir a la ficha actualizada
    return redirect(f"/ficha/{voluntario.id}")


# -------------------------------------------------------------------------
# API: ELIMINAR VOLUNTARIO (DELETE) - SOLO ADMIN
# -------------------------------------------------------------------------
@app.route('/api/voluntarios/<int:id>', methods=['DELETE'])
@login_required
@es_admin
def delete_voluntario(id):
    """Elimina un voluntario (solo administradores)"""
    voluntario = Voluntario.query.get_or_404(id)
    
    # Eliminar foto si existe
    if voluntario.foto_path and os.path.exists(voluntario.foto_path):
        try:
            os.remove(voluntario.foto_path)
        except:
            pass
    
    db.session.delete(voluntario)
    db.session.commit()
    
    return '', 204


# =============================================================================
# RUTAS DE ADMINISTRACIÓN
# =============================================================================

# -------------------------------------------------------------------------
# RUTA: PANEL DE ADMINISTRACIÓN
# -------------------------------------------------------------------------
@app.route('/admin')
@login_required
@es_admin
def panel_admin():
    """Panel de administración para gestionar usuarios y roles"""
    usuarios = Usuario.query.all()
    return render_template('admin/dashboard.html', usuarios=usuarios)


# -------------------------------------------------------------------------
# RUTA: CAMBIAR ROL DE USUARIO (SOLO ADMIN)
# -------------------------------------------------------------------------
@app.route('/admin/cambiar-rol/<int:usuario_id>', methods=['POST'])
@login_required
@es_admin
def cambiar_rol(usuario_id):
    """Cambia el rol de un usuario"""
    usuario = Usuario.query.get_or_404(usuario_id)
    nuevo_rol = request.json.get('rol')
    
    if nuevo_rol not in ['ver', 'modificar', 'admin']:
        return jsonify({'error': 'Rol no válido'}), 400
    
    usuario.rol = nuevo_rol
    db.session.commit()
    
    return jsonify({'success': True, 'nuevo_rol': nuevo_rol})


# =============================================================================
# RUTAS DE IMPORTACIÓN/EXPORTACIÓN (TUS FUNCIONES ORIGINALES)
# =============================================================================

# -------------------------------------------------------------------------
# RUTA: IMPORTAR DATOS DESDE EXCEL (SOLO ADMIN)
# -------------------------------------------------------------------------
@app.route('/importar-excel', methods=['POST'])
@login_required
@es_admin
def importar_excel():
    """
    Endpoint para importar datos masivos desde archivo Excel.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No se proporcionó archivo'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400
    
    try:
        df = pd.read_excel(file, sheet_name=0, header=0)
        df.columns = df.columns.str.strip()
        
        print(f"\n📊 TOTAL DE FILAS EN EL ARCHIVO: {len(df)}")
        
        if 'CODIGO' not in df.columns:
            return jsonify({'error': 'El archivo Excel debe contener una columna llamada "CODIGO"'}), 400
        
        df = df[df['CODIGO'].notna()]
        df = df[df['CODIGO'].astype(str).str.strip() != '']
        
        print(f"📊 FILAS VÁLIDAS A PROCESAR: {len(df)}")
        
        contador = 0
        errores = []
        detalles = []
        
        print("\n🔄 PROCESANDO REGISTROS...")
        
        for idx, row in df.iterrows():
            try:
                data = {}
                
                # Extraer datos
                if 'CODIGO' in df.columns and pd.notna(row.get('CODIGO')):
                    data['codigo'] = str(row['CODIGO']).strip()
                
                if 'INSTITUCION' in df.columns and pd.notna(row.get('INSTITUCION')):
                    data['institucion'] = str(row['INSTITUCION']).strip()
                
                if 'JERARQUIA' in df.columns and pd.notna(row.get('JERARQUIA')):
                    data['jerarquia'] = str(row['JERARQUIA']).strip()
                
                if 'NOMBRE Y APELLIDO' in df.columns and pd.notna(row.get('NOMBRE Y APELLIDO')):
                    data['nombre_apellido'] = str(row['NOMBRE Y APELLIDO']).strip()
                
                if 'CEDULA' in df.columns and pd.notna(row.get('CEDULA')):
                    data['cedula'] = limpiar_cedula(row['CEDULA'])
                
                if 'F/N' in df.columns and pd.notna(row.get('F/N')):
                    data['fecha_nacimiento'] = convertir_fecha(row['F/N'])
                
                if 'EDAD' in df.columns and pd.notna(row.get('EDAD')):
                    data['edad'] = convertir_numero(row['EDAD'])
                
                if 'FECHA DE INGRESO 1' in df.columns and pd.notna(row.get('FECHA DE INGRESO 1')):
                    data['fecha_ingreso_1'] = convertir_fecha(row['FECHA DE INGRESO 1'])
                
                if 'FECHA DE EGRESO 1' in df.columns and pd.notna(row.get('FECHA DE EGRESO 1')):
                    data['fecha_egreso_1'] = convertir_fecha(row['FECHA DE EGRESO 1'])
                
                if 'FECHA DE INGRESO 2' in df.columns and pd.notna(row.get('FECHA DE INGRESO 2')):
                    data['fecha_ingreso_2'] = convertir_fecha(row['FECHA DE INGRESO 2'])
                
                if 'FECHA DE EGRESO 2' in df.columns and pd.notna(row.get('FECHA DE EGRESO 2')):
                    data['fecha_egreso_2'] = convertir_fecha(row['FECHA DE EGRESO 2'])
                
                col_ultima = 'ULTIMA FECHA DE INGRESO HASTA LA ACTUALIDAD'
                if col_ultima in df.columns and pd.notna(row.get(col_ultima)):
                    data['ultima_fecha_ingreso'] = convertir_fecha(row[col_ultima])
                
                if 'TOTAL AÑOS VOL' in df.columns and pd.notna(row.get('TOTAL AÑOS VOL')):
                    data['total_anos_vol'] = convertir_numero(row['TOTAL AÑOS VOL'])
                
                col_nivel = 'NIVEL ACAD\nLISTA DESPLEGABLE'
                if col_nivel in df.columns and pd.notna(row.get(col_nivel)):
                    data['nivel_academico'] = str(row[col_nivel]).strip()
                
                if 'CARRERA' in df.columns and pd.notna(row.get('CARRERA')):
                    data['carrera'] = str(row['CARRERA']).strip()
                
                if 'ULTIMO ASCENSO' in df.columns and pd.notna(row.get('ULTIMO ASCENSO')):
                    valor = row['ULTIMO ASCENSO']
                    if isinstance(valor, float):
                        data['ultimo_ascenso'] = str(int(valor))
                    else:
                        data['ultimo_ascenso'] = str(valor).strip()
                
                if 'O. GENERAL' in df.columns and pd.notna(row.get('O. GENERAL')):
                    data['orden_general'] = str(row['O. GENERAL']).strip()
                
                if 'CARGO' in df.columns and pd.notna(row.get('CARGO')):
                    data['cargo'] = str(row['CARGO']).strip()
                
                if 'TIPEAJE DE SANGRE' in df.columns and pd.notna(row.get('TIPEAJE DE SANGRE')):
                    data['tipo_sangre'] = str(row['TIPEAJE DE SANGRE']).strip()
                
                if 'TELEFONO' in df.columns and pd.notna(row.get('TELEFONO')):
                    data['telefono'] = formatear_telefono(row['TELEFONO'])
                
                if 'CORREO' in df.columns and pd.notna(row.get('CORREO')):
                    data['correo'] = str(row['CORREO']).strip()
                
                if 'T. PANTALON' in df.columns and pd.notna(row.get('T. PANTALON')):
                    valor = row['T. PANTALON']
                    if isinstance(valor, float):
                        data['talla_pantalon'] = str(int(valor))
                    else:
                        data['talla_pantalon'] = str(valor).strip()
                
                if 'T. CAMISA' in df.columns and pd.notna(row.get('T. CAMISA')):
                    data['talla_camisa'] = str(row['T. CAMISA']).strip()
                
                if 'T. BOTAS' in df.columns and pd.notna(row.get('T. BOTAS')):
                    valor = row['T. BOTAS']
                    if isinstance(valor, float):
                        data['talla_botas'] = str(int(valor))
                    else:
                        data['talla_botas'] = str(valor).strip()
                
                if 'T. GORRA' in df.columns and pd.notna(row.get('T. GORRA')):
                    valor = row['T. GORRA']
                    if isinstance(valor, float):
                        data['talla_gorra'] = str(int(valor))
                    else:
                        data['talla_gorra'] = str(valor).strip()
                
                if 'OBSERVACIONES' in df.columns and pd.notna(row.get('OBSERVACIONES')):
                    data['observaciones'] = str(row['OBSERVACIONES']).strip()
                
                # Validaciones
                if not data.get('codigo'):
                    errores.append(f"Fila {idx+2}: Código vacío")
                    continue
                
                if not data.get('nombre_apellido'):
                    errores.append(f"Fila {idx+2}: Nombre vacío")
                    continue
                
                # Crear voluntario
                voluntario = Voluntario(**data)
                db.session.add(voluntario)
                contador += 1
                
                detalles.append({
                    'fila': idx + 2,
                    'codigo': data.get('codigo'),
                    'nombre': data.get('nombre_apellido')
                })
                
                if contador % 10 == 0:
                    print(f"   ✅ {contador} registros procesados...")
                
            except Exception as e:
                errores.append(f"Fila {idx+2}: {str(e)}")
                continue
        
        db.session.commit()
        
        print("\n" + "="*50)
        print(f"📊 RESUMEN:")
        print(f"   ✅ Registros importados: {contador}")
        print(f"   ⚠️  Errores: {len(errores)}")
        print(f"   📋 Total filas procesadas: {len(df)}")
        print("="*50)
        
        return jsonify({
            'importados': contador,
            'total_filas': len(df),
            'errores': errores[:20],
            'total_errores': len(errores),
            'detalles': detalles[:10]
        }), 200 if contador > 0 else 400
        
    except Exception as e:
        print(f"❌ Error general: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# -------------------------------------------------------------------------
# API: EXPORTAR DATOS A EXCEL
# -------------------------------------------------------------------------
@app.route('/api/exportar-excel', methods=['GET'])
@login_required
def exportar_excel_api():
    """
    Exporta todos los voluntarios a un archivo Excel.
    """
    try:
        voluntarios = Voluntario.query.all()
        
        # Preparar lista de diccionarios con nombres de columnas originales
        data_export = []
        for v in voluntarios:
            row = {
                'CODIGO': v.codigo,
                'INSTITUCION': v.institucion,
                'JERARQUIA': v.jerarquia,
                'NOMBRE Y APELLIDO': v.nombre_apellido,
                'CEDULA': v.cedula,
                'F/N': v.fecha_nacimiento.strftime('%d/%m/%Y') if v.fecha_nacimiento else '',
                'EDAD': v.edad,
                'FECHA DE INGRESO 1': v.fecha_ingreso_1.strftime('%d/%m/%Y') if v.fecha_ingreso_1 else '',
                'FECHA DE EGRESO 1': v.fecha_egreso_1.strftime('%d/%m/%Y') if v.fecha_egreso_1 else '',
                'FECHA DE INGRESO 2': v.fecha_ingreso_2.strftime('%d/%m/%Y') if v.fecha_ingreso_2 else '',
                'FECHA DE EGRESO 2': v.fecha_egreso_2.strftime('%d/%m/%Y') if v.fecha_egreso_2 else '',
                'ULTIMA FECHA DE INGRESO HASTA LA ACTUALIDAD': v.ultima_fecha_ingreso.strftime('%d/%m/%Y') if v.ultima_fecha_ingreso else '',
                'TOTAL AÑOS VOL': v.total_anos_vol,
                'NIVEL ACAD\nLISTA DESPLEGABLE': v.nivel_academico,
                'CARRERA': v.carrera,
                'ULTIMO ASCENSO': v.ultimo_ascenso,
                'O. GENERAL': v.orden_general,
                'CARGO': v.cargo,
                'TIPEAJE DE SANGRE': v.tipo_sangre,
                'TELEFONO': v.telefono,
                'CORREO': v.correo,
                'T. PANTALON': v.talla_pantalon,
                'T. CAMISA': v.talla_camisa,
                'T. BOTAS': v.talla_botas,
                'T. GORRA': v.talla_gorra,
                'OBSERVACIONES': v.observaciones
            }
            data_export.append(row)
        
        # Crear DataFrame y guardar en memoria
        df = pd.DataFrame(data_export)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='VOLUNTARIOS')
        
        output.seek(0)
        
        filename = f"Bomberos_Valencia_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"❌ Error al exportar: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# FUNCIÓN PARA ACTUALIZAR ESQUEMA DE BASE DE DATOS
# =============================================================================
def actualizar_esquema_bd():
    """Agrega columnas faltantes a la base de datos"""
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        
        # Verificar tabla voluntarios
        if 'voluntarios' not in inspector.get_table_names():
            print("📋 La tabla 'voluntarios' no existe, se creará con db.create_all()")
            return
        
        columns_voluntarios = [col['name'] for col in inspector.get_columns('voluntarios')]
        print(f"📋 Columnas actuales en voluntarios: {columns_voluntarios}")
        
        if 'created_at' not in columns_voluntarios:
            try:
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE voluntarios ADD COLUMN created_at DATETIME'))
                    conn.commit()
                print("✅ Columna 'created_at' agregada correctamente")
            except Exception as e:
                print(f"⚠️ Error al agregar 'created_at': {e}")
        
        if 'updated_at' not in columns_voluntarios:
            try:
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE voluntarios ADD COLUMN updated_at DATETIME'))
                    conn.commit()
                print("✅ Columna 'updated_at' agregada correctamente")
            except Exception as e:
                print(f"⚠️ Error al agregar 'updated_at': {e}")
        
        # Verificar tabla usuarios
        if 'usuarios' in inspector.get_table_names():
            columns_usuarios = [col['name'] for col in inspector.get_columns('usuarios')]
            print(f"📋 Columnas actuales en usuarios: {columns_usuarios}")
        
        print("✅ Actualización del esquema completada")
        
    except Exception as e:
        print(f"❌ Error en actualización del esquema: {e}")


# =============================================================================
# INICIALIZACIÓN DE LA APLICACIÓN
# =============================================================================
with app.app_context():
    # Crear todas las tablas
    db.create_all()
    print("✅ Tablas creadas/verificadas correctamente")
    
    # Actualizar esquema
    actualizar_esquema_bd()
    
    # Crear usuario administrador por defecto (si no existe)
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@bomberos.com')
    
    # Verificar si ya existe un usuario con ese email en Supabase (opcional)
    # Por ahora, solo creamos una nota para que el primer usuario que se registre sea admin
    print("👤 Sistema de autenticación listo")
    print("📝 Nota: El primer usuario que se registre tendrá rol 'ver' por defecto")
    print("🔧 Para asignar rol 'admin', usa la consola SQL o el panel de administración")


# =============================================================================
# INFORMAR AL SISTEMA QUE ESTÁ LISTO
# =============================================================================
with app.app_context():
    try:
        # Consulta rápida para inicializar la conexión
        Voluntario.query.limit(1).all()
        print("🚀 Base de datos inicializada y lista.")
    except Exception as e:
        print(f"⚠️ Advertencia al inicializar base de datos: {e}")


# =============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# =============================================================================
if __name__ == '__main__':
    # Crear carpeta de fotos si no existe
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    print("\n" + "="*60)
    print("🚀 SERVIDOR INICIADO - Sistema de Gestión de Bomberos")
    print("="*60)
    print("📁 Rutas disponibles:")
    print("   - Página principal: http://localhost:5000/")
    print("   - Login: http://localhost:5000/login")
    print("   - Registro: http://localhost:5000/register")
    print("   - Nuevo voluntario: http://localhost:5000/nuevo")
    print("   - Panel admin: http://localhost:5000/admin")
    print("\n📋 ROLES:")
    print("   - ver: Solo puede consultar información")
    print("   - modificar: Puede crear y editar voluntarios")
    print("   - admin: Acceso total + gestión de usuarios")
    print("\n🔐 Por defecto, los nuevos usuarios tienen rol 'ver'")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)