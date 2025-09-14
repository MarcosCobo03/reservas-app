from flask import Flask, render_template, request, jsonify
from database import init_db, db, Reservation, AdminNotification
from datetime import datetime
import re
import os

@app.before_first_request
def create_tables():
    try:
        db.create_all()
        print("Tablas creadas exitosamente")
    except Exception as e:
        print(f"Error creando tablas: {e}")
        
app = Flask(__name__)
app.config.from_object('config.Config')

# Inicializar la base de datos
init_db(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/reservations', methods=['GET'])
def get_reservations():
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

@app.route('/api/reservations', methods=['POST'])
def create_reservation():
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

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
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

@app.route('/api/notifications/<int:notification_id>/view', methods=['POST'])
def mark_notification_viewed(notification_id):
    notification = AdminNotification.query.get(notification_id)
    if notification:
        notification.viewed = True
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Notificación no encontrada'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)