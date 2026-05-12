from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    user_id: str = Field(..., example="elias_123")
    course_id: str = Field(..., example="analisis_matematico_1")
    role: str = Field(default="estudiante")
    pregunta: str = Field(..., min_length=5)
    confidence: int = Field(..., ge=1, le=3, description="Nivel de detalle: 1-Paso a paso, 2-Estratégico, 3-Sintético")

class ChatResponse(BaseModel):
    tema: str
    respuesta: str
    status: Optional[str] = "success"