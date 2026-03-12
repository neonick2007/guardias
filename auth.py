from flask import redirect, url_for, render_template
from flask_security import Security, login_required, roles_required, \
    roles_accepted, current_user, SQLAlchemyUserDatastore
from models import db, Usuario, Rol

# Configurar el datastore (conector entre Flask-Security y SQLAlchemy)
user_datastore = SQLAlchemyUserDatastore(db, Usuario, Rol)

def init_auth(app):
    """Inicializa la autenticación en la aplicación"""
    
    # Configuración de Flask-Security
    app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'
    app.config['SECURITY_PASSWORD_SALT'] = 'mi_salt_muy_secreto_cambiame'
    app.config['SECURITY_REGISTERABLE'] = True
    app.config['SECURITY_SEND_REGISTER_EMAIL'] = False  # Cambiar a True si quieres confirmación por email
    app.config['SECURITY_CONFIRMABLE'] = False
    app.config['SECURITY_RECOVERABLE'] = True
    app.config['SECURITY_CHANGEABLE'] = True
    app.config['SECURITY_TRACKABLE'] = True
    
    # Personalizar páginas
    app.config['SECURITY_LOGIN_USER_TEMPLATE'] = 'login.html'
    app.config['SECURITY_REGISTER_USER_TEMPLATE'] = 'register.html'
    
    # Inicializar Flask-Security
    security = Security(app, user_datastore)
    
    return security

# Decoradores personalizados para tus roles específicos
def solo_ver(f):
    """Decorador para usuarios que solo pueden ver"""
    return roles_accepted('ver', 'admin', 'modificar')(f)

def puede_modificar(f):
    """Decorador para usuarios que pueden modificar"""
    return roles_accepted('admin', 'modificar')(f)

def es_admin(f):
    """Decorador para administradores"""
    return roles_required('admin')(f)