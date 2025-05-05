import pymysql
from flask import render_template, redirect, url_for, flash, request
from . import admin_bp  # Blueprint creado en __init__.py
from datetime import datetime
from flask_caching import Cache
from crear_datos_cine import conectar_base_datos_cine

cache = Cache()

def insertar_registro(tabla, datos: dict):
    try:
        conexion = conectar_base_datos_cine()
        cursor = conexion.cursor()

        columnas = ', '.join(datos.keys())
        placeholders = ', '.join(['%s'] * len(datos))
        print("Insertando cine...")
        print(datos)
        query = f"INSERT INTO {tabla} ({columnas}) VALUES ({placeholders})"
        cursor.execute(query, datos.values())
        conexion.commit()
        return cursor.lastrowid

    except Exception as e:
        print(f"Error: {e}")
        return None

    finally:
        if conexion.is_connected():
            print("Cine agregado!!")
            cursor.close()
            conexion.close()

def conectar_base_datos_con_SQL(sql):
    conexion = conectar_base_datos_cine()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)

    cursor.execute(sql)
    data = cursor.fetchall()
    cursor.close()
    conexion.close()

    return data

def get_cines_cache():
    cines = conectar_base_datos_con_SQL('SELECT c.nombre AS nombre, COUNT(s.id_sala) AS salas FROM cines c LEFT JOIN salas s ON c.id_cine = s.id_cine GROUP BY c.id_cine, c.nombre LIMIT 15')
    return cines

def get_peliculas_cache():
    sql = """
    SELECT p.titulo AS titulo, p.año AS año
        FROM peliculas p LEFT JOIN funciones f ON p.id_pelicula = f.id_pelicula
        GROUP BY p.titulo, p.año ORDER BY p.año, p.titulo
    """
    pelis = conectar_base_datos_con_SQL(sql)
    return pelis

def get_funciones_cache():
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

        horarios_dict = {}
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

    print(funciones)

    return funciones

@admin_bp.route('/dashboard')
def dashboard():
    return render_template('admin/dashboard.html', cines= get_cines_cache(), pelis= get_peliculas_cache(), funciones= get_funciones_cache(), now = datetime.now())

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

@admin_bp.route('/cines/nuevo', methods=['GET', 'POST'])
def nuevo_cine():
    print(request.method)
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
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/form_cines.html')

# Rutas similares para películas y funciones
@admin_bp.route('/admin/peliculas')
def peliculas():
    return render_template('admin/peliculas.html')

@admin_bp.route('/admin/funciones')
def funciones():
    return render_template('admin/funciones.html')