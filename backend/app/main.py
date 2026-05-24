from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import application_types, document_templates, samples, suggest

app = FastAPI(title="IDP — Admin API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(application_types.router)
app.include_router(document_templates.router)
app.include_router(samples.router)
app.include_router(suggest.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
