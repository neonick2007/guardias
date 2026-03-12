from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin, SQLAlchemyUserDatastore
from datetime import datetime

db = SQLAlchemy()

# Tabla intermedia para la relación muchos a muchos entre usuarios y roles
roles_usuarios = db.Table('roles_usuarios',
    db.Column('usuario_id', db.Integer(), db.ForeignKey('usuario.id')),
    db.Column('rol_id', db.Integer(), db.ForeignKey('rol.id'))
)

class Rol(db.Model, RoleMixin):
    __tablename__ = 'rol'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    
    # Permisos específicos (ej: "ver", "modificar")
    permissions = db.Column(db.String(255), default="ver")
    
    def __repr__(self):
        return f'<Rol {self.name}>'

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    username = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean(), default=True)
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False)
    confirmed_at = db.Column(db.DateTime())
    
    # Relación con roles
    roles = db.relationship('Rol', secondary=roles_usuarios,
                           backref=db.backref('usuarios', lazy='dynamic'))
    
    # Datos adicionales
    nombre_completo = db.Column(db.String(255))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acceso = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Usuario {self.email}>'