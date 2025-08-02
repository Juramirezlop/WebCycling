import psycopg2

# Configuración de conexión a PostgreSQL
DB_NAME = "WebCycling"
DB_USER = "postgres"
DB_PASS = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"

# Definición de las tablas
TABLES = {}

TABLES["ciclistas"] = """
CREATE TABLE IF NOT EXISTS ciclistas (
    id SERIAL PRIMARY KEY,
    nombre_ciclista VARCHAR(150) NOT NULL UNIQUE
);
"""

TABLES["carreras"] = """
CREATE TABLE IF NOT EXISTS carreras (
    id SERIAL PRIMARY KEY,
    nombre_carrera VARCHAR(150) NOT NULL,
    tipo VARCHAR(50),
    año INT NOT NULL
);
"""

TABLES["resultados"] = """
CREATE TABLE IF NOT EXISTS resultados (
    id SERIAL PRIMARY KEY,
    ciclista_id INT NOT NULL,
    carrera_id INT NOT NULL,
    posicion INT,
    camiseta_ganada VARCHAR(100),
    FOREIGN KEY (ciclista_id) REFERENCES ciclistas(id),
    FOREIGN KEY (carrera_id) REFERENCES carreras(id)
);
"""

TABLES["etapas"] = """
CREATE TABLE IF NOT EXISTS etapas (
    id SERIAL PRIMARY KEY,
    ciclista_id INT NOT NULL,
    carrera_id INT NOT NULL,
    resultado_etapa VARCHAR(50),
    FOREIGN KEY (ciclista_id) REFERENCES ciclistas(id),
    FOREIGN KEY (carrera_id) REFERENCES carreras(id)
);
"""

TABLES["tours_continentales"] = """
CREATE TABLE IF NOT EXISTS tours_continentales (
    id SERIAL PRIMARY KEY,
    ciclista_id INT NOT NULL,
    carrera_id INT NOT NULL,
    continente VARCHAR(50),
    FOREIGN KEY (ciclista_id) REFERENCES ciclistas(id),
    FOREIGN KEY (carrera_id) REFERENCES carreras(id)
);
"""

def create_tables():
    try:
        # Conectar a PostgreSQL
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()

        # Crear cada tabla
        for table_name, ddl in TABLES.items():
            print(f"Creando tabla {table_name}...")
            cur.execute(ddl)

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Tablas creadas exitosamente.")

    except Exception as e:
        print("❌ Error creando tablas:", e)

if __name__ == "__main__":
    create_tables()
