from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

db = SQLAlchemy()

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    dni = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    notifications = db.relationship('AdminNotification', backref='reservation', lazy=True)

class AdminNotification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservation.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    viewed = db.Column(db.Boolean, default=False)

def init_db(app):
    db.init_app(app)
    with app.app_context():
        try:
            # Verificar si las tablas ya existen
            inspector = db.inspect(db.engine)
            if not inspector.has_table('reservation'):
                db.create_all()
                print("Tablas creadas exitosamente")
            else:
                print("Las tablas ya existen")
        except Exception as e:
            print(f"Error al inicializar la base de datos: {e}")
            # Reintentar con SQLite si hay error con PostgreSQL
            if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
                app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/reservas.db'
                db.create_all()
                print("Base de datos SQLite creada como respaldo")