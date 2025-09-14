// Funciones para interactuar con la API
async function submitReservation(reservationData) {
    try {
        const response = await fetch('/api/reservations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(reservationData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Reserva confirmada y notificación enviada al administrador');
            // Recargar notificaciones
            loadNotifications();
            return true;
        } else {
            showNotification('Error: ' + result.errors.join(', '), true);
            return false;
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error de conexión', true);
        return false;
    }
}

async function loadNotifications() {
    try {
        const response = await fetch('/api/notifications');
        const notifications = await response.json();
        
        const notificationsList = document.getElementById('notifications-list');
        notificationsList.innerHTML = '';
        
        notifications.forEach(notif => {
            const notificationElement = document.createElement('div');
            notificationElement.className = `notification-item ${notif.viewed ? 'viewed' : 'new'}`;
            notificationElement.innerHTML = `
                <p>${notif.message}</p>
                <small>${notif.created_at}</small>
                ${notif.viewed ? '' : '<button class="mark-viewed" data-id="' + notif.id + '">Marcar como vista</button>'}
            `;
            notificationsList.appendChild(notificationElement);
        });
        
        // Agregar event listeners a los botones
        document.querySelectorAll('.mark-viewed').forEach(button => {
            button.addEventListener('click', async function() {
                const notificationId = this.getAttribute('data-id');
                await markNotificationViewed(notificationId);
                loadNotifications();
            });
        });
    } catch (error) {
        console.error('Error cargando notificaciones:', error);
    }
}

async function markNotificationViewed(notificationId) {
    try {
        const response = await fetch(`/api/notifications/${notificationId}/view`, {
            method: 'POST'
        });
        return await response.json();
    } catch (error) {
        console.error('Error:', error);
    }
}

// Llamar a loadNotifications cuando la página cargue
document.addEventListener('DOMContentLoaded', function() {
    loadNotifications();
    // El resto del código del calendario...
});