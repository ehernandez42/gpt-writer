from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.generate import generate_text, get_generation, list_generations, update_generation

router = APIRouter(tags=["generate"])


class GenerateRequest(BaseModel):
    style_id: str
    prompt: str


class UpdateGenerationRequest(BaseModel):
    generated_text: str


@router.post("/generate")
async def generate_endpoint(payload: GenerateRequest):
    try:
        return await generate_text(payload.style_id, payload.prompt)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/generations")
def list_generations_endpoint():
    return list_generations()


@router.get("/generations/{generation_id}")
def get_generation_endpoint(generation_id: str):
    generation = get_generation(generation_id)
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")
    return generation


@router.patch("/generations/{generation_id}")
def update_generation_endpoint(generation_id: str, payload: UpdateGenerationRequest):
    generation = update_generation(generation_id, payload.generated_text)
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")
    return generation
