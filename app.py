from flask import Flask, render_template, request, jsonify
from database import init_db, db, Reservation, AdminNotification
from datetime import datetime
import re
import os
from pathlib import Path

# Crear la aplicación Flask
app = Flask(__name__)

# Configuración
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-cambiar-en-produccion')

# Configurar la base de datos - compatible con Render
database_url = os.environ.get('DATABASE_URL', '')
if database_url:
    # Si está en Render con PostgreSQL
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # SQLite para desarrollo local
    Path("instance").mkdir(exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/reservas.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar la base de datos
init_db(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/reservations', methods=['GET'])
def get_reservations():
    try:
        reservations = Reservation.query.all()
        result = []
        for res in reservations:
            result.append({
                'id': res.id,
                'start_date': res.start_date.strftime('%Y-%m-%d'),
                'end_date': res.end_date.strftime('%Y-%m-%d'),
                'name': res.name,
                'dni': res.dni,
                'email': res.email,
                'phone': res.phone,
                'created_at': res.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reservations', methods=['POST'])
def create_reservation():
    try:
        data = request.get_json()
        
        # Validaciones
        errors = []
        
        # Validar fechas
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            if start_date > end_date:
                errors.append('La fecha de inicio no puede ser posterior a la fecha final')
        except:
            errors.append('Formato de fecha inválido')
        
        # Validar nombre
        if not data.get('name') or len(data['name'].strip()) < 5:
            errors.append('El nombre debe tener al menos 5 caracteres')
        
        # Validar DNI (7-8 dígitos)
        if not re.match(r'^\d{7,8}$', data.get('dni', '')):
            errors.append('DNI inválido (debe tener 7 u 8 dígitos)')
        
        # Validar email
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data.get('email', '')):
            errors.append('Email inválido')
        
        # Validar teléfono argentino
        if not re.match(r'^(\+54|0)?\s?(11|[2368]\d{2,3})?\s?(\d{4}\s?\d{4}|\d{2}\s?\d{4}\s?\d{4})$', data.get('phone', '')):
            errors.append('Teléfono argentino inválido')
        
        if errors:
            return jsonify({'success': False, 'errors': errors}), 400
        
        # Crear la reserva
        reservation = Reservation(
            start_date=start_date,
            end_date=end_date,
            name=data['name'],
            dni=data['dni'],
            email=data['email'],
            phone=data['phone']
        )
        
        db.session.add(reservation)
        
        # Crear notificación para el admin
        notification = AdminNotification(
            reservation=reservation,
            message=f"Nueva reserva de {data['name']} desde {data['start_date']} hasta {data['end_date']}"
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Reserva creada correctamente'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    try:
        notifications = AdminNotification.query.order_by(AdminNotification.created_at.desc()).all()
        result = []
        for notif in notifications:
            result.append({
                'id': notif.id,
                'message': notif.message,
                'reservation_id': notif.reservation_id,
                'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'viewed': notif.viewed
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/<int:notification_id>/view', methods=['POST'])
def mark_notification_viewed(notification_id):
    try:
        notification = AdminNotification.query.get(notification_id)
        if notification:
            notification.viewed = True
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Notificación no encontrada'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Crear tablas al inicio
with app.app_context():
    try:
        db.create_all()
        print("Tablas de base de datos creadas correctamente")
    except Exception as e:
        print(f"Error creando tablas: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)