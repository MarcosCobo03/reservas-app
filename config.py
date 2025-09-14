import os
import re

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-cambiar-en-produccion'
    
    # Obtener DATABASE_URL de environment variable
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://') or 'sqlite:///instance/reservas.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False