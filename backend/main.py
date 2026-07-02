import os
from pathlib import Path
from contextlib import asynccontextmanager 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.db import DBManager
from routers.styles import router as styles_router
from routers.generate import router as generate_router
from routers.export import router as export_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = DBManager()
    schema_path = Path(__file__).parent / "database" / "init.sql"
    db.init_db(schema_path)
    db.init_vector_tables() 
    yield


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_env_file(Path(__file__).with_name(".env"))

app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(styles_router)
app.include_router(generate_router)
app.include_router(export_router)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
