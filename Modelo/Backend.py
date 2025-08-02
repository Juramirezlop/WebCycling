from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from CyclingLLM import CyclingLLM
import uvicorn
from typing import Optional, Dict, Any
import os

# Modelos de datos
class QuestionRequest(BaseModel):
    question: str

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Dict[Any, Any]] = None
    error: Optional[str] = None

# Crear instancia de FastAPI
app = FastAPI(
    title="Cycling LLM API",
    description="Consultas de ciclismo colombiano",
    version="1.0.0"
)

# Configurar CORS para permitir requests del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancia global de CyclingLLM
cycling_llm = None

@app.on_event("startup")
async def startup_event():
    """Inicializar CyclingLLM al arrancar la aplicación"""
    global cycling_llm
    try:
        cycling_llm = CyclingLLM()
        print("✅ CyclingLLM inicializado correctamente")
    except Exception as e:
        print(f"❌ Error inicializando CyclingLLM: {e}")

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Cycling LLM API está funcionando",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "ask": "/ask (POST)",
            "test-connection": "/test-connection"
        }
    }

@app.get("/health")
async def health_check():
    """Verificar estado de la aplicación"""
    global cycling_llm
    
    if cycling_llm is None:
        return ApiResponse(
            success=False,
            error="CyclingLLM no está inicializado"
        )
    
    # Probar conexión a la base de datos
    connection_test = cycling_llm.test_connection()
    
    return ApiResponse(
        success=connection_test["success"],
        data={
            "status": "healthy" if connection_test["success"] else "unhealthy",
            "database": connection_test["message"]
        },
        error=None if connection_test["success"] else connection_test["message"]
    )

@app.get("/test-connection")
async def test_db_connection():
    """Probar conexión específicamente a la base de datos"""
    global cycling_llm
    
    if cycling_llm is None:
        raise HTTPException(
            status_code=500, 
            detail="CyclingLLM no está inicializado"
        )
    
    try:
        result = cycling_llm.test_connection()
        
        return ApiResponse(
            success=result["success"],
            data={
                "message": result["message"],
                "timestamp": None
            },
            error=None if result["success"] else result["message"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error probando conexión: {str(e)}"
        )

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """Procesar pregunta sobre ciclismo colombiano"""
    global cycling_llm
    
    if cycling_llm is None:
        raise HTTPException(
            status_code=500,
            detail="CyclingLLM no está inicializado"
        )
    
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="La pregunta no puede estar vacía"
        )
    
    try:
        # Procesar la pregunta
        result = cycling_llm.ask_question(request.question.strip())
        
        if result["success"]:
            return ApiResponse(
                success=True,
                data=result["data"],
                error=None
            )
        else:
            return ApiResponse(
                success=False,
                data=None,
                error=result["error"]
            )
    
    except Exception as e:
        print(f"Error procesando pregunta: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )

@app.get("/schema")
async def get_database_schema():
    """Obtener esquema de la base de datos (endpoint opcional para debug)"""
    global cycling_llm
    
    if cycling_llm is None:
        raise HTTPException(
            status_code=500,
            detail="CyclingLLM no está inicializado"
        )
    
    try:
        schema = cycling_llm.get_database_schema()
        
        return ApiResponse(
            success=True,
            data={
                "schema": schema
            },
            error=None
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo esquema: {str(e)}"
        )

# Endpoint adicional para redirigir al frontend
@app.get("/app")
async def redirect_to_frontend():
    """Redirigir al frontend (si está en el mismo servidor)"""
    return {
        "message": "Para usar la interfaz web, ve a /frontend o ejecuta el frontend por separado",
        "frontend_url": "http://localhost:3000",  # URL típica de React
        "api_docs": "/docs"
    }

if __name__ == "__main__":
    # Configuración para desarrollo
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🚀 Iniciando servidor en http://{host}:{port}")
    print(f"📚 Documentación API: http://{host}:{port}/docs")
    print(f"🔗 JSON Schema: http://{host}:{port}/redoc")
    
    uvicorn.run(
        "Backend:app",  # Asume que este archivo se llama main.py
        host=host,
        port=port,
        reload=True,  # Solo para desarrollo
        log_level="info"
    )

# Para producción, usar:
# uvicorn main:app --host 0.0.0.0 --port 8000