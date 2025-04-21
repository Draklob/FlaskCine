import pymysql
from pymysql import MySQLError, OperationalError

def crear_base_datos():
    try:
        # Conexion al servidor MySQL
        print("Creando base datos")
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            port=3308,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        try:
            with connection.cursor() as cursor:
                # Crear la base de datos si no existe
                cursor.execute("SHOW DATABASES LIKE 'cine_db'")
                result = cursor.fetchone()
                if result is None:
                    cursor.execute("CREATE DATABASE IF NOT EXISTS cine_db")
                    print("Base de datos 'cine' creada correctamente.")
                else:
                    print("Base de datos 'cine' ya existe.")
        finally:
            connection.close()

    except pymysql.err.OperationalError as e:
        # Errores de conexión (ej: servidor no disponible, credenciales incorrectas)
        print(f"❌ Error al conectar a MySQL: {e}")

    except MySQLError as e:
        print(f"Error de MYSQL: {e}")

    except Exception as e:
        # Cualquier otro error inesperado
        print(f"❌ Error inesperado: {e}")

def conectar_base_datos_cine():
    """Establece conexion con la base de datos cine"""
    try:
        conexion= pymysql.connect(
            host='localhost',
            user='root',
            password='',
            port=3308,
            database='cine_db',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        print("Conexion con base de datos cine fue exitosa.")
        return conexion

    except OperationalError as e:
        print(f"❌ Error al conectar a la base de datos: {e}")
        return None

def listar_base_datos():
    conexion = conectar_base_datos_cine()
    if conexion is None:
        return False

    try:
        with conexion.cursor() as cursor:
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()

            print("Bases de datos disponibles:")
            for db in databases:
                print(f"- {db['Database']}") # Accedemos al campo 'Database'

    finally:
        conexion.close()

def crear_tablas():
    try:
        conexion = conectar_base_datos_cine()

        cursor = conexion.cursor()
        # SCRIPT SQL COMPLETO
        # Si ya existen las tablas, no las vuelve a crear, simplemente da el salto a la siguiente secuencia SQL
        script_sql = """
            -- Crea la tabla PELICULAS
            CREATE TABLE IF NOT EXISTS peliculas(
            id_pelicula INT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(100) UNIQUE NOT NULL,
            año INT NOT NULL,
            duracion INT NOT NULL,
            genero VARCHAR(40) NOT NULL,
            director VARCHAR(40) NOT NULL,
            actores VARCHAR(180),
            sinopsis TEXT,
            clasificacion VARCHAR(10) NOT NULL,
            poster_url VARCHAR(250)
            );
            
            -- Crea la tabla CINE
            CREATE TABLE IF NOT EXISTS cines(
            id_cine INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            direccion VARCHAR(250) NOT NULL,
            telefono VARCHAR(20) NOT NULL,
            precio_base DECIMAL (3,2) NOT NULL
            );

            -- Crea la tabla SALAS
            CREATE TABLE IF NOT EXISTS salas(
            id_sala INT AUTO_INCREMENT PRIMARY KEY,
            numero VARCHAR(50) NOT NULL,
            capacidad INT NOT NULL,
            id_cine INT NOT NULL,
            FOREIGN KEY (id_cine) REFERENCES cines (id_cine)
            );
            
            -- Crea la tabla FUNCIONES
            CREATE TABLE IF NOT EXISTS funciones(
            id_funcion INT AUTO_INCREMENT PRIMARY KEY,
            id_pelicula INT,
            id_sala INT,
            fecha_hora DATETIME NOT NULL,
            FOREIGN KEY (id_pelicula) REFERENCES peliculas (id_pelicula),
            FOREIGN KEY (id_sala) REFERENCES salas (id_sala)
            );
            
            -- Crea la tabla Usuarios
            CREATE TABLE IF NOT EXISTS usuarios(
            id_usuario INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL,
            telefono VARCHAR(20) DEFAULT NULL,
            fecha_nacimiento DATETIME DEFAULT NULL,
            es_estudiante BOOLEAN DEFAULT FALSE
            );
            
            -- Crea la tabla Reservas
            CREATE TABLE IF NOT EXISTS reservas(
            id_reserva INT AUTO_INCREMENT PRIMARY KEY,
            id_usuario INT,
            id_funcion INT,
            cantidad_entradas INT NOT NULL,
            fecha_hora DATETIME NOT NULL,
            pago_total DECIMAL (4,2) NOT NULL,
            FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario),
            FOREIGN KEY (id_funcion) REFERENCES funciones (id_funcion)
            );
            
            -- Crea la tabla Asientos
            CREATE TABLE IF NOT EXISTS asientos(
            id_asiento INT AUTO_INCREMENT PRIMARY KEY,
            id_sala INT,
            num_asiento VARCHAR(10) NOT NULL,
            disponible BOOLEAN NOT NULL
            );
            
            -- Crea la tabla ReservarAsiento
            CREATE TABLE IF NOT EXISTS reservarasiento(
            id_reserva INT,
            id_asiento INT,
            FOREIGN KEY (id_reserva) REFERENCES reservas (id_reserva),
            FOREIGN KEY (id_asiento) REFERENCES asientos (id_asiento)
            );
            
            -- Crea la tabla descuentos
            CREATE TABLE IF NOT EXISTS descuentos(
            id_descuento INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(70) NOT NULL,
            edad_minima INT DEFAULT NULL,
            edad_maxima INT DEFAULT NULL,
            requiere_estudiante BOOLEAN DEFAULT FALSE
            );
            
            -- Crea la tabla descuentos_cine
            CREATE TABLE IF NOT EXISTS descuentos_cine(
            id_descuento_cine INT AUTO_INCREMENT PRIMARY KEY,
            id_cine INT,
            id_descuento INT,
            porcentaje DECIMAL(3,3) NOT NULL, -- 0.30 para un 30% de descuento
            dia_semana INT CHECK (dia_semana BETWEEN 1 AND 7 OR dia_semana IS NULL),
            FOREIGN KEY (id_cine) REFERENCES cines (id_cine),
            FOREIGN KEY (id_descuento) REFERENCES descuentos (id_descuento)
            );
            """
        # TERMINA LA CREACION DE LAS TABLAS

        # Ejecutamos el script separando cada sentencia
        for sentencia in script_sql.split(';'):
            if sentencia.strip(): # Que elimine cualquier espacio sobrante
                cursor.execute(sentencia)

        # Confirmamos y guardamos los cambios en la base de datos
        conexion.commit()
        print("Tablas creadas exitosamente")

    except pymysql.Error as e:
        print(f"Ocurrió un error: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()
            print("Cerrando conexion con la base de datos.")

def insertar_datos():
    pass