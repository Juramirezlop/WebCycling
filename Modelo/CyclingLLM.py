import os
import psycopg2
from openai import AzureOpenAI
from dotenv import load_dotenv
import re

# Cargar variables de entorno
load_dotenv()

class CyclingLLM:
    def __init__(self):
        # Configurar conexión a PostgreSQL
        self.db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432"),
            "database": os.getenv("DB_NAME", "WebCycling"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "")
        }
        
        # Configurar Azure OpenAI
        self.client = AzureOpenAI(
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
        )
        self.deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT')

    def connect_db(self):
        """Conectar a PostgreSQL"""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            print(f"Error conectando a la base de datos: {e}")
            return None
    
    def get_database_schema(self):
        """Extraer esquema real de la base de datos"""
        conn = self.connect_db()
        if not conn:
            return "Error conectando a la base de datos"
        
        try:
            cursor = conn.cursor()
            
            # Obtener información detallada de las tablas
            cursor.execute("""
                SELECT 
                    t.table_name,
                    c.column_name,
                    c.data_type,
                    CASE 
                        WHEN tc.constraint_type = 'PRIMARY KEY' THEN 'PK'
                        WHEN tc.constraint_type = 'FOREIGN KEY' THEN 'FK'
                        ELSE ''
                    END as constraint_info
                FROM information_schema.tables t
                JOIN information_schema.columns c ON t.table_name = c.table_name
                LEFT JOIN information_schema.key_column_usage kcu ON c.table_name = kcu.table_name 
                    AND c.column_name = kcu.column_name
                LEFT JOIN information_schema.table_constraints tc ON kcu.constraint_name = tc.constraint_name
                WHERE t.table_schema = 'public' 
                    AND t.table_type = 'BASE TABLE'
                ORDER BY t.table_name, c.ordinal_position;
            """)
            
            results = cursor.fetchall()
            
            # Formatear el esquema
            schema_dict = {}
            for row in results:
                table_name, column_name, data_type, constraint_info = row
                if table_name not in schema_dict:
                    schema_dict[table_name] = []
                
                column_info = f"{column_name} ({data_type})"
                if constraint_info:
                    column_info += f" {constraint_info}"
                
                schema_dict[table_name].append(column_info)
            
            # También obtener nombres de carreras disponibles
            cursor.execute("SELECT DISTINCT nombre_carrera FROM carreras ORDER BY nombre_carrera;")
            carreras_disponibles = [row[0] for row in cursor.fetchall()]
            
            # Construir texto del esquema
            schema_text = "ESQUEMA DE BASE DE DATOS:\n\n"
            for table, columns in schema_dict.items():
                schema_text += f"Tabla: {table}\n"
                for column in columns:
                    schema_text += f"  - {column}\n"
                schema_text += "\n"
            
            schema_text += f"CARRERAS DISPONIBLES EN LA BD:\n"
            for carrera in carreras_disponibles:
                schema_text += f"- {carrera}\n"
            schema_text += "\n"
            
            cursor.close()
            conn.close()
            return schema_text
            
        except Exception as e:
            print(f"Error obteniendo esquema: {e}")
            if conn:
                conn.close()
            return "Error obteniendo esquema de la base de datos"

    def normalize_year(self, text):
        """Convertir años en formato coloquial a formato completo"""
        year_patterns = [
            r"\b'?(\d{2})\'?\b",  # '46, 46', 46
            r"\b(\d{4})\b"        # 1946
        ]
        
        normalized_text = text
        for pattern in year_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) == 2:  # Año de 2 dígitos
                    year_num = int(match)
                    if year_num >= 0 and year_num <= 30:  # 00-30 = 2000-2030
                        full_year = 2000 + year_num
                    else:  # 31-99 = 1931-1999
                        full_year = 1900 + year_num
                    
                    # Reemplazar en el texto
                    old_patterns = [f"'{match}'", f"'{match}", f"{match}'", f"{match}"]
                    for old_pattern in old_patterns:
                        if old_pattern in normalized_text:
                            normalized_text = normalized_text.replace(old_pattern, str(full_year))
                            break
        
        return normalized_text

    def normalize_question(self, question):
        """Normalizar la pregunta para manejar lenguaje coloquial"""
        question = question.lower()
        
        # Normalizar años
        question = self.normalize_year(question)
        
        # Sinónimos y términos coloquiales
        replacements = {
            # Carreras
            'nacionales': 'nacional',
            'nacional de ruta': 'nacional',
            'nacionales de ruta': 'nacional',
            'campeonato nacional': 'nacional',
            'campeonatos nacionales': 'nacional',
            
            # Posiciones y logros múltiples
            'podio': 'posicion <= 3',
            'podium': 'posicion <= 3',
            'podios': 'posicion <= 3',
            'los 3 primeros': 'posicion <= 3',
            'top 3': 'posicion <= 3',
            'primeros tres': 'posicion <= 3',
            'mas podios': 'count podios',
            'más podios': 'count podios',
            'con mas podios': 'count podios',
            'con más podios': 'count podios',
            'mayor cantidad de podios': 'count podios',
            'más triunfos': 'count victorias',
            'mas triunfos': 'count victorias',
            'más victorias': 'count victorias',
            'mas victorias': 'count victorias',
            
            # Ganadores
            'campeón': 'posicion = 1',
            'campeon': 'posicion = 1',
            'ganador': 'posicion = 1',
            'quien ganó': 'posicion = 1',
            'quien gano': 'posicion = 1',
            'el que ganó': 'posicion = 1',
            'el que gano': 'posicion = 1',
            
            # Años
            'año a año': 'por año',
            'todos los años': 'por año',
            'cada año': 'por año',
        }
        
        for old, new in replacements.items():
            question = question.replace(old, new)
        
        return question

    def execute_query(self, query):
        """Ejecutar consulta SQL y retornar resultados"""
        conn = self.connect_db()
        if not conn:
            return None, "Error de conexión a la base de datos"
        
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            # Convertir a lista de diccionarios
            data = []
            for row in results:
                row_dict = {}
                for i, value in enumerate(row):
                    if hasattr(value, 'isoformat'):  # datetime objects
                        row_dict[columns[i]] = value.isoformat()
                    else:
                        row_dict[columns[i]] = value
                data.append(row_dict)
            
            cursor.close()
            conn.close()
            return data, None
        
        except Exception as e:
            error_msg = f"Error ejecutando consulta: {str(e)}"
            print(error_msg)
            if conn:
                conn.close()
            return None, error_msg
    
    def generate_sql_query(self, user_question):
        """Generar consulta SQL con mejor comprensión coloquial y estadísticas"""
        
        # Normalizar la pregunta
        normalized_question = self.normalize_question(user_question)
        schema = self.get_database_schema()
        
        prompt = f"""Eres un experto en SQL para ciclismo colombiano. Genera consultas SQL precisas para estadísticas y conteos.

{schema}

REGLAS CRÍTICAS:
1. Genera SOLO código SQL válido, sin explicaciones
2. El nombre exacto de las carreras es "Campeonato Nacional de Ruta"
3. Para búsquedas de carreras nacionales usa: nombre_carrera ILIKE '%nacional%'
4. Para búsquedas de ciclistas usa ILIKE '%nombre%' (coincidencias parciales)
5. SIEMPRE incluye año, nombre_ciclista, posicion en SELECT cuando sea relevante

TÉRMINOS ESPECIALES PARA ESTADÍSTICAS:
- "count podios" = Contar ciclistas con más podios (posicion <= 3)
- "count victorias" = Contar ciclistas con más victorias (posicion = 1)
- "mas podios/más podios" = Usar GROUP BY y COUNT con ORDER BY count DESC
- "quien tiene mas" = Usar GROUP BY ciclista y COUNT

ESTRUCTURA PARA CONTEOS DE PODIOS:
SELECT 
    ci.nombre_ciclista,
    COUNT(*) as total_podios
FROM resultados r
JOIN ciclistas ci ON r.ciclista_id = ci.id
JOIN carreras ca ON r.carrera_id = ca.id
WHERE r.posicion <= 3 AND ca.nombre_carrera ILIKE '%nacional%'
GROUP BY ci.nombre_ciclista
ORDER BY total_podios DESC, ci.nombre_ciclista ASC;

ESTRUCTURA PARA CONTEOS DE VICTORIAS:
SELECT 
    ci.nombre_ciclista,
    COUNT(*) as total_victorias
FROM resultados r
JOIN ciclistas ci ON r.ciclista_id = ci.id
JOIN carreras ca ON r.carrera_id = ca.id
WHERE r.posicion = 1 AND ca.nombre_carrera ILIKE '%nacional%'
GROUP BY ci.nombre_ciclista
ORDER BY total_victorias DESC, ci.nombre_ciclista ASC;

ESTRUCTURA NORMAL PARA RESULTADOS:
SELECT 
    ci.nombre_ciclista,
    ca.nombre_carrera,
    ca.año,
    r.posicion,
    r.camiseta_ganada
FROM resultados r
JOIN ciclistas ci ON r.ciclista_id = ci.id
JOIN carreras ca ON r.carrera_id = ca.id
WHERE [condiciones]
ORDER BY ca.año ASC, r.posicion ASC;

EJEMPLOS CRÍTICOS:
- "quien tiene mas podios" → Usar estructura de conteos de podios
- "cual es el corredor con mas podios" → Usar estructura de conteos de podios  
- "ciclista con mas victorias" → Usar estructura de conteos de victorias
- "ganadores nacionales" → WHERE r.posicion = 1 AND ca.nombre_carrera ILIKE '%nacional%'
- "podio nacional 1947" → WHERE ca.año = 1947 AND r.posicion <= 3 AND ca.nombre_carrera ILIKE '%nacional%'

Pregunta original: {user_question}
Pregunta normalizada: {normalized_question}

SQL:"""

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=500
            )
            
            sql_query = response.choices[0].message.content.strip()
            sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
            
            if not sql_query.upper().startswith('SELECT'):
                return None
                
            return sql_query
        
        except Exception as e:
            print(f"Error generando consulta SQL: {e}")
            return None
    
    def generate_answer(self, user_question, query_results):
        """Generar respuesta final con mejor manejo de estadísticas"""
        
        if not query_results:
            return "No encontré datos para responder tu pregunta en la base de datos."
        
        # Detectar si es una consulta de estadísticas
        has_count_column = any('total_' in str(key) or 'count' in str(key).lower() 
                                for row in query_results for key in row.keys())
        
        # Crear interpretación clara de los datos
        data_summary = "INTERPRETACIÓN CLARA DE LOS DATOS:\n"
        
        if has_count_column:
            # Manejo especial para estadísticas
            data_summary += "\n*** ESTADÍSTICAS DE CICLISTAS ***\n"
            for i, row in enumerate(query_results, 1):
                ciclista = row.get('nombre_ciclista', 'No especificado')
                total_podios = row.get('total_podios', 0)
                total_victorias = row.get('total_victorias', 0)
                
                data_summary += f"\n{i}. {ciclista}:\n"
                if total_podios > 0:
                    data_summary += f"   - Total de podios: {total_podios}\n"
                if total_victorias > 0:
                    data_summary += f"   - Total de victorias: {total_victorias}\n"
                
                # Interpretación automática
                if i == 1:  # El primero en la lista
                    if total_podios > 0:
                        data_summary += f"   *** {ciclista} ES EL CICLISTA CON MÁS PODIOS ({total_podios}) ***\n"
                    if total_victorias > 0:
                        data_summary += f"   *** {ciclista} ES EL CICLISTA CON MÁS VICTORIAS ({total_victorias}) ***\n"
        else:
            # Manejo normal para resultados individuales
            for i, row in enumerate(query_results, 1):
                data_summary += f"\nRegistro {i}:\n"
                
                ciclista = row.get('nombre_ciclista', 'No especificado')
                año = row.get('año', 'No especificado')
                posicion = row.get('posicion', 'No especificada')
                carrera = row.get('nombre_carrera', 'No especificada')
                
                data_summary += f"  - Ciclista: {ciclista}\n"
                data_summary += f"  - Año: {año}\n"
                data_summary += f"  - Posición: {posicion}\n"
                data_summary += f"  - Carrera: {carrera}\n"
                
                # Interpretación automática de la posición
                if posicion == 1:
                    data_summary += f"  *** {ciclista} FUE EL GANADOR/CAMPEÓN en {año} ***\n"
                elif posicion == 2:
                    data_summary += f"  *** {ciclista} quedó SEGUNDO en {año} ***\n"
                elif posicion == 3:
                    data_summary += f"  *** {ciclista} quedó TERCERO en {año} ***\n"

        prompt = f"""Eres un experto en ciclismo colombiano. Responde basándote ÚNICAMENTE en estos datos interpretados.

{data_summary}

REGLAS SIMPLES:
1. Los datos ya están interpretados arriba
2. Si dice "ES EL CICLISTA CON MÁS PODIOS/VICTORIAS" entonces responde claramente quién es el líder
3. Si dice "FUE EL GANADOR/CAMPEÓN" entonces responde que ganó
4. Para estadísticas, menciona los números exactos mostrados arriba
5. SOLO menciona ciclistas, años, posiciones y estadísticas que aparecen arriba
6. Responde de forma natural y coloquial, como un experto comentarista

Pregunta: {user_question}

Respuesta natural:"""

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "Eres un experto comentarista de ciclismo colombiano. Respondes basándote únicamente en los datos proporcionados, sin inventar información."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=800
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Error generando respuesta: {e}")
            return "No pude generar una respuesta en este momento."
    
    def ask_question(self, user_question):
        """Procesar pregunta completa del usuario - Método principal para API"""
        print(f"\n🚴 Pregunta: {user_question}")
        
        # 1. Generar consulta SQL
        sql_query = self.generate_sql_query(user_question)
        if not sql_query:
            return {
                "success": False,
                "error": "No pude generar una consulta SQL válida para tu pregunta.",
                "data": None
            }
        
        print(f"📊 SQL generado: {sql_query}")
        
        # 2. Ejecutar consulta
        results, error = self.execute_query(sql_query)
        if error:
            return {
                "success": False,
                "error": f"Error en la consulta: {error}",
                "data": None
            }
        
        print(f"📈 Resultados encontrados: {len(results) if results else 0} registros")
        
        # 3. Generar respuesta final
        answer = self.generate_answer(user_question, results)
        
        return {
            "success": True,
            "error": None,
            "data": {
                "question": user_question,
                "answer": answer,
                "results_count": len(results) if results else 0,
                "sql_query": sql_query,  # Para debug si se necesita
                "raw_results": results[:10] if results else []  # Solo primeros 10 para evitar payload grande
            }
        }

    def test_connection(self):
        """Probar conexión a la base de datos"""
        conn = self.connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                conn.close()
                return {"success": True, "message": "Conexión exitosa"}
            except Exception as e:
                return {"success": False, "message": f"Error en prueba: {e}"}
        else:
            return {"success": False, "message": "No se pudo conectar a la base de datos"}

def main():
    """Función principal para pruebas locales"""
    print("🚴‍♂️ Sistema LLM de Ciclismo Colombiano (Versión Mejorada)")
    print("=" * 70)
    
    # Inicializar sistema
    cycling_llm = CyclingLLM()
    
    # Verificar conexión
    conn_test = cycling_llm.test_connection()
    if conn_test["success"]:
        print("✅ Conexión a base de datos exitosa")
    else:
        print(f"❌ {conn_test['message']}")
        return
    
    while True:
        print("\nOpciones:")
        print("1. Hacer una pregunta")
        print("2. Ver esquema de base de datos")
        print("3. Salir")
        
        choice = input("\nSelecciona una opción (1-3): ").strip()
        
        if choice == "1":
            question = input("\n¿Qué quieres saber sobre ciclismo colombiano?: ").strip()
            if question:
                result = cycling_llm.ask_question(question)
                print(f"\n🎯 Respuesta:")
                if result["success"]:
                    print(result["data"]["answer"])
                    print(f"\n📊 Registros encontrados: {result['data']['results_count']}")
                else:
                    print(f"❌ Error: {result['error']}")
                print("-" * 50)
        
        elif choice == "2":
            schema = cycling_llm.get_database_schema()
            print(f"\n📋 Esquema de la base de datos:")
            print(schema)
        
        elif choice == "3":
            print("¡Hasta luego! 🚴‍♂️")
            break
        
        else:
            print("Opción no válida. Intenta de nuevo.")

if __name__ == "__main__":
    main()