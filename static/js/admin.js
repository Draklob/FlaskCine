
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

document.querySelectorAll('.delete-btn-cines').forEach(button => {
    button.addEventListener('click', function (event) {
        event.preventDefault(); // Evita que el formulario se envíe inmediatamente
        const cineId = this.getAttribute('data-cine-id');
        const nombreCine = this.getAttribute('data-nombre-cine');
        Swal.fire({
            title: `¿Eliminar ${nombreCine}?`,
            text: 'No podrás recuperar este cine después de eliminarlo.',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                document.getElementById(`delete-form-${cineId}`).submit(); // Envía el formulario
            }
        });
    });
});

const peliculasTbody = document.getElementById('peliculas-tbody');
if (peliculasTbody) {
    peliculasTbody.addEventListener('click', function (event) {
        const button = event.target.closest('.delete-btn-peliculas');
        if (button) {
            event.preventDefault(); // Evita que el formulario se envíe inmediatamente
            const peliculaID = button.getAttribute('data-pelicula-id');
            const tituloPelicula = button.getAttribute('data-pelicula-titulo');
            console.log('Eliminar película:', peliculaID, tituloPelicula);

            Swal.fire({
                title: `¿Eliminar ${tituloPelicula}?`,
                text: 'No podrás recuperar esta película después de eliminarla.',
                icon: 'warning',
                iconHtml: `<img src="${filmIconUrl}" style="width: 64px; height: 64px; border: navy" >`,
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Sí, eliminar',
                cancelButtonText: 'Cancelar',
                customClass: {
                    icon: 'no-border'
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    document.getElementById(`delete-form-${peliculaID}`).submit();
                }
            });
        }
    });
}

