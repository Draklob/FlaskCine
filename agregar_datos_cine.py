from itertools import count

from crear_datos_cine import conectar_base_datos_cine

import pymysql
import json

def agregar_datos_cine():
    try:
        conexion = conectar_base_datos_cine()
        cursor = conexion.cursor()

        # Verificamos si los cines ya fueron agregados, si es asi no los vuelve a agregar
        cursor.execute("SELECT COUNT(*) AS total FROM cines")
        count = cursor.fetchone()['total']

        if count == 0:
            # **** CINES *****
            print("Introduciendo datos en la tabla cine")
            #Leer el archivo JSON datos cines
            with open('datos_cines.json', 'r', encoding='utf-8') as file:
                cines = json.load(file)

            # Preparamos los datos de los cines
            cine_datos = [(c['nombre'], c['direccion'], c['telefono'], c['precio_base']) for c in cines]

            sql_cines = """
                INSERT INTO cines (nombre, direccion, telefono, precio_base) VALUES (%s, %s, %s, %s)
            """

            cursor.executemany(sql_cines, cine_datos)
            print(f"Insertadas {cursor.rowcount} cines a la base de datos.")

            # Confirmamos los cambios
            conexion.commit()
            # **** FIN CINES *****

        cursor.execute("SELECT COUNT(*) AS total FROM peliculas")
        count = cursor.fetchone()['total']

        if count == 0:
            # **** PELICULAS *****
            print("Introduciendo datos en la tabla peliculas")
            # Leer el archivo JSON datos peliculas
            with open('datos_peliculas.json', 'r', encoding='utf-8') as file:
                peliculas = json.load(file)

            # Preparamos los datos de las peliculas
            peliculas_datos = [(p['titulo'], p['año'], p['duracion'], p['genero'], p['director'],
                                p['actores'], p['sipnosis'], p['clasificacion'], p['poster_url'] ) for p in peliculas ]

            sql_pelis = """
                INSERT IGNORE INTO peliculas (titulo, año, duracion, genero, director, actores, sinopsis, clasificacion, poster_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            cursor.executemany(sql_pelis, peliculas_datos)
            print(f"Insertadas {cursor.rowcount} peliculas a la base de datos.")

            # Confirmar cambios
            conexion.commit()

            # **** FIN PELICULAS *****

        cursor.execute("SELECT COUNT(*) AS total FROM salas")
        count = cursor.fetchone()['total']

        if count == 0:
            # **** SALAS   ****
            print("Introduciendo salas en la tabla salas")
            with open('./datos_salas.json', 'r', encoding='utf-8') as file:
                salas = json.load(file)
            print(salas)
            # Preparamos los datos de las salas
            salas_datos = [(s['id_cine'], s['numero'], s['capacidad']) for s in salas]
            sql_salas = """
            INSERT INTO salas (id_cine, numero, capacidad) VALUES (%s, %s, %s)
            """

            cursor.executemany(sql_salas, salas_datos)
            print(f"Insertadas {cursor.rowcount} salas en la base de datos.")

            conexion.commit()

            # ***** FIN SALAS *****

        cursor.execute("SELECT COUNT(*) AS total FROM funciones")
        count = cursor.fetchone()['total']

        if count == 0:
            print("Introduciendo funciones en la tabla funciones")
            # **** FUNCIONES   ****

            with open('datos_funciones.json', 'r', encoding='utf-8') as file:
                funciones = json.load(file)

            funciones_datos = [(f['id_pelicula'], f['id_sala'], f['fecha_hora']) for f in funciones]
            sql_funciones = """
            INSERT IGNORE INTO funciones (id_pelicula, id_sala, fecha_hora) VALUES (%s, %s, %s)
            """

            cursor.executemany(sql_funciones, funciones_datos)
            conexion.commit()

            # **** FIN FUNCIONES ****

    except pymysql.Error as e:
        print(f"Error en la base de datos: {e}")
    except FileNotFoundError:
        print("Error: No se encontró el archivo 'datos_funciones.json'.")
    except json.JSONDecodeError as e:
        print(f"Error al leer el JSON: {e}")
    except KeyError as e:
        print(f"Error: Falta la clave {e} en el JSON.")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()
            print("Conexión cerrada.")