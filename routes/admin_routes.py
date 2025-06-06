import traceback

import pymysql
from flask import render_template, redirect, url_for, flash, request, jsonify, current_app, make_response
import os, time
from fpdf import FPDF

from utils import validate_url
from . import admin_bp  # Blueprint creado en __init__.py
from datetime import datetime, date
from flask_caching import Cache
from crear_datos_cine import conectar_base_datos_cine

cache = Cache()
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def archivo_permitido(archivo):
    return '.' in archivo and archivo.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ejecutar_consulta_sql(sql, argumentos= None, fetch= True):
    conexion = None
    cursor = None

    try:
        conexion = conectar_base_datos_cine()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)

        if argumentos is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql, argumentos)

        # Manejar el resultado
        if fetch:
            data = cursor.fetchall()
            return data
        else:
            conexion.commit()
            return cursor.rowcount # Numero de filas afectadas

    except pymysql.Error as e:
        print(f"Error en la consulta: {e}")
        return None

    finally:
        if cursor:
            cursor.close()
        if conexion and conexion.open:
            conexion.close()

def insertar_registro(tabla, datos: dict):
    conexion = None
    cursor = None
    try:
        if not datos:
            raise ValueError("El diccionario de registro no tiene datos.")
        conexion = conectar_base_datos_cine()
        cursor = conexion.cursor()

        # Comprobamos que existe la tabla primero
        cursor.execute("SHOW TABLES LIKE %s", (tabla,) )
        if not cursor.fetchone():
            raise ValueError(f"La tabla {tabla} no existe en la base de datos.")

        # Continuamos y preparamos el sql para lanzarse.
        # Deberia comprobar que existe la tabla primero o asi saber que el fallo empieza por ahi.
        columnas = ', '.join(datos.keys())
        placeholders = ', '.join(['%s'] * len(datos))
        print("Insertando cine...")
        print(datos)
        query = f"INSERT INTO {tabla} ({columnas}) VALUES ({placeholders})"
        cursor.execute(query, tuple(datos.values()))
        conexion.commit()

        if cursor.rowcount == 1:
            return cursor.lastrowid
        else:
            print("❌ No se insertó ninguna fila")
            return None

    except pymysql.Error as err:
        print(f"Error de MySQL: {err}")
        if conexion:
            conexion.rollback()
        return None

    except Exception as e:
        print(f"Error: {e}")
        if conexion:
            conexion.rollback()
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
        print(query)
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
    cines = ejecutar_consulta_sql('SELECT c.nombre AS nombre, COUNT(s.id_sala) AS salas FROM cines c LEFT JOIN salas s ON c.id_cine = s.id_cine GROUP BY c.id_cine, c.nombre LIMIT 15')
    return cines

def get_peliculas():
    sql = """
    SELECT p.titulo AS titulo, p.año AS año, p.id_pelicula
        FROM peliculas p LEFT JOIN funciones f ON p.id_pelicula = f.id_pelicula
        GROUP BY p.titulo, p.año ORDER BY p.año, p.titulo
    """
    pelis = ejecutar_consulta_sql(sql)
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
    funciones = ejecutar_consulta_sql(sql)

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
            print(cine)
            return cine
    except Exception as e:
        print(f"Error al obtener cine: {e}")
        return None
    finally:
        if conexion and conexion.open:
            conexion.close()

def obtener_pelicula(pelicula_id):
    # Buscamos la peli
    sql = """
            SELECT * FROM peliculas WHERE id_pelicula = %s
            """
    peli = ejecutar_consulta_sql(sql, (pelicula_id,))[0]
    print(peli)
    return peli

@admin_bp.route('/dashboard')
def dashboard():
    return render_template('admin/dashboard.html', cines= get_cines(), pelis= get_peliculas(), funciones= get_funciones(), now = datetime.now())

@admin_bp.route('/get_cines')
def obtener_cines():
    try:
        conexion = conectar_base_datos_cine()
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id_cine AS id, nombre FROM cines")
            cines = cursor.fetchall()

        return jsonify(cines)
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        conexion.close()

@admin_bp.route('/get_salas_cine')
def obtener_salas_cine():
    cine_id = request.args.get('cine_id')
    if not cine_id:
        return jsonify({'error': 'No se ha seleccionado ninguna cine'})

    try:
        conexion = conectar_base_datos_cine()
        with conexion.cursor() as cursor:
            cursor.execute("SELECT s.id_sala, s.numero AS nombre_sala FROM cines c LEFT JOIN salas s ON c.id_cine = s.id_cine WHERE c.id_cine= %s", (cine_id,))
            salas = cursor.fetchall()

        return jsonify(salas)
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        conexion.close()

@admin_bp.route('/get_peliculas')
def obtener_peliculas():
    peliculas = get_peliculas()
    return jsonify(peliculas)

@admin_bp.route('/filtrar_peliculas_por_genero')
def filtrar_peliculas_por_genero():
    sql = """
            SELECT DISTINCT genero FROM peliculas
        """
    generos_a_filtrar = ejecutar_consulta_sql(sql)
    generos = set()
    for genero in generos_a_filtrar:
        generos_tmp = genero['genero'].replace(' ', '').split(',')
        for gen in generos_tmp:
            generos.add(gen)

    generos_list = list(generos)

    return jsonify(generos_list)

@admin_bp.route('/filtrar_peliculas', methods=['GET'])
def filtrar_peliculas():
    try:
        genero = request.args.get('genero', '')

        if genero:
            sql = """
                SELECT * FROM peliculas WHERE genero LIKE %s
            """
            genero_param = f"%{genero}%"
            peliculas = ejecutar_consulta_sql(sql, genero_param)
            print(peliculas)
            return jsonify(peliculas)
            # return render_template('admin/peliculas.html', peliculas = peliculas)
        else:
            return redirect(url_for('admin.mostrar_peliculas'))

    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    cines = ejecutar_consulta_sql(sql)

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
                return redirect(url_for('cines.editar_ciness', cine_id=cine_id))
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
    query = "SELECT * FROM peliculas"
    peliculas = ejecutar_consulta_sql(query)

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
        actores = request.form['actores']
        sinopsis = request.form['sinopsis']
        clasificacion = request.form['clasificacion']
        poster = request.form.get('poster', None)
        poster_file = request.files.get('poster_file', '')

        # Comprobamos primero que no estan ambos campos rellenados, solo se necesita uno de ellos
        if poster and poster_file and poster_file.filename:
            flash("Por favor, proporciona solo una URL o una imagen.", "danger")
            return render_template('admin/form_peliculas.html')

        # Si elige URL, comprobamos que es valida.
        if poster:
            if not validate_url(poster):
                flash("URL no valida", "danger")
                return render_template('admin/form_peliculas.html')
#       Procedemos a procesar el archivo, si es la opcion elegida
        if poster_file and poster_file.filename:
            if not archivo_permitido(poster_file.filename):
                flash("Solo se permiten archivos .jpg, .png o .jpeg", "danger")
                return render_template('admin/form_peliculas.html')
            # Generar nombre unico
            ext = poster_file.filename.rsplit('.', 1)[1].lower()
            # {titulo.lower().replace(' ', '_')}_{int(time.time())}.{ext}
            unique_filename = f"pelicula_{titulo.lower().replace(' ', '_')}.{ext}"
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            try:
                poster_file.save(file_path)
                poster = f"uploads/posters/{unique_filename}"
                poster= url_for('static', filename=poster)
            except Exception as e:
                flash(f"Error al guardar el archivo: {e}", "danger")
                return render_template('admin/form_peliculas.html')

        # Validaciones
        if not all([titulo, año, duracion, genero, director, clasificacion, sinopsis]):
            flash('Todos los campos son obligatorios', 'danger')
            return redirect(url_for('peliculas.nueva_pelicula'))

        datos_pelicula = {'titulo': titulo, 'año': año, 'duracion': duracion, 'genero': genero,
                          'director': director, 'sinopsis': sinopsis, 'clasificacion': clasificacion}

        # Comprobamos que los campos opcionales si estan con informacion, los incluimos
        if actores:
            datos_pelicula['actores'] = actores

        # En caso de que tengamos URL, la metemos en la base de datos
        if poster:
            datos_pelicula['poster_url'] = poster

        print(datos_pelicula)
        insertar_registro("peliculas", datos_pelicula)

        flash('Pelicula agregada exitosamente', 'success')
        return redirect(url_for('admin.mostrar_peliculas'))

    # Cuando pulsamos el boton nos manda al formulario de crear pelicula
    return render_template('admin/form_peliculas.html')

@admin_bp.route('/peliculas/editar/<int:id_pelicula>', methods=['GET','POST'])
def editar_pelicula(id_pelicula):
    peli = None
    if request.method == 'GET':
        peli = obtener_pelicula(id_pelicula)

        if peli is None:
            flash('No se encontro la pelicula', 'warning')
            return redirect(url_for('admin.mostrar_peliculas'))

    if request.method == 'POST':
        titulo = request.form['titulo']
        año = int(request.form['anho'])
        duracion = int(request.form['duracion'])
        genero = request.form['genero']
        director = request.form['director']
        actores = request.form['actores']
        sinopsis = request.form['sinopsis']
        clasificacion = request.form['clasificacion']
        poster = request.form['poster']
        poster_file = request.form['poster_file']

        peli = obtener_pelicula(id_pelicula)

        # Comprobamos primero que no estan ambos campos rellenados, solo se necesita uno de ellos
        if poster and poster_file and poster_file.filename:
            flash("Por favor, proporciona solo una URL o una imagen.", "danger")
            return render_template('admin/form_peliculas.html')

        # Si elige URL, comprobamos que es valida.
        if poster:
            if not validate_url(poster):
                flash("URL no valida", "danger")
                return render_template('admin/form_peliculas.html')
        #       Procedemos a procesar el archivo, si es la opcion elegida
        if poster_file and poster_file.filename:
            if not archivo_permitido(poster_file.filename):
                flash("Solo se permiten archivos .jpg, .png o .jpeg", "danger")
                return render_template('admin/form_peliculas.html')
            # Generar nombre unico
            ext = poster_file.filename.rsplit('.', 1)[1].lower()
            # {titulo.lower().replace(' ', '_')}_{int(time.time())}.{ext}
            unique_filename = f"pelicula_{titulo.lower().replace(' ', '_')}.{ext}"
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            try:
                poster_file.save(file_path)
                poster = f"uploads/posters/{unique_filename}"
                poster = url_for('static', filename=poster)
            except Exception as e:
                flash(f"Error al guardar el archivo: {e}", "danger")
                return render_template('admin/form_peliculas.html')

        # Validaciones
        if not all([titulo, año, duracion, genero, director, clasificacion, sinopsis]):
            flash('Todos los campos son obligatorios', 'danger')
            return redirect(url_for('peliculas.nueva_pelicula'))

        datos_pelicula = {}
        # Comprobamos que cada dato se guarde, si es diferente al existente
        if titulo != peli['titulo']:
            datos_pelicula['titulo'] = titulo
        if año != peli['año']:
            datos_pelicula['año'] = año
        if duracion != peli['duracion']:
            datos_pelicula['duracion'] = duracion
        if genero != peli['genero']:
            datos_pelicula['genero'] = genero
        if director != peli['director']:
            datos_pelicula['director'] = director
        if actores != peli['actores']:
            datos_pelicula['actores'] = actores
        if sinopsis != peli['sinopsis']:
            datos_pelicula['sinopsis'] = sinopsis
        if clasificacion != peli['clasificacion']:
            datos_pelicula['clasificacion'] = clasificacion
        if poster != peli['poster_url']:
            datos_pelicula['poster_url'] = poster

        if datos_pelicula:
            datos_pelicula['id_pelicula'] = peli['id_pelicula']
            print(f"Cambios nuevos: {datos_pelicula}")
            actualizar_registro("peliculas", datos_pelicula)

            flash('Pelicula actualizada exitosamente', 'success')
            return redirect(url_for('admin.mostrar_peliculas'))
        else:
            flash('No hay datos nuevos a cambiar', 'danger')
            return redirect(url_for('admin.mostrar_peliculas'))


    return render_template('admin/editar_pelicula.html', pelicula = peli)

@admin_bp.route('/peliculas/eliminar/<int:id_pelicula>', methods=['POST'])
def eliminar_pelicula(id_pelicula):
    conexion = None
    cursor = None
    try:
        conexion = conectar_base_datos_cine()
        cursor = conexion.cursor()

        query = f"DELETE FROM peliculas WHERE id_pelicula = %s"
        cursor.execute(query, (id_pelicula,))
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

    return redirect(url_for('admin.mostrar_peliculas'))

@admin_bp.route('/funciones', methods=['GET','POST'])
def mostrar_funciones():
    fecha = None
    if request.method == 'GET':
        # Deberiamos mostrar siempre las funciones cogiendo la fecha actual cuando abrimos por primera vez las funciones
        hoy = date.today()
        # En este caso vamos a fakeear el dia directamente para coger las funciones de un dia especifico
        fecha = '2025-04-14'
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'buscar':
            fecha_str = request.form.get('fecha')
            fecha = fecha_str

    sql = """
    SELECT
    c.id_cine,
    c.nombre AS nombre_cine,
    p.id_pelicula,
    p.titulo AS nombre_pelicula,
    s.numero,
    TIME_FORMAT(f.fecha_hora, '%%H:%%i') AS hora_funcion
FROM
    cines c
    LEFT JOIN salas s ON c.id_cine = s.id_cine
    LEFT JOIN funciones f ON s.id_sala = f.id_sala
    LEFT JOIN peliculas p ON f.id_pelicula = p.id_pelicula
WHERE
    DATE(f.fecha_hora) = %s
ORDER BY
    c.nombre, s.numero, hora_funcion;
    """

    funciones = ejecutar_consulta_sql(sql, (fecha,))
    print(funciones)
    return render_template('admin/funciones.html', funciones = funciones, fecha = fecha)

@admin_bp.route('/funciones/nueva_funcion', methods=['GET','POST'])
def agregar_funcion():
    if request.method == 'GET':
        cines = get_cines()
        peliculas = get_peliculas()
        salas_cine = obtener_salas_cine()

        return render_template('admin/form_funcion.html', cines=cines, peliculas=peliculas, salas=salas_cine)

    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "error": "No se enviaron datos"}), 400

            pelicula_id = data.get('pelicula_id')
            sala_id = data.get('sala_id')
            fecha_hora = data.get('fecha_hora')

            # Validar datos
            if not all([pelicula_id, sala_id, fecha_hora]):
                return jsonify({"success": False, "error": "Faltan campos requeridos"}), 400

            print(f"pelicula_id: {pelicula_id}, sala_id: {sala_id}, fecha_hora: {fecha_hora}")

            # Insertar la nueva función en la base de datos
            query = """
                INSERT IGNORE INTO funciones (id_pelicula, id_sala, fecha_hora)
                VALUES (%s, %s, %s)
            """
            result = ejecutar_consulta_sql(query, (pelicula_id, sala_id, fecha_hora), False)
            if result is None:
                return jsonify({"success": False, "error": "Error al guardar la función"}), 500

            return jsonify({"success": True, "message": "Función agregada exitosamente"}), 200
        except Exception as e:
            return jsonify({"success": False, "error": f"Error en el servidor: {str(e)}"}), 500

@admin_bp.route('/generar_report_pdf', methods=['POST'])
def generar_report_pdf():
    try:
        # Obtener los datos para exportar segun lo que decida el administrador
        data = request.get_json()
        fecha_inicio = data.get('fechaInicio')#
        fecha_final = data.get('fechaFin')

        # Tu lógica de generación del PDF aquí...
        print(f"Fechas recibidas: {fecha_inicio} - {fecha_final}")

        sql = """
        SELECT
            c.nombre AS nombre_cine,
            p.titulo AS nombre_pelicula,
            s.numero,
            TIME_FORMAT(f.fecha_hora, '%%H:%%i') AS hora_funcion
        FROM
            cines c
            LEFT JOIN salas s ON c.id_cine = s.id_cine
            LEFT JOIN funciones f ON s.id_sala = f.id_sala
            LEFT JOIN peliculas p ON f.id_pelicula = p.id_pelicula
        WHERE
            DATE(f.fecha_hora) BETWEEN %s AND %s
        ORDER BY
            c.nombre, s.numero, hora_funcion;
        """
        datos = ejecutar_consulta_sql( sql, (fecha_inicio, fecha_final))
        print(datos)
        # Generamos el PDF
        pdf = FPDF()
        pdf.add_page()

        pdf.set_font("Arial", style="", size=16)

        # Título principal
        pdf.cell(200, 10, "Reporte de Cartelera", ln=1, align='C')
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, f"Del {fecha_inicio} al {fecha_final}", ln=1, align='C')
        pdf.ln(10)

        # Agrupar datos por cine
        cines = {}
        for row in datos:
            cine = row['nombre_cine'] or "Sin cine"  # Manejo de valores nulos
            if cine not in cines:
                cines[cine] = {}
            sala = f"Sala {row['numero']}" if row['numero'] else "Sin sala"
            if sala not in cines[cine]:
                cines[cine][sala] = []
            cines[cine][sala].append({
                'pelicula': row['nombre_pelicula'] or "Sin película",
                'hora': row['hora_funcion'] or "Sin hora"
            })

        # Generar contenido del PDF
        pdf.set_font("Arial", size=12)
        for cine, salas in cines.items():
            pdf.set_fill_color(200, 220, 255)
            pdf.cell(200, 10, cine, ln=1, fill=True)
            pdf.ln(5)

            for sala, funciones in salas.items():
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(200, 8, sala, ln=1)
                pdf.set_font("Arial", size=10)

                for funcion in funciones:
                    pelicula = funcion['pelicula']
                    hora = funcion['hora']
                    pdf.cell(100, 6, f"- {pelicula}", ln=0)
                    pdf.cell(30, 6, hora, ln=1)
                pdf.ln(5)

        # # Generar y devolver el PDF
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        # pdf_output = pdf.output(dest='S')  # Generar PDF como string
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = (
            f'attachment; filename=cartelera_{fecha_inicio}_a_{fecha_final}.pdf'
        )
        return response


        # return jsonify({
        #     "status": "success",
        #     "message": "PDF generado correctamente",
        #     "fechas": {"inicio": fecha_inicio, "fin": fecha_final}
        # }), 200


    except Exception as e:
        # Imprimir traza completa para depuración
        print(f"Error en generar_report_pdf: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": f"Error al generar el PDF: {str(e)}"}), 500

@admin_bp.route('/cerrar_sesion')
def cerrar_sesion():
    return redirect(url_for('serve_index'))