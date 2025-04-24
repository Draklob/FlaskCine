import pymysql
from flask import Flask, jsonify, render_template, request, url_for, redirect, Blueprint
from flask_cors import CORS
from crear_datos_cine import crear_base_datos, listar_base_datos, crear_tablas, conectar_base_datos_cine
from agregar_datos_cine import agregar_datos_cine
from datetime import datetime

def iniciar_base_datos():
    print("\n=== Iniciando configuración de la base de datos ===")
    crear_base_datos()
    crear_tablas()
    agregar_datos_cine()
    #listar_base_datos()

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
app = Flask(__name__)
CORS(app)

@app.route("/api/info_peli/<int:id_pelicula>")
def info_peli(id_pelicula):
    try:
        conexion = conectar_base_datos_cine()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        print(f"Buscando la pelicula {id_pelicula}")
        # Buscamos la pelicula y nos devuelva toda la informacion sobre ella.
        cursor.execute('SELECT * FROM peliculas WHERE id_pelicula = %s', (id_pelicula,))
        pelicula = cursor.fetchone()
        cursor.close()
        conexion.close()
        return jsonify(pelicula)

    except pymysql.Error as error:
        return jsonify({'error': str(error)}), 500

@app.route('/cines', methods=['GET'])
def get_cines():
    iniciar_base_datos()
    try:
        conexion = conectar_base_datos_cine()
        cursor = conexion.cursor( pymysql.cursors.DictCursor )
        # Cogemos los datos de los cines de la base de datos
        cursor.execute('SELECT id_cine, nombre, direccion, telefono, precio_base FROM cines')
        cines = cursor.fetchall()

        # Buscamos el numero de salas que tiene cada cine y lo guardamos en la info de cada cine
        for i,cine in enumerate(cines):
            cursor.execute('SELECT COUNT(*) AS salas FROM cines c INNER JOIN salas s ON c.id_cine = s.id_cine WHERE c.id_cine = %s', (cine['id_cine'],))
            num_salas = cursor.fetchone()['salas']
            cines[i]['salas'] = num_salas

        cursor.close()
        conexion.close()
        return jsonify(cines)
    except pymysql.Error as error:
        return jsonify({'error': str(error)}), 500

@app.route('/cines/<int:id_cine>/peliculas', methods=['GET'])
#def get_peliculas(id_cine, fecha):
def get_peliculas(id_cine):
    try:
        conexion = conectar_base_datos_cine()
        cursor = conexion.cursor( pymysql.cursors.DictCursor )
        print("Buscando peliculas")
        cursor.execute('''
            SELECT
                p.id_pelicula, p.titulo, p.poster_url,
                GROUP_CONCAT(CONCAT(s.numero, ' a las ', TIME_FORMAT(f.fecha_hora,'%%H:%%i')) ORDER BY f.fecha_hora ASC SEPARATOR '; ') AS horarios
            FROM
                cines c
                INNER JOIN salas s ON c.id_cine = s.id_cine
                INNER JOIN funciones f ON s.id_sala = f.id_sala
                INNER JOIN peliculas p ON f.id_pelicula = p.id_pelicula
            WHERE
                c.id_cine = %s
                AND DATE(f.fecha_hora) = %s
            GROUP BY
                p.id_pelicula, p.titulo, p.duracion
            ORDER BY 
                p.id_pelicula, MIN(f.fecha_hora);
        ''', (id_cine, '2025-04-14'))
        peliculas = cursor.fetchall()

        cursor.close()
        conexion.close()
        return jsonify(peliculas)

    except pymysql.Error as error:
        return jsonify({'error': str(error)}), 500
@app.route('/')
def serve_index():
    return render_template('index.html')

@admin_bp.route('/')
def dashboard():
    return render_template('admin/dashboard.html', now = datetime.now())

@admin_bp.route('/cines')
def cines():
    # Lógica para obtener cines de la base de datos
    return render_template('admin/cines.html')


# Rutas similares para películas y funciones
@app.route('/admin/peliculas')
def admin_peliculas():
    return render_template('admin/peliculas.html')


@app.route('/admin/funciones')
def admin_funciones():
    return render_template('admin/funciones.html')

app.register_blueprint(admin_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5000)