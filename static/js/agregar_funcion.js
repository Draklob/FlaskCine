document.addEventListener('DOMContentLoaded', function() {
    // Variables para almacenar las selecciones
    const selecciones = {
        cine_id: null,
        sala_id: null,
        pelicula_id: null,
        fecha: null,
        hora: null
    };

    // Elementos del DOM
    const stepIndicator = document.getElementById('step-indicator');
    const steps = stepIndicator.querySelectorAll('.step');
    const stepContents = document.querySelectorAll('.step-content');
    const form = document.getElementById('funcion-form');

    // Cargar cines al inicio
    cargarCines();

    // Event listeners
    document.getElementById('cine').addEventListener('change', handleCineChange);
    document.getElementById('sala').addEventListener('change', handleSalaChange);
    document.getElementById('pelicula').addEventListener('change', handlePeliculaChange);
    document.getElementById('fecha').addEventListener('change', handleFechaChange);
    document.getElementById('hora').addEventListener('change', handleHoraChange);

    // Botones de navegación
    document.getElementById('btn-step1').addEventListener('click', () => cambiarPaso(1, 2));
    document.getElementById('btn-step2').addEventListener('click', () => cambiarPaso(2, 3));
    document.getElementById('btn-step3').addEventListener('click', () => cambiarPaso(3, 4));

    // Botones "Anterior"
    document.querySelectorAll('.btn-prev').forEach(btn => {
        btn.addEventListener('click', function() {
            const currentStep = parseInt(this.closest('.step-content').id.replace('step', ''));
            cambiarPaso(currentStep, currentStep - 1);
        });
    });

    // Envío del formulario
    form.addEventListener('submit', handleSubmit);

    // Funciones
    function cargarCines() {
        fetch('/admin/get_cines')
            .then(response => response.json())
            .then(data => {
                const cineSelect = document.getElementById('cine');
                cineSelect.innerHTML = '<option value="" selected disabled>Seleccione un cine</option>';

                data.forEach(cine => {
                    const option = document.createElement('option');
                    option.value = cine.id;
                    option.textContent = cine.nombre;
                    cineSelect.appendChild(option);
                });

                document.getElementById('btn-step1').disabled = true;
            })
            .catch(error => {
                console.error('Error al cargar cines:', error);
                document.getElementById('cine').innerHTML = '<option value="" selected disabled>Error al cargar cines</option>';
            });
    }

    function handleCineChange(e) {
        const cineId = e.target.value;
        selecciones.cine_id = cineId;
        document.getElementById('btn-step1').disabled = !cineId;

        if (cineId) {
            cargarSalas(cineId);
        }
    }

    function cargarSalas(cineId) {
        fetch(`/admin/get_salas_cine?cine_id=${cineId}`)
            .then(response => response.json())
            .then(data => {
                const salaSelect = document.getElementById('sala');
                salaSelect.innerHTML = '<option value="" selected disabled>Seleccione una sala</option>';

                if (data.length === 0) {
                    salaSelect.innerHTML = '<option value="" selected disabled>No hay salas disponibles</option>';
                } else {
                    console.log(data)
                    data.forEach(sala => {
                        const option = document.createElement('option');
                        option.value = sala.id_sala;
                        option.textContent = sala.nombre_sala;
                        salaSelect.appendChild(option);
                    });

                    salaSelect.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error al cargar salas:', error);
                document.getElementById('sala').innerHTML = '<option value="" selected disabled>Error al cargar salas</option>';
            });
    }

    function handleSalaChange(e) {
        selecciones.sala_id = e.target.value;
        document.getElementById('btn-step2').disabled = !selecciones.sala_id;
    }

    function cambiarPaso(current, next) {
        // Validar si necesitamos cargar películas al pasar al paso 3
        if (next === 3 && !document.getElementById('pelicula').querySelector('option:not([disabled])')) {
            cargarPeliculas();
        }

        // Validar si necesitamos configurar fecha al pasar al paso 4
        if (next === 4) {
            console.log("Paso FINAL FECHA HORA")
            const fechaInput = document.getElementById('fecha');
            fechaInput.disabled = false;

            // Establecer fecha mínima como hoy
            const today = new Date().toISOString().split('T')[0];
            fechaInput.min = today;
        }

        // Ocultar paso actual y mostrar siguiente
        document.getElementById(`step${current}`).classList.add('d-none');
        document.getElementById(`step${next}`).classList.remove('d-none');

        // Actualizar indicador de pasos
        steps.forEach(step => {
            step.classList.remove('active', 'completed');

            const stepNum = parseInt(step.dataset.step);
            if (stepNum < next) {
                step.classList.add('completed');
            } else if (stepNum === next) {
                step.classList.add('active');
            }
        });
    }

    function cargarPeliculas() {
        fetch('/admin/get_peliculas')
            .then(response => response.json())
            .then(data => {
                const peliculaSelect = document.getElementById('pelicula');
                peliculaSelect.innerHTML = '<option value="" selected disabled>Seleccione una película</option>';

                data.forEach(pelicula => {
                    const option = document.createElement('option');
                    option.value = pelicula.id_pelicula;
                    option.textContent = pelicula.titulo;
                    peliculaSelect.appendChild(option);
                });

                peliculaSelect.disabled = false;
            })
            .catch(error => {
                console.error('Error al cargar películas:', error);
                document.getElementById('pelicula').innerHTML = '<option value="" selected disabled>Error al cargar películas</option>';
            });
    }

    function handlePeliculaChange(e) {
        selecciones.pelicula_id = e.target.value;
        document.getElementById('btn-step3').disabled = !selecciones.pelicula_id;
    }

    function handleFechaChange(e) {
        selecciones.fecha = e.target.value;
        validarFechaHora();
    }

    function handleHoraChange(e) {
        selecciones.hora = e.target.value;
        validarFechaHora();
    }

    function validarFechaHora() {
        const fechaValida = selecciones.fecha && selecciones.fecha.length > 0;
        const horaValida = selecciones.hora && selecciones.hora.length > 0;
        document.getElementById('btn-submit').disabled = !(fechaValida && horaValida);
    }

    function handleSubmit(e) {
        e.preventDefault();

        const fechaHora = `${selecciones.fecha} ${selecciones.hora}:00`;
        console.log(fechaHora);

        fetch('/admin/funciones/nueva_funcion', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                pelicula_id: selecciones.pelicula_id,
                sala_id: selecciones.sala_id,
                fecha_hora: fechaHora
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw err; });
            }
            return response.json();
        })
        .then(data => {
            // Se puede comprobar también usando if(data.success)
            Swal.fire({
                title: '¡Éxito!',
                text: 'Función agregada correctamente',
                icon: 'success',
                confirmButtonText: 'Aceptar'
                // Aqui podemos sino llamar a una funcion y que nos rediriga desde aqui a las funciones
                // window.location.href = '/adimn/mostrar_funciones'
            }).then(() => {
                // Recargar la página para reiniciar el formulario
                window.location.reload();
            });
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire({
                title: 'Error',
                text: error.error || 'Ocurrió un error al guardar la función',
                icon: 'error',
                confirmButtonText: 'Aceptar'
            });
        });
    }
});