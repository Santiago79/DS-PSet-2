from fastapi import FastAPI

from app.api.routes import router
from app.infra.database import init_db

app = FastAPI(
    title="Fintech Mini Bank API",
    description="API para clientes, cuentas y transacciones (deposit, withdraw, transfer).",
    version="1.0.0",
)

@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def read_root():
    return {"message": "API de Fintech Mini Bank funcionando correctamente"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


app.include_router(router)