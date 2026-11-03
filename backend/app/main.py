import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

from .api import engine_routes, simulation_routes

app = FastAPI(title="PetroLumen API", version="0.1.0")
app.include_router(simulation_routes.router, prefix="/api")
app.include_router(engine_routes.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "version": app.version}


@app.exception_handler(Exception)
async def unhandled_exception(request, exc):
    logging.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get('/', include_in_schema=False)
async def root():
    return RedirectResponse(url='/docs')
