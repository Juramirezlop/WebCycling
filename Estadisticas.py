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
# FUNCIONES DE CONSULTA
# ===============================
def consultar_ciclista(nombre_ciclista):
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS,
                            host=DB_HOST, port=DB_PORT)
    cur = conn.cursor()

    query = """
    (
        SELECT 
            ci.nombre_ciclista,
            ca.nombre_carrera,
            ca.año,
            ca.tipo,
            'Resultado' AS origen,
            r.posicion::text AS detalle
        FROM resultados r
        JOIN ciclistas ci ON r.ciclista_id = ci.id
        JOIN carreras ca ON r.carrera_id = ca.id
        WHERE ci.nombre_ciclista ILIKE %s
    )
    UNION ALL
    (
        SELECT 
            ci.nombre_ciclista,
            ca.nombre_carrera,
            ca.año,
            ca.tipo,
            'Etapas' AS origen,
            e.cantidad_etapas::text AS detalle
        FROM etapas e
        JOIN ciclistas ci ON e.ciclista_id = ci.id
        JOIN carreras ca ON e.carrera_id = ca.id
        WHERE ci.nombre_ciclista ILIKE %s
    )
    ORDER BY año, nombre_carrera, origen;
    """

    cur.execute(query, (nombre_ciclista, nombre_ciclista))
    rows = cur.fetchall()

    if not rows:
        print(f"\n❌ No se encontraron registros para {nombre_ciclista}")
    else:
        print(f"\n📊 Resultados y etapas de {nombre_ciclista}:")
        for nombre, carrera, año, tipo, origen, detalle in rows:
            if origen == "Resultado":
                print(f" - {carrera} {año} ({tipo}) → Posición {detalle}")
            else:
                print(f" - {carrera} {año} ({tipo}) → Ganó {detalle} etapas")

    cur.close()
    conn.close()


def consultar_carrera(nombre_carrera):
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS,
                            host=DB_HOST, port=DB_PORT)
    cur = conn.cursor()

    query = """
    (
        SELECT 
            ca.nombre_carrera,
            ca.año,
            ca.tipo,
            ci.nombre_ciclista,
            'Resultado' AS origen,
            r.posicion::text AS detalle
        FROM resultados r
        JOIN ciclistas ci ON r.ciclista_id = ci.id
        JOIN carreras ca ON r.carrera_id = ca.id
        WHERE ca.nombre_carrera ILIKE %s
    )
    UNION ALL
    (
        SELECT 
            ca.nombre_carrera,
            ca.año,
            ca.tipo,
            ci.nombre_ciclista,
            'Etapas' AS origen,
            e.cantidad_etapas::text AS detalle
        FROM etapas e
        JOIN ciclistas ci ON e.ciclista_id = ci.id
        JOIN carreras ca ON e.carrera_id = ca.id
        WHERE ca.nombre_carrera ILIKE %s
    )
    ORDER BY año, nombre_carrera, origen;
    """

    cur.execute(query, (nombre_carrera, nombre_carrera))
    rows = cur.fetchall()

    if not rows:
        print(f"\n❌ No se encontraron registros para la carrera {nombre_carrera}")
    else:
        print(f"\n📊 Resultados y etapas en {nombre_carrera}:")
        for carrera, año, tipo, ciclista, origen, detalle in rows:
            if origen == "Resultado":
                print(f" - {ciclista}: {carrera} {año} ({tipo}) → Posición {detalle}")
            else:
                print(f" - {ciclista}: {carrera} {año} ({tipo}) → Ganó {detalle} etapas")

    cur.close()
    conn.close()


def consultar_por_año(anio):
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS,
                            host=DB_HOST, port=DB_PORT)
    cur = conn.cursor()

    query = """
    (
        SELECT 
            ca.nombre_carrera,
            ca.año,
            ca.tipo,
            ci.nombre_ciclista,
            'Resultado' AS origen,
            r.posicion::text AS detalle
        FROM resultados r
        JOIN ciclistas ci ON r.ciclista_id = ci.id
        JOIN carreras ca ON r.carrera_id = ca.id
        WHERE ca."año" = %s
    )
    UNION ALL
    (
        SELECT 
            ca.nombre_carrera,
            ca.año,
            ca.tipo,
            ci.nombre_ciclista,
            'Etapas' AS origen,
            e.cantidad_etapas::text AS detalle
        FROM etapas e
        JOIN ciclistas ci ON e.ciclista_id = ci.id
        JOIN carreras ca ON e.carrera_id = ca.id
        WHERE ca."año" = %s
    )
    ORDER BY nombre_carrera, origen;
    """

    cur.execute(query, (anio, anio))
    rows = cur.fetchall()

    if not rows:
        print(f"\n❌ No se encontraron registros para el año {anio}")
    else:
        print(f"\n📊 Resultados y etapas del año {anio}:")
        for carrera, año, tipo, ciclista, origen, detalle in rows:
            if origen == "Resultado":
                print(f" - {ciclista}: {carrera} ({tipo}) → Posición {detalle}")
            else:
                print(f" - {ciclista}: {carrera} ({tipo}) → Ganó {detalle} etapas")

    cur.close()
    conn.close()


# ===============================
# MENÚ PRINCIPAL
# ===============================
def main():
    print("\n📌 Menú de consultas")
    print("1. Consultar por ciclista")
    print("2. Consultar por carrera")
    print("3. Consultar por año")
    print("4. Salir")

    opcion = input("Seleccione una opción: ")

    if opcion == "1":
        nombre = input("Ingrese el nombre del ciclista: ")
        consultar_ciclista(nombre)
    elif opcion == "2":
        nombre = input("Ingrese el nombre de la carrera: ")
        consultar_carrera(nombre)
    elif opcion == "3":
        año = input("Ingrese el año: ")
        consultar_por_año(año)
    elif opcion == "4":
        print("👋 Saliendo...")
    else:
        print("❌ Opción no válida, intente de nuevo.")


if __name__ == "__main__":
    main()
