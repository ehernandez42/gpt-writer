from io import BytesIO

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.embeddings import test_sqlite_vec
from services.export import export_document

router = APIRouter(tags=["export"])


class ExportRequest(BaseModel):
    content: str
    format: str
    content_type: str


@router.post("/export")
def export_endpoint(payload: ExportRequest):
    try:
        file_data = export_document(payload.content, payload.format, payload.content_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return StreamingResponse(
        BytesIO(file_data["content"]),
        media_type=file_data["content_type"],
        headers={"Content-Disposition": f"attachment; filename={file_data['filename']}"},
    )


@router.get("/test")
def test():
    return test_sqlite_vec()