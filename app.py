import pymysql
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from crear_datos_cine import crear_base_datos, listar_base_datos, crear_tablas, conectar_base_datos_cine
from agregar_datos_cine import agregar_datos_cine

def iniciar_base_datos():
    print("\n=== Iniciando configuración de la base de datos ===")
    crear_base_datos()
    crear_tablas()
    agregar_datos_cine()
    #listar_base_datos()
app = Flask(__name__)
CORS(app)

@app.route('/cines', methods=['GET'])
def get_cines():
    iniciar_base_datos()
    try:
        conexion = conectar_base_datos_cine()
        cursor = conexion.cursor( pymysql.cursors.DictCursor )
        # Cogemos los datos de los cines de la base de datos
        cursor.execute('SELECT id_cine, nombre, direccion, telefono, precio_base FROM cines')
        cines = cursor.fetchall()
        # Buscamos el numero de salas que tiene cada cine


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
                p.id_pelicula, p.titulo,
                GROUP_CONCAT(CONCAT(s.numero, ' a las ', TIME_FORMAT(f.fecha_hora,'%%H:%%i')) SEPARATOR '; ') AS horarios
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
                `p`.`id_pelicula` ASC;
        ''', (id_cine, '2025-04-14'))
        peliculas = cursor.fetchall()
        print(peliculas)

        cursor.close()
        conexion.close()
        return jsonify(peliculas)

    except pymysql.Error as error:
        return jsonify({'error': str(error)}), 500
@app.route('/')
def serve_index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)