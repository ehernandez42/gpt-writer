from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from starlette.status import HTTP_204_NO_CONTENT

from services.styles import create_style, delete_style, get_style, list_styles

router = APIRouter(prefix="/styles", tags=["styles"])


@router.post("", status_code=201)
def create_style_endpoint(name: str = Form(...), files: list[UploadFile] = File(...)):
    return create_style(name, files)


@router.get("")
def list_styles_endpoint():
    return list_styles()


@router.get("/{style_id}")
def get_style_endpoint(style_id: str):
    style = get_style(style_id)
    if not style:
        raise HTTPException(status_code=404, detail="Style not found")
    return style


@router.delete("/{style_id}", status_code=HTTP_204_NO_CONTENT)
def delete_style_endpoint(style_id: str):
    delete_style(style_id)
