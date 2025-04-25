
document.addEventListener('DOMContentLoaded', () => {
    // Confirmación para cerrar sesión
    document.querySelector('.btn-logout')?.addEventListener('click', () => {
        if (confirm('¿Estás seguro de que deseas cerrar sesión?')) {
            window.location.href = "{{ url_for('logout') }}";
        }
    });

    // Efecto hover mejorado para tarjetas
    const cards = document.querySelectorAll('.stat-card, .action-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transition = 'all 0.3s ease-out';
        });

        card.addEventListener('mouseleave', () => {
            card.style.transition = 'all 0.2s ease-in';
        });
    });
});