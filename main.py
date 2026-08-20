import os

from fastapi import FastAPI, HTTPException, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI(
    title="API de Estudiantes",
    description="API RESTful de demostración para el seminario de "
                "IA en Ingeniería de Software.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Protección de endpoints destructivos ----------
# DELETE y /admin/reset requieren esta clave (header X-Admin-Key).
# GET, POST y PATCH quedan abiertos para que el curso participe sin fricción.
ADMIN_KEY = os.environ.get("ADMIN_KEY", "seminario2026")
api_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)

def verificar_admin(clave: str = Depends(api_key_header)):
    if clave != ADMIN_KEY:
        raise HTTPException(
            status_code=403,
            detail="Requiere clave de administrador (botón Authorize arriba a la derecha).",
        )
    return True

# ---------- Modelos ----------

class Estudiante(BaseModel):
    id: int
    nombre: str
    carrera: str

class EstudianteCreate(BaseModel):
    nombre: str = Field(..., min_length=1, examples=["Eduardo"])
    carrera: str = Field(..., min_length=1,
                         examples=["Ingeniería Civil Informática"])

class EstudiantePatch(BaseModel):
    nombre: Optional[str] = None
    carrera: Optional[str] = None

class Error(BaseModel):
    detail: str

# ---------- Estado en memoria ----------

DATOS_INICIALES = [
    {"id": 1, "nombre": "Juan",  "carrera": "Ingeniería"},
    {"id": 2, "nombre": "Sofía", "carrera": "Informática"},
]

estudiantes: List[dict] = [dict(e) for e in DATOS_INICIALES]
siguiente_id = 3

def buscar(id: int) -> dict:
    for e in estudiantes:
        if e["id"] == id:
            return e
    raise HTTPException(status_code=404, detail="Estudiante no encontrado")

# ---------- Endpoints ----------

@app.get("/estudiantes", response_model=List[Estudiante],
         summary="Obtener todos los estudiantes", tags=["Estudiantes"])
def listar_estudiantes():
    return estudiantes

@app.get("/estudiantes/{id}", response_model=Estudiante,
         summary="Obtener un estudiante por id", tags=["Estudiantes"],
         responses={404: {"model": Error, "description": "No existe"}})
def obtener_estudiante(id: int):
    return buscar(id)

@app.post("/estudiantes", response_model=Estudiante, status_code=201,
          summary="Crear un estudiante", tags=["Estudiantes"])
def crear_estudiante(datos: EstudianteCreate):
    global siguiente_id
    nuevo = {"id": siguiente_id, **datos.model_dump()}
    estudiantes.append(nuevo)
    siguiente_id += 1
    return nuevo

@app.patch("/estudiantes/{id}", response_model=Estudiante,
           summary="Modificar parcialmente un estudiante",
           tags=["Estudiantes"],
           responses={404: {"model": Error, "description": "No existe"}})
def modificar_estudiante(id: int, cambios: EstudiantePatch):
    estudiante = buscar(id)
    estudiante.update(cambios.model_dump(exclude_unset=True))
    return estudiante

@app.delete("/estudiantes/{id}", status_code=204,
            summary="Eliminar un estudiante", tags=["Estudiantes"],
            responses={404: {"model": Error, "description": "No existe"}},
            dependencies=[Depends(verificar_admin)])
def eliminar_estudiante(id: int):
    estudiante = buscar(id)
    estudiantes.remove(estudiante)
    return Response(status_code=204)

# ---------- Utilidad para la demo ----------

@app.post("/admin/reset", status_code=204,
          summary="Restaurar los datos iniciales",
          tags=["Demo"],
          dependencies=[Depends(verificar_admin)])
def reset():
    global estudiantes, siguiente_id
    estudiantes = [dict(e) for e in DATOS_INICIALES]
    siguiente_id = 3
    return Response(status_code=204)
