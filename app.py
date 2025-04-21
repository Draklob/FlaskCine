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
        cursor.execute('SELECT id_cine, nombre, direccion, telefono, precio_base FROM cines')
        cines = cursor.fetchall()
        cursor.close()
        conexion.close()
        return jsonify(cines)
    except pymysql.Error as error:
        return jsonify({'error': str(error)}), 500

@app.route('/')
def serve_index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)