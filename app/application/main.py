from fastapi import FastAPI

app = FastAPI(title="Fintech Mini Bank API")

@app.get("/")
def read_root():
    return {"message": "API de Fintech Mini Bank funcionando correctamente"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}