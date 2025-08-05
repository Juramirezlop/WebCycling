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
# DATOS DEL CICLISTA
# ===============================
ciclista = "Jose Alfonso Lopez"

grandes_vueltas = [
]

# Mundiales (ruta y crono)
mundiales = [
]

# Juegos Olímpicos (ruta y crono)
juegos_olimpicos = [
]

world_tour = [
]

# Nacionales (ruta y crono)
nacionales = [
]

campeones_continentales = [
]

# Inserta etapas y especifica tipo de carrera
etapas = [
    ("Vuelta Costa Rica", 1976, "Continental", 2),
    ("Tour del Porvenir", 1982, "Sub-23", 1),
]

# ===============================
# FUNCIONES
# ===============================
def insert_data():
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
    )
    cur = conn.cursor()
    
    def get_or_create_ciclista(cur, nombre):
        # Buscar si ya existe
        cur.execute("SELECT id FROM ciclistas WHERE nombre_ciclista = %s;", (nombre,))
        row = cur.fetchone()
        if row:
            return row[0], False
        
        # Si no existe, insertarlo
        cur.execute(
            "INSERT INTO ciclistas (nombre_ciclista) VALUES (%s) RETURNING id;",
            (nombre,)
        )
        new_id = cur.fetchone()[0]
        return new_id, True 

    ciclista_id, creado = get_or_create_ciclista(cur, ciclista)

    if creado:
        print(f"🚴 Nuevo ciclista agregado: {ciclista} (id {ciclista_id})")
    else:
        print(f"↩️ Usando ciclista existente: {ciclista} (id {ciclista_id})")


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
    
    # Mundiales
    if mundiales:
        print("🔎 Insertando Mundiales...")
        for nombre, año, pos in mundiales:
            carrera_id = get_or_create_carrera(nombre, "Mundial", año)
            cur.execute(
                "INSERT INTO resultados (ciclista_id, carrera_id, posicion) VALUES (%s, %s, %s);",
                (ciclista_id, carrera_id, pos),
            )
            print(f"🌍 Mundial: {ciclista} {nombre} {año} -> {pos}°")
        print("")

    # Juegos Olímpicos
    if juegos_olimpicos:
        print("🔎 Insertando Juegos Olímpicos...")
        for nombre, año, pos in juegos_olimpicos:
            carrera_id = get_or_create_carrera(nombre, "Juegos Olímpicos", año)
            cur.execute(
                "INSERT INTO resultados (ciclista_id, carrera_id, posicion) VALUES (%s, %s, %s);",
                (ciclista_id, carrera_id, pos),
            )
            print(f"🏅 JJOO: {ciclista} {nombre} {año} -> {pos}°")
        print("")

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
    
    # Campeones de carreras continentales
    if campeones_continentales:
        print("🔎 Insertando campeonatos continentales...")
        for nombre, año in campeones_continentales:
            carrera_id = get_or_create_carrera(nombre, "Continental", año)

            # Verificar si tiene continente asignado
            cur.execute("SELECT continente FROM tours_continentales WHERE carrera_id = %s;", (carrera_id,))
            row = cur.fetchone()
            if not row or not row[0]:  # no existe registro o continente vacío
                continente = input(f"🌍 La carrera '{nombre} {año}' no tiene continente asignado. Ingrese continente: ")
                cur.execute(
                    "INSERT INTO tours_continentales (carrera_id, continente) VALUES (%s, %s);",
                    (carrera_id, continente)
                )
                print(f"✅ Continente '{continente}' asignado a {nombre} {año}")

            # Insertar resultado del campeón
            cur.execute(
                "INSERT INTO resultados (ciclista_id, carrera_id, posicion) VALUES (%s, %s, %s);",
                (ciclista_id, carrera_id, 1)
            )
            print(f"🏆 {ciclista} campeón de {nombre} {año}")
        print("")

    # Insertar etapas
    if etapas:
        print("🔎 Insertando etapas...")
        for nombre, año, tipo, cantidad in etapas:
            carrera_id = get_or_create_carrera(nombre, tipo, año)

            # Si es carrera Continental, verificar si tiene continente asignado
            if tipo == "Continental":
                cur.execute("SELECT continente FROM tours_continentales WHERE carrera_id = %s;", (carrera_id,))
                row = cur.fetchone()
                if not row:  # no tiene continente
                    continente = input(f"🌍 La carrera '{nombre} {año}' no tiene continente asignado. Ingrese continente: ")
                    cur.execute(
                        "INSERT INTO tours_continentales (carrera_id, continente) VALUES (%s, %s);",
                        (carrera_id, continente)
                    )
                    print(f"✅ Continente '{continente}' asignado a {nombre} {año}")

            # Insertar la etapa
            cur.execute(
                "INSERT INTO etapas (ciclista_id, carrera_id, cantidad_etapas) VALUES (%s, %s, %s);",
                (ciclista_id, carrera_id, cantidad),
            )
            print(f"✅ Etapas: {nombre} {año} ({tipo}) -> {cantidad} ganadas")
        print("")

    conn.commit()
    cur.close()
    conn.close()
    print("🚴‍♂️ Datos insertados exitosamente.\n")

if __name__ == "__main__":
    insert_data()