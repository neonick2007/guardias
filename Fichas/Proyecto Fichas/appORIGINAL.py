# =============================================================================
# APP.PY - SERVIDOR FLASK PARA GESTIÓN DE BOMBEROS
# =============================================================================
# Este es el archivo principal que ejecuta el servidor web y maneja toda la
# lógica de la aplicación: base de datos, rutas API y procesamiento de datos
# 
# AUTOR: Sistema de Gestión de Voluntarios - Cuerpo de Bomberos de Valencia
# VERSIÓN: 4.0 (COMPLETO - CON TODAS LAS RUTAS)
# FECHA: Marzo 2026
# =============================================================================

# -----------------------------------------------------------------------------
# IMPORTACIÓN DE LIBRERÍAS
# -----------------------------------------------------------------------------
import os
import shutil
import zipfile
from io import BytesIO
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import re
from werkzeug.utils import secure_filename

# =============================================================================
# CONFIGURACIÓN INICIAL DE LA APLICACIÓN
# =============================================================================
app = Flask(__name__)

# Configuración de la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bomberos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración de subida de archivos (fotos)
app.config['UPLOAD_FOLDER'] = 'static/fotos'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Límite: 16MB

# Inicializamos SQLAlchemy
db = SQLAlchemy(app)


# =============================================================================
# MODELO DE DATOS - TABLA VOLUNTARIOS
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
    codigo = db.Column(db.String(20), nullable=False)  # Sin unique para permitir múltiples
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
# FUNCIONES AUXILIARES
# =============================================================================

def limpiar_cedula(cedula):
    """Limpia el formato de la cédula eliminando caracteres no numéricos."""
    import pandas as pd
    if not cedula or pd.isna(cedula):
        return None
    cedula_str = str(cedula).strip()
    cedula_limpia = re.sub(r'[^0-9]', '', cedula_str)
    return cedula_limpia if cedula_limpia else None


def formatear_telefono(telefono):
    """Formatea el número de teléfono para guardarlo de manera consistente."""
    import pandas as pd
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
    import pandas as pd
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
    import pandas as pd
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
# CONSTANTES Y CONFIGURACIÓN DE NEGOCIO
# =============================================================================

# Jerarquía oficial de rangos (de mayor a menor)
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

# -------------------------------------------------------------------------
# RUTAS DE LA APLICACIÓN (ENDPOINTS)
# -------------------------------------------------------------------------

# -------------------------------------------------------------------------
# RUTA PRINCIPAL - PÁGINA DE INICIO
# -------------------------------------------------------------------------
@app.route('/')
def index():
    """Renderiza la página principal con el listado de voluntarios"""
    return render_template('index.html')


# -------------------------------------------------------------------------
# RUTA: FORMULARIO PARA NUEVO VOLUNTARIO
# -------------------------------------------------------------------------
@app.route('/nuevo', methods=['GET'])
def nuevo_voluntario_form():
    """Muestra el formulario para crear un nuevo voluntario"""
    return render_template('nuevo.html')


# -------------------------------------------------------------------------
# RUTA: FORMULARIO PARA EDITAR VOLUNTARIO
# -------------------------------------------------------------------------
@app.route('/editar/<int:id>', methods=['GET'])
def editar_voluntario_form(id):
    """Muestra el formulario para editar un voluntario existente"""
    voluntario = Voluntario.query.get_or_404(id)
    return render_template('editar.html', voluntario=voluntario)


# -------------------------------------------------------------------------
# RUTA: VER FICHA INDIVIDUAL DEL VOLUNTARIO
# -------------------------------------------------------------------------
@app.route('/ficha/<int:id>')
def ver_ficha(id):
    """Muestra la ficha imprimible de un voluntario"""
    voluntario = Voluntario.query.get_or_404(id)
    return render_template('ficha.html', voluntario=voluntario, now=datetime.now)


# -------------------------------------------------------------------------
# API: OBTENER TODOS LOS VOLUNTARIOS (GET)
# -------------------------------------------------------------------------
@app.route('/api/voluntarios', methods=['GET'])
def get_voluntarios():
    """Obtiene todos los voluntarios en formato JSON, ordenados por jerarquía"""
    voluntarios = Voluntario.query.all()
    
    # Función para obtener el peso de la jerarquía
    def get_rank_weight(v):
        if not v.jerarquia:
            return 99 # Sin jerarquía al final
        rank = v.jerarquia.strip().upper()
        return RANK_HIERARCHY.get(rank, 90) # Rangos desconocidos al final pero antes que vacíos
    
    # Ordenar: primero por jerarquía (peso menor es mayor rango), luego por nombre
    voluntarios_sorted = sorted(voluntarios, key=lambda v: (get_rank_weight(v), v.nombre_apellido))
    
    return jsonify([v.to_dict() for v in voluntarios_sorted])


# -------------------------------------------------------------------------
# API: OBTENER UN VOLUNTARIO POR ID (GET)
# -------------------------------------------------------------------------
@app.route('/api/voluntarios/<int:id>', methods=['GET'])
def get_voluntario(id):
    """Obtiene un voluntario específico por ID"""
    voluntario = Voluntario.query.get_or_404(id)
    return jsonify(voluntario.to_dict())


# -------------------------------------------------------------------------
# API: CREAR NUEVO VOLUNTARIO (POST)
# -------------------------------------------------------------------------
@app.route('/api/voluntarios', methods=['POST'])
def create_voluntario():
    """Crea un nuevo voluntario (desde formulario o API)"""
    data = request.form.to_dict()
    
    # Procesamiento de foto
    foto_path = None
    if 'foto' in request.files:
        foto = request.files['foto']
        if foto.filename:
            filename = secure_filename(f"{datetime.now().timestamp()}_{foto.filename}")
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
# API: ACTUALIZAR VOLUNTARIO (PUT) - Para usar desde JavaScript
# -------------------------------------------------------------------------
@app.route('/api/voluntarios/<int:id>', methods=['PUT'])
def update_voluntario(id):
    """Actualiza un voluntario existente (API)"""
    voluntario = Voluntario.query.get_or_404(id)
    data = request.form.to_dict()
    
    # Procesar foto si se subió una nueva
    if 'foto' in request.files:
        foto = request.files['foto']
        if foto.filename:
            if voluntario.foto_path and os.path.exists(voluntario.foto_path):
                try:
                    os.remove(voluntario.foto_path)
                except:
                    pass
            filename = secure_filename(f"{datetime.now().timestamp()}_{foto.filename}")
            foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            data['foto_path'] = f"static/fotos/{filename}"
    
    for key, value in data.items():
        if hasattr(voluntario, key) and key != 'id':
            if 'fecha' in key:
                if value and value.strip():
                    try:
                        value = datetime.strptime(value, '%Y-%m-%d').date()
                    except:
                        value = None
                else:
                    value = None
            elif key in ['edad', 'total_anos_vol']:
                if value and value.strip():
                    try:
                        value = int(value)
                    except:
                        value = None
                else:
                    value = None
            setattr(voluntario, key, value)
    
    db.session.commit()
    return jsonify(voluntario.to_dict())


# -------------------------------------------------------------------------
# API: ELIMINAR VOLUNTARIO (DELETE)
# -------------------------------------------------------------------------
@app.route('/api/voluntarios/<int:id>', methods=['DELETE'])
def delete_voluntario(id):
    """Elimina un voluntario"""
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
# FUNCIÓN PARA ACTUALIZAR ESQUEMA DE BASE DE DATOS
# =============================================================================
def actualizar_esquema_bd():
    """Agrega columnas faltantes a la base de datos"""
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        
        if 'voluntarios' not in inspector.get_table_names():
            print("📋 La tabla 'voluntarios' no existe, se creará con db.create_all()")
            return
        
        columns = [col['name'] for col in inspector.get_columns('voluntarios')]
        print(f"📋 Columnas actuales en la BD: {columns}")
        
        if 'created_at' not in columns:
            try:
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE voluntarios ADD COLUMN created_at DATETIME'))
                    conn.commit()
                print("✅ Columna 'created_at' agregada correctamente")
                
                with db.engine.connect() as conn:
                    conn.execute(text("UPDATE voluntarios SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))
                    conn.commit()
                print("✅ Valores iniciales asignados a 'created_at'")
            except Exception as e:
                print(f"⚠️ Error al agregar 'created_at': {e}")
        
        if 'updated_at' not in columns:
            try:
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE voluntarios ADD COLUMN updated_at DATETIME'))
                    conn.commit()
                print("✅ Columna 'updated_at' agregada correctamente")
                
                with db.engine.connect() as conn:
                    conn.execute(text("UPDATE voluntarios SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL"))
                    conn.commit()
                print("✅ Valores iniciales asignados a 'updated_at'")
            except Exception as e:
                print(f"⚠️ Error al agregar 'updated_at': {e}")
        
        print("✅ Actualización del esquema completada")
        
    except Exception as e:
        print(f"❌ Error en actualización del esquema: {e}")


# =============================================================================
# RUTA: IMPORTAR DATOS DESDE EXCEL
# =============================================================================
@app.route('/importar-excel', methods=['POST'])
def importar_excel():
    """
    Endpoint para importar datos masivos desde archivo Excel.
    """
    import pandas as pd
    import traceback
    
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
def exportar_excel_api():
    """
    Exporta todos los voluntarios a un archivo Excel.
    """
    import pandas as pd
    import io
    
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
        
        output = io.BytesIO()
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
# PUNTO DE ENTRADA PRINCIPAL
# =============================================================================
# -------------------------------------------------------------------------
# RUTA: CREAR BACKUP (EXPORTAR TODO)
# -------------------------------------------------------------------------
@app.route('/api/backup/crear', methods=['GET'])
def crear_backup():
    """Genera un archivo ZIP con la base de datos y las fotos"""
    try:
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Agregar base de datos
            db_path = os.path.join(app.instance_path, 'voluntarios.db')
            if os.path.exists(db_path):
                zf.write(db_path, 'voluntarios.db')
            
            # Agregar fotos
            fotos_dir = app.config['UPLOAD_FOLDER']
            for root, dirs, files in os.walk(fotos_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(fotos_dir))
                    zf.write(file_path, arcname)
        
        memory_file.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'backup_bomberos_{timestamp}.zip'
        )
    except Exception as e:
        print(f"❌ Error al crear backup: {e}")
        return jsonify({'error': str(e)}), 500


# -------------------------------------------------------------------------
# RUTA: RESTAURAR BACKUP (IMPORTAR TODO)
# -------------------------------------------------------------------------
@app.route('/api/backup/restaurar', methods=['POST'])
def restaurar_backup():
    """Restaura la base de datos y fotos desde un archivo ZIP"""
    if 'file' not in request.files:
        return jsonify({'error': 'No se proporcionó archivo'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400
    
    try:
        # Guardar temporalmente
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_restore.zip')
        file.save(temp_path)
        
        with zipfile.ZipFile(temp_path, 'r') as zf:
            # Extraer archivos
            # Nota: Esto sobrescribirá los archivos existentes
            
            # Restaurar Base de Datos
            if 'voluntarios.db' in zf.namelist():
                db_target = os.path.join(app.instance_path, 'voluntarios.db')
                # Cerrar conexiones si es posible o esperar que SQLite maneje el lock
                # En una app de un solo usuario suele funcionar
                with open(db_target, 'wb') as f:
                    f.write(zf.read('voluntarios.db'))
            
            # Restaurar Fotos
            for item in zf.namelist():
                if item.startswith('fotos/') and not item.endswith('/'):
                    target_path = os.path.join('static', item)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with open(target_path, 'wb') as f:
                        f.write(zf.read(item))
        
        # Eliminar temporal
        os.remove(temp_path)
        return jsonify({'message': 'Restauración completada con éxito. Reinicie la aplicación si es necesario.'}), 200
        
    except Exception as e:
        print(f"❌ Error al restaurar backup: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# INFORMAR AL SISTEMA QUE ESTÁ LISTO (PRE-WARM)
# =============================================================================
with app.app_context():
    try:
        # Consulta rápida para inicializar la conexión y SQLAlchemy
        Voluntario.query.limit(1).all()
        print("🚀 Base de datos inicializada y lista.")
    except Exception as e:
        print(f"⚠️ Advertencia al inicializar base de datos: {e}")

if __name__ == '__main__':
    # Crear carpeta de fotos si no existe
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Inicializar base de datos
    with app.app_context():
        db.create_all()
        print("✅ Tablas creadas/verificadas correctamente")
        actualizar_esquema_bd()
    
    print("\n🚀 SERVIDOR INICIADO - Sistema completo")
    print("📁 Rutas disponibles:")
    print("   - Página principal: http://localhost:5000/")
    print("   - Nuevo voluntario: http://localhost:5000/nuevo")
    print("   - Editar voluntario: http://localhost:5000/editar/ID")
    print("   - Ficha: http://localhost:5000/ficha/ID")
    app.run(debug=True, host='0.0.0.0', port=5000)