import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

from .api import (
    chart_routes,
    engine_routes,
    petrophysics_routes,
    production_routes,
    pvt_routes,
    simulation_routes,
    workflow_routes,
)


class HealthResponse(BaseModel):
    status: str
    version: str


from app.api.reservoir_routes import router as reservoir_router

app = FastAPI(title="PetroLumen API", version="0.1.0")

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(simulation_routes.router, prefix="/api")
app.include_router(engine_routes.router, prefix="/api")
app.include_router(production_routes.router, prefix="/api")
app.include_router(petrophysics_routes.router, prefix="/api")
app.include_router(pvt_routes.router, prefix="/api")
app.include_router(chart_routes.router, prefix="/api")
app.include_router(workflow_routes.router, prefix="/api")


@app.get("/health", response_model=HealthResponse)
async def health():
    return {"status": "ok", "version": app.version}


@app.exception_handler(Exception)
async def unhandled_exception(request, exc):
    logging.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url='/docs')


app.include_router(reservoir_router)

from app.api.reservoir_routes_ch5_9_13 import router as reservoir_2_router
app.include_router(reservoir_2_router)

from app.api.reservoir_routes_pvt import router as reservoir_pvt_router
app.include_router(reservoir_pvt_router)
