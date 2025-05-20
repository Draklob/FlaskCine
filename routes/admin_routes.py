import pymysql
from flask import render_template, redirect, url_for, flash, request
from . import admin_bp  # Blueprint creado en __init__.py
from datetime import datetime
from flask_caching import Cache
from crear_datos_cine import conectar_base_datos_cine


cache = Cache()

def conectar_base_datos_con_SQL(sql):
    conexion = conectar_base_datos_cine()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)

    cursor.execute(sql)
    data = cursor.fetchall()
    cursor.close()
    conexion.close()

    return data

def insertar_registro(tabla, datos: dict):
    conexion = None
    cursor = None
    try:
        conexion = conectar_base_datos_cine()
        cursor = conexion.cursor()

        # Deberia comprobar que existe la tabla primero o asi saber que el fallo empieza por ahi.
        columnas = ', '.join(datos.keys())
        placeholders = ', '.join(['%s'] * len(datos))
        print("Insertando cine...")
        print(datos)
        query = f"INSERT INTO {tabla} ({columnas}) VALUES ({placeholders})"
        cursor.execute(query, tuple(datos.values()))
        conexion.commit()
        return cursor.lastrowid

    except Exception as e:
        print(f"Error: {e}")
        return None

    finally:
        if cursor:
            cursor.close()
        if conexion and conexion.open:
            conexion.close()

def actualizar_registro(tabla, datos: dict ):
    conexion = None
    cursor = None
    try:
        conexion = conectar_base_datos_cine()
        cursor = conexion.cursor()
        identificador = list(datos.keys())[-1]
        # Construimos la clausula SET dinamicamente. Pasamos las keys a una lista para ignorar el ultimo elemento, que es el ID
        set_clause = ', '.join([f"{key} = %s" for key in list(datos.keys())[:-1]])
        valores = list(datos.values())
        query = f"UPDATE {tabla} SET {set_clause} WHERE {identificador} = %s"
        cursor.execute(query, tuple(valores))
        conexion.commit()

        return cursor.rowcount >0

    except Exception as e:
        print(f"Error: {e}")
        return None

    finally:
        print("Cambio realizado")
        if cursor:
            cursor.close()
        if conexion and conexion.open:
            conexion.close()

def eliminar_registro(tabla, id: int):
    pass

def get_cines():
    cines = conectar_base_datos_con_SQL('SELECT c.nombre AS nombre, COUNT(s.id_sala) AS salas FROM cines c LEFT JOIN salas s ON c.id_cine = s.id_cine GROUP BY c.id_cine, c.nombre LIMIT 15')
    return cines

def get_peliculas():
    sql = """
    SELECT p.titulo AS titulo, p.año AS año
        FROM peliculas p LEFT JOIN funciones f ON p.id_pelicula = f.id_pelicula
        GROUP BY p.titulo, p.año ORDER BY p.año, p.titulo
    """
    pelis = conectar_base_datos_con_SQL(sql)
    return pelis

def get_funciones():
    sql = """
        SELECT
            c.nombre,
            p.titulo,
            GROUP_CONCAT(CONCAT(s.numero, ' a las ', TIME_FORMAT(f.fecha_hora,'%H:%i')) ORDER BY f.fecha_hora ASC SEPARATOR '; ') AS horarios
        FROM
            cines c
            INNER JOIN salas s ON c.id_cine = s.id_cine
            INNER JOIN funciones f ON s.id_sala = f.id_sala
            INNER JOIN peliculas p ON f.id_pelicula = p.id_pelicula
        GROUP BY
            c.id_cine ,p.id_pelicula, p.titulo, p.duracion
        ORDER BY
            c.nombre, MIN(f.fecha_hora), p.titulo, p.año;
    """
    funciones = conectar_base_datos_con_SQL(sql)

    for funcion in funciones:
        horarios = funcion.pop('horarios').split(';')
        sesiones = []
        for sesion in horarios:
            sesiones.append(sesion.strip())

        for sesion in sesiones:
            funcion_split = sesion.split(' a las ')
            if len(funcion_split) != 2:
                print("Error en el split al separar sala y hora")
                continue

            # Cogemos la sala donde echan la pelicula
            sala = funcion_split[0]
            # Guardamos la hora de la sesion
            hora = funcion_split[1]
            if not funcion.get('sala'):
                funcion['sala'] = sala

            if not funcion.get('hora'):
                funcion['hora'] = [hora]
            else:
                funcion['hora'].append(hora)

    return funciones

def obtener_cine_por_id(cine_id):
    """ Obtiene los datos de un cine especifico"""
    conexion = None
    try:
        conexion = conectar_base_datos_cine()
        with conexion.cursor() as cursor:
            sql = "SELECT * FROM cines WHERE id_cine = %s"
            cursor.execute(sql, (cine_id,))
            cine = cursor.fetchone() # En este caso devuelve diccionario porque lo tenemos configurado con DictCursor
            return cine
    except Exception as e:
        print(f"Error al obtener cine: {e}")
        return None
    finally:
        if conexion and conexion.open:
            conexion.close()

@admin_bp.route('/dashboard')
def dashboard():
    return render_template('admin/dashboard.html', cines= get_cines(), pelis= get_peliculas(), funciones= get_funciones(), now = datetime.now())

@admin_bp.route('/cines')
def cines():
    # Lógica para obtener cines de la base de datos
    sql = """
    SELECT
        c.id_cine, c.nombre, c.direccion, c.telefono,c.precio_base,
        COUNT(DISTINCT s.id_sala) AS num_salas,
        COUNT(DISTINCT f.id_funcion) AS num_funciones
    FROM
        cines c
        LEFT JOIN salas s ON c.id_cine = s.id_cine
        LEFT JOIN funciones f ON s.id_sala = f.id_sala
    GROUP BY
        c.id_cine,
        c.nombre,
        c.direccion,
        c.telefono,
        c.precio_base
    ORDER BY
        c.id_cine;
    """
    cines = conectar_base_datos_con_SQL(sql)

    return render_template('admin/cines.html', cines = cines)

@admin_bp.route('/cines/formulario')
def gestionar_cines():
    return render_template('admin/form_cines.html')

@admin_bp.route('/cines/nuevo', methods=['POST'])
def nuevo_cine():
    if request.method == 'POST':
        nombre = request.form['nombre']
        direccion = request.form['direccion']
        telefono = request.form['telefono']
        precio_base = request.form['precio_base']

        # Validaciones
        if not nombre or not precio_base:
            flash('Nombre y precio base son obligatorios', 'danger')
            return redirect(url_for('cines.nuevo_cine'))
        try:
            precio_base = float(precio_base)
            if precio_base < 0:
                flash('El precio base no puede ser negativo', 'danger')
                return redirect(url_for('cines.nuevo_cine'))
        except ValueError:
            flash('El precio debe ser un numero valida', 'danger')
            return redirect(url_for('cines.nuevo_cine'))

        datos_cine = { 'nombre': nombre, 'direccion': direccion, 'telefono': telefono, 'precio_base': precio_base }
        insertar_registro('cines', datos_cine)

        flash('Cine agregado correctamente', 'success')
        return redirect(url_for('admin.cines'))

    return render_template('admin/form_cines.html')

@admin_bp.route('/cines/editar/<int:cine_id>', methods=['GET', 'POST'])
def editar_cine(cine_id):
    cine = None

    if request.method == "GET":
        cine = obtener_cine_por_id(cine_id)
        print(f"GET Cine {cine}")
        if not cine:
            print("NO CINE")

    if request.method == "POST":
        nombre = request.form['nombre']
        direccion = request.form['direccion']
        telefono = request.form['telefono']
        precio_base = request.form['precio_base']

        # Validaciones
        if not nombre or not precio_base:
            flash('Nombre y precio base son obligatorios', 'danger')
            return redirect(url_for('cines.editar_cine', cine_id=cine_id))
        try:
            precio_base = float(precio_base)
            if precio_base < 0:
                flash('El precio base no puede ser negativo', 'danger')
                return redirect(url_for('cines.editar_cine', cine_id=cine_id))
        except ValueError:
            flash('El precio debe ser un numero valida', 'danger')
            return redirect(url_for('cines.editar_cine', cine_id=cine_id))

        cine = obtener_cine_por_id(cine_id)
        print(f"Imprimiendo cine: {cine}")
        datos_cine = {}
        # Comprobamos que actualizamos los datos que son diferentes a los que ya tiene el cine.
        if nombre != cine['nombre']:
            datos_cine['nombre'] = nombre
        if direccion != cine['direccion']:
            datos_cine['direccion'] = direccion
        if telefono != cine['telefono']:
            datos_cine['telefono'] = telefono
        if precio_base != cine['precio_base']:
            datos_cine['precio_base'] = precio_base

        # Si al menos tenemos algun dato para cambiar
        if datos_cine:
            datos_cine['cine_id'] = cine_id
            print(datos_cine)
            if actualizar_registro('cines', datos_cine):
                flash('Cine actualizado correctamente', 'success')
            else:
                flash('Error al actualizar el cine', 'danger')
            return redirect(url_for('admin.cines'))
        else:
            print("No hay cambios")
            return redirect(url_for('admin.cines'))

    return render_template('admin/editar_cine.html', cine = cine)

@admin_bp.route('/admin/cines/eliminar/<int:cine_id>', methods=['POST'])
def eliminar_cine(cine_id):
    conexion = None
    cursor = None
    try:
        conexion = conectar_base_datos_cine()
        cursor = conexion.cursor()

        query = f"DELETE FROM cines WHERE id_cine = %s"
        cursor.execute(query, (cine_id,))
        conexion.commit()

        if cursor.rowcount > 0:
            flash('Cine eliminado correctamente', 'success')
        else:
            flash('No se encontro el cine', 'warning')

    except pymysql.Error as e:
        print(f"Error: {e}")
        flash(f"Error al eliminar la pelicula")
        if conexion:
            conexion.rollback()

    finally:
        if cursor:
            cursor.close()
        if conexion and conexion.open:
            conexion.close()

    return redirect(url_for('admin.cines'))

# Rutas similares para películas y funciones
@admin_bp.route('/peliculas')
def mostrar_peliculas():
    query = "SELECT id_pelicula, titulo, año, duracion, genero, director, clasificacion FROM peliculas"
    peliculas = conectar_base_datos_con_SQL(query)

    return render_template('admin/peliculas.html', peliculas = peliculas)

@admin_bp.route('peliculas/form_nueva_pelicula')
def formulario_pelicula():
    return render_template('admin/form_peliculas.html')

@admin_bp.route('/peliculas/nueva_pelicula', methods=['POST'])
def nueva_pelicula():
    if request.method == 'POST':
        titulo = request.form['titulo']
        año = request.form['anho']
        duracion = request.form['duracion']
        genero = request.form['genero']
        director = request.form['director']
        clasificacion = request.form['clasificacion']

        # Validaciones
        if not titulo or not año or not duracion or not genero or not director or not clasificacion:
            flash('Todos los campos son obligatorios', 'danger')
            return redirect(url_for('peliculas.nueva_pelicula'))

        datos_pelicula = {'titulo': titulo, 'año': año, 'duracion': duracion, 'genero': genero, 'director': director, 'clasificacion': clasificacion}
        insertar_registro("peliculas", datos_pelicula)

        flash('Pelicula agregada exitosamente', 'success')
        return redirect(url_for('admin.mostrar_peliculas'))

    # Cuando pulsamos el boton nos manda al formulario de crear pelicula
    return render_template('admin/form_peliculas.html')

@admin_bp.route('/admin/funciones')
def funciones():
    return render_template('admin/funciones.html')