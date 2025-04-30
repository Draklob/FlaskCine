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
        p.titulo,
        GROUP_CONCAT(CONCAT(s.numero, ' a las ', TIME_FORMAT(f.fecha_hora,'%H:%i')) ORDER BY f.fecha_hora ASC SEPARATOR '; ') AS horarios
    FROM
        cines c
        INNER JOIN salas s ON c.id_cine = s.id_cine
        INNER JOIN funciones f ON s.id_sala = f.id_sala
        INNER JOIN peliculas p ON f.id_pelicula = p.id_pelicula
    GROUP BY
        p.id_pelicula, p.titulo, p.duracion
    ORDER BY
        p.año, p.titulo, MIN(f.fecha_hora);
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
            # Comprobamos que si ya existe, de ser asi le introducimos la siguiente hora de la funcion de esa peli.
            if funcion.get(sala):
                funcion[sala].append(hora)
            else:
                # Si aun no existe esa sala registrada, guardamos la sala y la primera hora de esa sala
                funcion[sala] = [hora]

        print(funcion)

        # Guardamos la sala en la que se reproduce
        sala = ""
        # if i < len(sesiones):
        #     sala = sesiones[i][:7].strip()
        #

        # salas_horas = {}
        # for horario in horarios:
        #     horario = horario.strip()
        #     if not horario:
        #         continue
        #
        #     partes = horario.split(' a las ')
        #     if len(partes) != 2:
        #         continue
        #
        #     sala = partes[0].strip()
        #     hora = partes[1].strip()
        #
        #     if sala not in salas_horas:
        #         salas_horas[sala] = []
        #     salas_horas[sala].append(hora)
        # print(salas_horas)

    print(funciones)

    return ""

@admin_bp.route('/dashboard')

def dashboard():
    return render_template('admin/dashboard.html', cines= get_cines_cache(), pelis= get_peliculas_cache(), funciones= get_funciones_cache(), now = datetime.now())

@admin_bp.route('/cines')
def cines():
    # Lógica para obtener cines de la base de datos
    return render_template('admin/cines.html')


# Rutas similares para películas y funciones
@admin_bp.route('/admin/peliculas')
def admin_peliculas():
    return render_template('admin/peliculas.html')


@admin_bp.route('/admin/funciones')
def admin_funciones():
    return render_template('admin/funciones.html')