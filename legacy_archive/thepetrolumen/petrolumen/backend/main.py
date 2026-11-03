from fastapi import FastAPI

app = FastAPI(title="Petrolumen API")


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"version": "0.1.0"}
