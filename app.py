from flask import Flask

from crear_datos_cine import crear_base_datos, listar_base_datos, crear_tablas

def iniciar_base_datos():
    print("\n=== Iniciando configuración de la base de datos ===")
    crear_base_datos()
    crear_tablas()
    listar_base_datos()
app = Flask(__name__)
@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'

if __name__ == '__main__':
    iniciar_base_datos()
    app.run(debug=False)