import psycopg2

# ===============================
# CONFIGURACIÓN CONEXIÓN
# ===============================
DB_NAME = "WebCycling"
DB_USER = "postgres"
DB_PASS = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"

# ===============================
# DATOS DEL CICLISTA (ejemplo)
# ===============================
ciclista = "Luis Ortiz"

grandes_vueltas = [
]

world_tour = [
]

etapas = [
]

tours_continentales = [
]

# Nacionales (ruta y crono)
nacionales = [
    ("Campeonato Nacional de Ruta", 1947, 3),
]

# 🆕 Carreras Sub-23
sub23 = [
]

# ===============================
# FUNCIONES
# ===============================
def insert_data():
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
    )
    cur = conn.cursor()

    # Insertar ciclista
    cur.execute(
        "INSERT INTO ciclistas (nombre_ciclista) VALUES (%s) RETURNING id;", (ciclista,)
    )
    ciclista_id = cur.fetchone()[0]
    print(f"\n✅ Ciclista '{ciclista}' insertado con id {ciclista_id}\n")

    def get_or_create_carrera(nombre, tipo, año):
        print(f"🔎 Buscando carrera: {nombre} ({año}, {tipo})")
        cur.execute(
            'SELECT id FROM carreras WHERE nombre_carrera=%s AND "año"=%s;',
            (nombre, año),
        )
        row = cur.fetchone()
        if row:
            print(f"➡️ Carrera ya existe con id {row[0]}")
            return row[0]
        print("➡️ No existe, creando nueva...")
        cur.execute(
            'INSERT INTO carreras (nombre_carrera, tipo, "año") VALUES (%s, %s, %s) RETURNING id;',
            (nombre, tipo, año),
        )
        new_id = cur.fetchone()[0]
        print(f"✅ Carrera '{nombre}' {año} ({tipo}) insertada con id {new_id}")
        return new_id

    # Grandes Vueltas
    for nombre, año, pos, camiseta in grandes_vueltas:
        carrera_id = get_or_create_carrera(nombre, "GV", año)
        cur.execute(
            "INSERT INTO resultados (ciclista_id, carrera_id, posicion, camiseta_ganada) VALUES (%s, %s, %s, %s);",
            (ciclista_id, carrera_id, pos, camiseta),
        )
        print(f"✅ Resultado GV: {ciclista} {nombre} {año} -> {pos}°\n")

    # World Tour
    for nombre, año, pos in world_tour:
        carrera_id = get_or_create_carrera(nombre, "WT", año)
        cur.execute(
            "INSERT INTO resultados (ciclista_id, carrera_id, posicion) VALUES (%s, %s, %s);",
            (ciclista_id, carrera_id, pos),
        )
        print(f"✅ Resultado WT: {ciclista} {nombre} {año} -> {pos}°\n")

    # Nacionales
    if nacionales:
        print("🔎 Insertando nacionales...")
        for nombre, año, pos in nacionales:
            carrera_id = get_or_create_carrera(nombre, "Nacional", año)
            cur.execute(
                "INSERT INTO resultados (ciclista_id, carrera_id, posicion) VALUES (%s, %s, %s);",
                (ciclista_id, carrera_id, pos),
            )
            print(f"✅ Nacional: {ciclista} {nombre} {año} -> {pos}°")
        print("")
    
    # Sub-23 (clasificación general / podios)
    if sub23:
        print("🔎 Insertando resultados Sub-23...")
        for nombre, año, pos in sub23:
            carrera_id = get_or_create_carrera(nombre, "Sub23", año)
            cur.execute(
                "INSERT INTO resultados (ciclista_id, carrera_id, posicion) VALUES (%s, %s, %s);",
                (ciclista_id, carrera_id, pos),
            )
            print(f"✅ Sub-23: {ciclista} {nombre} {año} -> {pos}°\n")

    # Etapas
    if etapas:
        print("🔎 Insertando etapas...")
        for nombre, año, desc in etapas:
            carrera_id = get_or_create_carrera(nombre, "Etapa", año)
            cur.execute(
                "INSERT INTO etapas (ciclista_id, carrera_id, resultado_etapa) VALUES (%s, %s, %s);",
                (ciclista_id, carrera_id, desc),
            )
            print(f"✅ Etapa: {nombre} {año} -> {desc}")
        print("")

    # Tours Continentales
    if tours_continentales:
        print("🔎 Insertando tours continentales...")
        for nombre, año, continente in tours_continentales:
            carrera_id = get_or_create_carrera(nombre, "Continental", año)
            cur.execute(
                "INSERT INTO tours_continentales (ciclista_id, carrera_id, continente) VALUES (%s, %s, %s);",
                (ciclista_id, carrera_id, continente),
            )
            print(f"✅ Tour continental: {nombre} {año} ({continente})")

    conn.commit()
    cur.close()
    conn.close()
    print("\n🚴‍♂️ Datos insertados exitosamente.\n")


if __name__ == "__main__":
    insert_data()